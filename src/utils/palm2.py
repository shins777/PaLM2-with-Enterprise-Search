
import vertexai
from vertexai.preview.language_models import TextGenerationModel
from vertexai.preview.language_models import ChatModel

from google.cloud import logging

import google
from google.oauth2 import service_account
import google.auth.transport.requests
import requests

import utils.variables as env

class SingletonInstane:
    __instance = None

    @classmethod
    def __getInstance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls.__getInstance
        return cls.__instance

class Palm2_Util(SingletonInstane):

    credentials = None
    llm = None
    chat_model = None

    logger = None
    TERMINAL_LOGGING = False
    LOGGING = True
    
    def __init__(self):

        """ Initialize VertexAI instance in a way of langchain library. """
        print("Create instance of Palm2_Util")

    def model_initialize(self, project_id, region, text_model_name,chat_model_name ):
        
        """ Initialize LLM model """
        Palm2_Util.credentials = service_account.Credentials.from_service_account_file(
            env.SVC_ACCT_FILE, 
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Initialize Palm2.
        vertexai.init(project=project_id, location=region, credentials =Palm2_Util.credentials)

        # TextGenerationModel
        if text_model_name =='google/text-bison@latest' or text_model_name =='google/text-bison@001':
            Palm2_Util.llm = TextGenerationModel.from_pretrained(text_model_name)

        # ChatModel.
        Palm2_Util.chat_model = ChatModel.from_pretrained(chat_model_name)

        logging_client = logging.Client(credentials=Palm2_Util.credentials)
        Palm2_Util.logger = logging_client.logger('GenAI')

    def build_query(self, user_input, context, prompt, step ):
        
        """Prompt building  """
        
        # Build a query message for prompt engineering.
        if step == "REASONING":  
            query_with_context = f"{prompt}\n Context : ``` {context} ``` \n\n Question : {user_input} \n REASONING : "
        elif step == "SUMMARIZATION":
            query_with_context = f"{prompt}\n Context : ``` {context} ``` \n\n Question : {user_input} \n\n SUMMARY : "
        elif step =="PUBLIC_SEARCH":
            query_with_context = f"{prompt}\n\n Question : {user_input} \n\n SUMMARY : "

        else: 
            query_with_context = f"{prompt}\n ``` {context} ``` "

        if self.LOGGING:
            self.log("INFO",f"Final Prompt : {query_with_context}")

        return query_with_context

    def generate_response(self, prompt, temperature, output_token, top_k, top_p):
        """Retrieve information from LLM(English) """

        response = Palm2_Util.llm.predict(
                        prompt=prompt,
                        max_output_tokens=output_token,
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k)

        if self.LOGGING:
            self.log("INFO", f"Response from PaLM2:\n {response.text}")
            self.log("INFO","\n\n-------------------------[ Query End ]---------------------------\n\n")

        return response.text

    def log(self, severity, log_str):

        self.logger.log_text(log_str,severity=severity )

        if self.TERMINAL_LOGGING:
            print(f"[{severity}] : {log_str}")

