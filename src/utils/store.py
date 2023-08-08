
class ChainsStore():
 
    context = ""
    context_with_reference = ""
    
    es_search_result =""
    vectordb_search_result =""

    public_search_result = ""
    
    reasoning_prompt = ""
    summary_prompt = ""
    final_prompt = ""
    final_context = ""

    reasoning_outcomes = ""
    summary_outcomes = ""
    final_outcomes = ""

    latency = ""

    chat = None

    def __init__(self):
        print("Create instance of ChainsStore")

class ParameterStore():
 
    text_model = ""
    chat_model = ""
    
    n_threads = ""

    temperature = ""
    output_token = ""
    top_k = ""
    top_p = ""

    reasoning_prompt_env = ""
    es_url = ""
    num_es = ""

    def __init__(self):
        print("Create instance of ParameterStore")