import os
import json
import vertexai
from vertexai.preview.language_models import TextGenerationModel
from google.cloud import logging

import google
from google.oauth2 import service_account
import google.auth.transport.requests
import requests
from dotenv import load_dotenv
from langchain.llms import VertexAI

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

    logger = None
    TERMINAL_LOGGING = False
    LOGGING = True
    
    def __init__(self):

        """ Initialize VertexAI instance in a way of langchain library. """


        print("Create instance of Palm2_Util")

        Palm2_Util.credentials = service_account.Credentials.from_service_account_file(
            env.SVC_ACCT_FILE, 
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        Palm2_Util.llm = self._model_initialize(env.PROJECT_ID, env.REGION, env.MODEL, Palm2_Util.credentials ) 

        # For Centralized Logging
        Palm2_Util.credentials_log = service_account.Credentials.from_service_account_file(
            env.LOG_SVC_ACCT_FILE, 
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        logging_client = logging.Client(credentials=Palm2_Util.credentials_log)
        Palm2_Util.logger = logging_client.logger('GenAI')

#    def init_vertexai(self):




    def _model_initialize(self, project_id, region, model_name, credentials ):
        
        """ Initialize LLM model """

        # Initialize Palm2.
        vertexai.init(project=project_id, location=region, credentials =credentials)
        model = TextGenerationModel.from_pretrained(model_name)
        
        return model

    def build_query(self, user_input,context, default_prompt ):
        
        """Prompt building  """
        
        # Build a query message for prompt engineering.
        query_with_context = f""" {default_prompt}
        Question: {user_input}
        Context: {context}
        AI chatbot :
        """
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
