# import sys
# import os
#
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#
# from utils.conversation_simulator import create_conversation, TEXT, CONVERSATION
# from actions.prediction.predict import predict_operation
#
# conversation = CONVERSATION
# dataset_name = conversation.describe.get_dataset_name()
#
#
# def test_prediction_with_id():
#     """Test prediction functionality"""
#     parse_text = ["filter", "id", "215", "and", "predict", "[E]"]
#
#     return_s, status_code = predict_operation(conversation, parse_text, 1)
#
#     file_html = open(f"./tests/html/prediction/{dataset_name}_prediction_with_id.html", "w")
#     text = TEXT
#     text += return_s
#     text += "</body></html>"
#     file_html.write(text)
#
#     # Saving the data into the HTML file
#     file_html.close()
#     assert status_code == 1
#
#
# def test_prediction_all():
#     """Test prediction functionality"""
#     parse_text = ["predict", "all", "[E]"]
#
#     return_s, status_code = predict_operation(conversation, parse_text, 1)
#
#     file_html = open(f"./tests/html/prediction/{dataset_name}_prediction_all.html", "w")
#     text = TEXT
#     text += return_s
#     text += "</body></html>"
#     file_html.write(text)
#
#     # Saving the data into the HTML file
#     file_html.close()
#     assert status_code == 1
#
#
# # TODO: test for custom input