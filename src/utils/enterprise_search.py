import json
from google.oauth2 import service_account
import google.auth.transport.requests
import requests

from utils.palm2 import Palm2_Util
import utils.variables as env

class EnterpriseSearch():

    credentials = None

    def __init__(self):

        """ Credential initialization with Service account"""

        EnterpriseSearch.credentials = service_account.Credentials.from_service_account_file(
            env.SVC_ACCT_FILE, 
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        request = google.auth.transport.requests.Request()

        # Refresh request with credentials.
        EnterpriseSearch.credentials.refresh(request)

    def retrieve_discovery_engine(self, endpoint, num_es, query ):

        """ retrieve information from enterprise search ( discovery engine )"""
        # Create a credentials token to call a REST API
        headers = { 
            "Authorization": "Bearer "+ EnterpriseSearch.credentials.token,
            "Content-Type": "application/json"
        }

        query_dic ={ 
            "query": query, 
            "page_size": str(num_es), 
            "offset": 0,
            "contentSearchSpec":{
                "snippetSpec": {"maxSnippetCount": 5,
                                },
                # "summarySpec": { "summaryResultCount": 5,
                #                  "includeCitations": True},
                "extractiveContentSpec":{
                    "maxExtractiveAnswerCount": 5,
                    "maxExtractiveSegmentCount": 1}
            },
            # "queryExpansionSpec":{"condition":"AUTO"}
        } 

        data = json.dumps(query_dic)

        # Encode data as UTF8
        data=data.encode("utf8")

        response = requests.post(endpoint,headers=headers, data=data)

        if Palm2_Util.instance().LOGGING:
            Palm2_Util.instance().log("INFO","---------------------[ Query Start ]-------------------------")
            Palm2_Util.instance().log("INFO","f\n\n User's input : \n{query} \n")

        return response.text

    def parse_discovery_results(self, response_text):

        """Parse response to build a conext to be sent to LLM"""

        dict_results = json.loads(response_text)
        
        #print(dict_results)

        outcome = ""
        outcome_ref =""

        outcome_list =[]
        outcome_ref_list=[]

        #summary= ""
        # if dict_results.get('summary'):
        #     summary = "\t" + dict_results['summary']['summaryText']

        idx = 1
        if dict_results.get('results'):

            for result in dict_results['results']:

                snippets_ctx =""
                answer_ctx =""
                segments_ctx =""
                
                reference = result['document']['derivedStructData']['link']
                
                #print("\n\n--< reference >------")
                #print(reference)

                #print("\n\n--< snippets >------")
                for snippet in result['document']['derivedStructData']['snippets']:
                    context = snippet['snippet']
                    snippets_ctx = snippets_ctx + context
                
                #print(snippets_ctx)

                #print("\n---< answers >-----")
                for answer in result['document']['derivedStructData']['extractive_answers']:
                    content = answer['content']
                    answer_ctx = answer_ctx + content

                #print(answer_ctx)

                #print("\n---<segments>-----")
                for segment in result['document']['derivedStructData']['extractive_segments']:
                    content = segment['content']
                    segments_ctx = segments_ctx + content

                #print(segments_ctx)

                each_outcome_ref = f"\n\n-------------------------- \n\nContext {idx} : \n\nReference : {reference} \n\n {snippets_ctx} \n\n {answer_ctx} \n\n {segments_ctx}"
                each_outcome = f"\n\n +{snippets_ctx} \n\n {answer_ctx} \n\n {segments_ctx}"

                outcome_ref_list.append(each_outcome_ref)
                outcome_list.append(each_outcome)

                idx = idx + 1

        if Palm2_Util.instance().LOGGING:
            Palm2_Util.instance().log("INFO",f"Context from Enterprise Search : \n{outcome_ref} \n")
        outcome_ref = "\n\n".join(outcome_ref_list)
        outcome = "\n\n".join(outcome_list)

        # print(outcome_ref)

        outcome_ref = outcome_ref.replace("<b>","").replace("</b>","").replace("&quot;","")
        outcome = outcome.replace("<b>","").replace("</b>","").replace("&quot;","")

        return outcome, outcome_ref
