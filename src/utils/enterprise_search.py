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
            env.ES_SVC_ACCT_FILE, 
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
                "snippetSpec": {"maxSnippetCount": 5},
                # "summarySpec": { "summaryResultCount": 5},
                "extractiveContentSpec":{
                    # "maxExtractiveAnswerCount": 5,
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
        
        outcome =""
        snippets_ctx =""
        segments_ctx =""

        outcome_with_reference=""
        summary= ""

        if dict_results.get('summary'):
            summary = "\t" + dict_results['summary']['summaryText']

        if dict_results.get('results'):

            for result in dict_results['results']:

                reference = result['document']['derivedStructData']['link'] +".\n"
                #print("\n\n--< reference >------")
                #print(reference)

                #print("\n\n--< snippets >------")
                for snippet in result['document']['derivedStructData']['snippets']:
                    context = snippet['snippet'] +"\n"
                    #print(context)
                    snippets_ctx = snippets_ctx + context
                    
                #print("\n---<segments>-----")
                for segment in result['document']['derivedStructData']['extractive_segments']:
                    content = segment['content'] +"\n"
                    #print(content)
                    segments_ctx = segments_ctx + content

                # print("\n---< answers >-----")
                # for answer in result['document']['derivedStructData']['extractive_answers']:
                #     content = "\t" + answer['content'] +"\n"
                #     print(content)

                outcome_with_reference  = outcome_with_reference + (reference +"\n\n" + snippets_ctx +"\n\n"+ segments_ctx) +"\n\n"
                outcome =  outcome + ( snippets_ctx +"\n\n"+ segments_ctx) +"\n\n"

        if Palm2_Util.instance().LOGGING:
            Palm2_Util.instance().log("INFO",f"Context from Enterprise Search : \n{outcome_with_reference} \n")

        snippets_ctx = snippets_ctx.replace("<b>","").replace("</b>","").replace("&quot;","")
        segments_ctx = segments_ctx.replace("<b>","").replace("</b>","").replace("&quot;","")

        outcome = outcome.replace("<b>","").replace("</b>","").replace("&quot;","")
        outcome_with_reference = outcome_with_reference.replace("<b>","").replace("</b>","").replace("&quot;","")

        return outcome, outcome_with_reference, snippets_ctx, segments_ctx
