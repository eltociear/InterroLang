import json
import os

import torch
from explained_models.Explainer.explainer import Explainer

from explained_models.Tokenizer.tokenizer import HFTokenizer
from explained_models.ModelABC.DANetwork import DANetwork

# https://huggingface.co/uw-hai/polyjuice
from polyjuice import Polyjuice
from polyjuice.generations.special_tokens import *
from da_model_utils import DADataset

ALL_CTRL_CODES = set([
   LEXCICAL, RESEMANTIC, NEGATION, INSERT,
   DELETE, QUANTIFIER, RESTRUCTURE, SHUFFLE
])

model_id2label = {0:'dummy', 1:'inform', 2:'question', 3:'directive', 4:'commissive'}


class CFEExplainer(Explainer):
    def __init__(self, explainer="polyjuice", tokenizer="bert"):
        super(CFEExplainer, self).__init__()
        self.device = None
        self.is_cuda = None
        self.check_cuda()

        self.model = DANetwork()
        self.explainer = Polyjuice(model_path="uw-hai/polyjuice", is_cuda=self.is_cuda) if explainer == 'polyjuice' else explainer
        self.tokenizer = HFTokenizer('bert-base-uncased', mode='bert').tokenizer if tokenizer == 'bert' else tokenizer

    def encode_sample(self, sample):
        encoded = self.tokenizer.encode_plus(sample, return_tensors='pt').to(self.device)
        return encoded

    def get_samples_from_pj(self, instance, ctrl_code):
        try:
            generated_samples = self.explainer.perturb(instance, ctrl_code=ctrl_code, num_perturbations=None,
                                           perplex_thred=10)  # , num_beams=5)
        except:
            generated_samples = self.explainer.perturb(instance, ctrl_code=ALL_CTRL_CODES, num_perturbations=None,
                                           perplex_thred=None)
        return generated_samples

    # instance: input string
    # number: max number of samples to generate
    # ctrl_code: ['resemantic', 'restructure', 'negation', 'insert', 'lexical', 'shuffle', 'quantifier', 'delete'] by default uses all codes
    # returns two lists with the generated samples that result in the same or different label
    # each list consists of tuples (generated_text, class)
    # e.g.:
    # same label: [('i also have blow if you prefer to do a few shots.', 'directive'), ('i also have blow if you prefer to do this.', 'directive')]
    # diff label: [('also blew me away with his single second.', 'inform')]
    def cfe(self, instance, number, ctrl_code=ALL_CTRL_CODES, id2label=None):
        new_samples = self.get_samples_from_pj(instance, ctrl_code)
        encoded_instance = self.encode_sample(instance)
        orig_prediction = self.model(encoded_instance['input_ids'], encoded_instance['attention_mask'])
        orig_prediction = torch.argmax(orig_prediction).item()
        if id2label is not None:
            orig_prediction = id2label[orig_prediction]
        same_label_samples = []
        diff_label_samples = []
        for new_sample in new_samples:
            encoded_new_sample = self.encode_sample(new_sample)
            prediction = self.model(encoded_new_sample['input_ids'], encoded_new_sample['attention_mask'])
            prediction = torch.argmax(prediction).item()
            if id2label is not None:
                prediction = id2label[prediction]
            if prediction != orig_prediction:
                diff_label_samples.append((new_sample, prediction))
            else:
                same_label_samples.append((new_sample, prediction))
        return same_label_samples[:number], diff_label_samples[:number]
    def check_cuda(self):
        if torch.cuda.is_available():
            self.is_cuda = True
            self.device = 'cuda'
        else:
            self.is_cuda = False
            self.device = 'cpu'

    def generate_explanation(self, store_data=False, data_path="../../cache/dailydialog/cfe_daily_dialog_explanation.json"):
        if os.path.exists(data_path):
            fileObject = open(data_path, "r")
            jsonContent = fileObject.read()
            result_list = json.loads(jsonContent)
            print(result_list)

        else:
            json_list = []

            ### testing with some random text ###
            instance_text = 'Why is this important?'
            same, diff = self.cfe(instance_text, number=4, ctrl_code='lexical')
            print('original text:', instance_text)
            print('same label predictions:', same)
            print('different label predictions:', diff)

            ### testing with the DA test dataloader ###
            test_dataloader = torch.load('../../explained_models/da_classifier/test_dataloader.pth')
            for b_input in test_dataloader:
                input_ids = b_input[0].to(self.device)
                instance_text = self.tokenizer.convert_tokens_to_string(self.tokenizer.convert_ids_to_tokens(input_ids[0], skip_special_tokens=True))
                same, diff = self.cfe(instance_text, number=4, id2label=model_id2label)
                print('original text:', instance_text)
                print('same label predictions:', same)
                print('different label predictions:', diff)
                input_mask = b_input[1].to(self.device)
                labels = b_input[2].to(self.device)

                with torch.no_grad():
                    result = self.model(input_ids, input_mask)
                    predicted_label_id = torch.argmax(result.detach().cpu()).item() # result.logits...
                    true_label_id = labels.to('cpu').numpy()[0]
                    print('predicted label:', model_id2label[predicted_label_id])
                    print('true label:', model_id2label[true_label_id])
                print()

                json_list.append({
                    "instance_text": instance_text,
                    "same_label_predictions": same,
                    "different_label_predictions": diff,
                    "predicted_label": model_id2label[predicted_label_id],
                    "true_label": model_id2label[true_label_id]
                })

            jsonString = json.dumps(json_list)
            jsonFile = open(data_path, "w")
            jsonFile.write(jsonString)
            jsonFile.close()


if __name__ == "__main__":
    CFEExplainer().generate_explanation()


