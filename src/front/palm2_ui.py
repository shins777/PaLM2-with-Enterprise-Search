
import time
import streamlit as st

import os
import sys

directory = os.getcwd()
# Append sys path to refer utils.
sys.path.append(directory+"/src")

import utils.variables as env
from utils.palm2 import Palm2_Util
from utils.store import ChainsStore
from utils.store import ParameterStore

#from utils.enterprise_search import EnterpriseSearch
from utils.reasoning import Reasoning
from utils.search import RAG

palm2_util = Palm2_Util.instance()
#es = EnterpriseSearch()

# Set Streamlit page configuration
st.set_page_config(page_title='Palm2 API Tester', layout='wide')

# Initialize session states
if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "input" not in st.session_state:
    st.session_state["input"] = ""

# Initialize session states
if "generated2" not in st.session_state:
    st.session_state["generated2"] = []
if "past2" not in st.session_state:
    st.session_state["past2"] = []
if "input2" not in st.session_state:
    st.session_state["input2"] = ""

# Define function to get user input
def get_text():

    input_text = st.text_area("You: ", st.session_state["input"], key="input",
                            placeholder="Your AI assistant here! Ask me anything ...", 
                            label_visibility='hidden')
    if es_url=="":
        st.warning('Put your Enterprise Search Endpoint(Unstructured) in "Configuration > Enterprise Search" to get the context ', icon="⚠️")
    return input_text

def get_text2():

    input_text2 = st.text_area("You: ", st.session_state["input2"], key="input2",
                            placeholder="Your AI assistant here! Ask me anything ...", 
                            label_visibility='hidden')
    if es_url=="":
        st.warning('Put your Enterprise Search Endpoint in "Configuration > Enterprise Search" to get the context ', icon="⚠️")
    return input_text2


default_prompt = None
es_url = None

# Set up sidebar with various options
with st.sidebar.expander("Configuration", expanded=True):
    
    side_tab1, side_tab2 = st.tabs(["LLM Model", "Enterprise Search"])

    with side_tab1:
        ParameterStore.text_model = st.selectbox(label='Text Model', options=env.TEXT_MODEL)
        ParameterStore.chat_model = st.selectbox(label='Chat Model', options=env.CHAT_MODEL)

        #n_threads = st.number_input(' Number of Answer ',min_value=1,max_value=5, value=3)
        
        st.markdown("""---""")
        ParameterStore.temperature = st.number_input(' Temperature ',min_value=0.0,max_value=1.0,step=0.1, format="%.1f",value= env.TEMPERATURE)
        ParameterStore.output_token = st.number_input(' Output Token ',min_value=100,max_value=1024,value=env.MAX_OUTPUT_TOKENS )
        ParameterStore.top_k = st.number_input(' Top K ',min_value=1,max_value=40, value=env.TOP_K)
        ParameterStore.top_p = st.number_input(' Top P ',min_value=0.0,max_value=1.0,step=0.1, format="%.1f",value= env.TOP_P)

    with side_tab2 : 
        ParameterStore.reasoning_prompt_env = st.text_area("Add default prompt, this will be added automatically in front of your request", value= env.reasoning_prompt)
        ParameterStore.es_url = st.text_area("Put your Enterprise engine url to search context",value=env.end_point)
        ParameterStore.num_es = st.number_input(' (#) of Enterprise search results',min_value=1,max_value=5, value=3)

palm2_util.model_initialize(env.PROJECT_ID,env.REGION, ParameterStore.text_model, ParameterStore.chat_model)

# Set up the Streamlit app layout
st.title("Palm2 + ES Tester")
st.subheader("An emulator to interact with Google Palm2 and Enterprise Search")

context = None
context_with_reference = None

chat = None

tab1, tab2, tab3, tab4 = st.tabs(["Ask PaLM2 + ES", "PaLM2 response with reasoning", "Process of summarizations and reasonings", "Results of Enterprise Search"])

with tab1 : 
    # Get the user input
    user_input = get_text()
    
    #search = st.checkbox('Search')
    mode = st.radio(" ", ('Search', 'Chat'), horizontal=True )
    

    if st.button("Ask Palm2 + ES"):

        if mode == "Search":

            print("Search mode")

            t1 = time.time()

            rag_search = RAG()
            rag_search.rag_search(user_input)

            t2 = time.time()
            reasoning = Reasoning()
            reasoning.consolidate(user_input)

            t3 = time.time()
            reasoning.final_request(user_input)
            
            t4 = time.time()
            palm2_util.log("INFO",f"\n\n-------------------[ Execution Time ]-----------------------")
            palm2_util.log("INFO",f'Execution time: RAG Search : {t2-t1} seconds')
            palm2_util.log("INFO",f'Execution time: Reasoning :  {t3-t2} seconds')
            palm2_util.log("INFO",f'Execution time: Final Request :  {t4-t3} seconds')
            palm2_util.log("INFO",f"---------------------[ Total : {t4-t1} seconds ]------------------------")

            ChainsStore.latency = f"Total Elapsed time : [{t2-t1}], Reasoning : [{t3-t2}], Final Request : [{t4-t3}], Total elapsed time :[{t4-t1}] "

            st.session_state.past.append(user_input) 
            st.session_state.generated.append(ChainsStore.final_outcomes) 

        elif mode == "Chat":

            print("Chat mode")        

            ChainsStore.chat = palm2_util.chat_model.start_chat(context=ChainsStore.context)
            
            parameters = {
                "temperature": ParameterStore.temperature,
                "max_output_tokens": ParameterStore.output_token,
                "top_p": ParameterStore.top_p,
                "top_k": ParameterStore.top_k
            }

            response = ChainsStore.chat.send_message(user_input, **parameters)
            print(f"Response from Model: {response.text}")

            st.session_state.past.append(user_input) 
            st.session_state.generated.append(response.text) 
            
            ChainsStore.prompt = user_input
            ChainsStore.final_outcomes = response.text
        
        if palm2_util.LOGGING:
            palm2_util.log("INFO", f"Response from PaLM2 :\n {ChainsStore.final_outcomes}")
            palm2_util.log("INFO","\n\n-------------------------[ Query End ]---------------------------\n\n")

    # Display the conversation history
    with st.expander("Conversation", expanded=True):
        for i in range(len(st.session_state["past"])-1, -1, -1):
            st.info(st.session_state["past"][i],icon="😊")
            st.success(st.session_state["generated"][i], icon="🤖")


with tab2:
    st.subheader("PaLM2 response with reasoning")

    #with st.expander("Resonse from PaLM2"):
    st.write(env.final_prompt + "\n\n" + ChainsStore.final_context + "\n\n\n\nFinal Results : \n\n" + ChainsStore.final_outcomes)

with tab3:
    st.subheader("Process of summarizations and reasonings")

    with st.expander("Context summary of Enteprise search results"):
        st.write(ChainsStore.summary_outcomes)

    with st.expander("Step by step reasoning for Enteprise search results "):
        st.write(ChainsStore.reasoning_outcomes)

    # with st.expander("Public Search Results"):
    #     st.write(ChainsStore.public_search_result)

    with st.expander("Latency "):
        st.write(ChainsStore.latency)

with tab4:
    st.subheader("Results of Enterprise Search")

    #with st.expander("Results of Enterprise Search with context references"):
    st.write(ChainsStore.context_with_reference)


# with tab5:
#     # Get the user input
#     user_input2 = get_text2()

#     if st.button("Ask Palm2"):    
#         outcomes2 = palm2_util.concurrent_call(user_input2,ParameterStore.temperature, ParameterStore.output_token, ParameterStore.top_k, ParameterStore.top_p, max_thread=1)

#         st.session_state.past2.append(user_input2) 
#         st.session_state.generated2.append(outcomes2) 

#     # Display the conversation history
#     with st.expander("Conversation2", expanded=True):

#         for i in range(len(st.session_state["past2"])-1, -1, -1):
#             st.info(st.session_state["past2"][i],icon="😊")
#             st.success(st.session_state["generated2"][i], icon="🤖")
