
import time
import streamlit as st

import os
import sys

directory = os.getcwd()
# Append sys path to refer utils.
sys.path.append(directory+"/src")

import utils.variables as env
from utils.palm2 import Palm2_Util
from utils.enterprise_search import EnterpriseSearch

palm2_util = Palm2_Util.instance()
es = EnterpriseSearch()

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
        st.warning('Put your Enterprise Search Endpoint in "Configuration > Enterprise Search" to get the context ', icon="⚠️")
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
        model = st.selectbox(label='Model', options=[env.MODEL])
        n_threads = st.number_input(' Number of Answer ',min_value=1,max_value=5, value=3)
        st.markdown("""---""")
        temperature = st.number_input(' Temperature ',min_value=0.0,max_value=1.0,step=0.1, format="%.1f",value= env.TEMPERATURE)
        output_token = st.number_input(' Output Token ',min_value=100,max_value=1024,value=env.MAX_OUTPUT_TOKENS )
        top_k = st.number_input(' Top K ',min_value=1,max_value=40, value=env.TOP_K)
        top_p = st.number_input(' Top P ',min_value=0.0,max_value=1.0,step=0.1, format="%.1f",value= env.TOP_P)

    with side_tab2 : 
        default_prompt = st.text_area("Add default prompt, this will be added automatically in front of your request", value= env.default_prompt_value)
        es_url = st.text_area("Put your Enterprise engine url to search context",value=env.end_point)
        num_es = st.number_input(' (#) of Enterprise search results',min_value=1,max_value=5, value=2)

# Set up the Streamlit app layout
st.title("Palm2 + ES Tester")
st.subheader("An emulator to interact with Google Palm2 and Enterprise Search")

context = None
context_with_reference = None
prompt = None
outcomes = None

snippets_ctx = None
segments_ctx = None
latency_str = None

tab1, tab2, tab3, tab4 = st.tabs(["Ask PaLM2 + ES (Internal References)", "Response Analysis", "Response Details ", "Ask PaLM2 (Public References)"])

with tab1 : 
    # Get the user input
    user_input = get_text()

    if st.button("Ask Palm2 + ES"):

        t1 = time.time()
        search_result = es.retrieve_discovery_engine(es_url, num_es, user_input )

        t2 = time.time()
        context, context_with_reference, snippets_ctx, segments_ctx = es.parse_discovery_results(search_result)

        t3 = time.time()
        prompt = palm2_util.build_query(user_input, context, default_prompt)

        t4 = time.time()
        #output = palm2_util.generate_response(prompt,temperature, output_token, top_k, top_p)
        outcomes = palm2_util.concurrent_call(prompt,temperature, output_token, top_k, top_p, n_threads)

        if palm2_util.LOGGING:
            palm2_util.log("INFO", f"Response from PaLM2 :\n {outcomes}")
            palm2_util.log("INFO","\n\n-------------------------[ Query End ]---------------------------\n\n")

        t5 = time.time()

        palm2_util.log("INFO",f"\n\n-------------------[ Execution Time ]-----------------------")
        palm2_util.log("INFO",f'Execution time: retrieve_discovery_engine : {t2-t1} seconds')
        palm2_util.log("INFO",f'Execution time: parse_discovery_results :  {t3-t2} seconds')
        palm2_util.log("INFO",f'Execution time: build_query :  {t4-t3} seconds')
        palm2_util.log("INFO",f'Execution time: generate_response :  {t5-t4} seconds')
        palm2_util.log("INFO",f"---------------------[ Total : {t5-t1} seconds ]------------------------")

        latency_str = f"Enterprise Search : [{t2-t1}], Parse_discovery_results : [{t3-t2}], Build_query : [{t4-t3}], LLM Execution : [{t5-t4}], Total elapsed time :[{t5-t1}] "
        
        st.session_state.past.append(user_input) 
        st.session_state.generated.append(outcomes) 

    # Display the conversation history
    with st.expander("Conversation", expanded=True):
        for i in range(len(st.session_state["past"])-1, -1, -1):
            st.info(st.session_state["past"][i],icon="😊")
            st.success(st.session_state["generated"][i], icon="🤖")

with tab2:
    st.subheader("Review the output from Palm2")
    with st.expander("Enterprise Search result"):
        st.write(context_with_reference)
    with st.expander("Final Prompt"):
        st.write(prompt)
    with st.expander("Answer from Palm2"):
        st.write(outcomes)

with tab3:
    st.subheader("Detailed information about response from the Enterprise Search")
    with st.expander("Enterprise Search Snippets"):
        st.write(snippets_ctx)
    with st.expander("Enterprise Search Segments"):
        st.write(segments_ctx)        
    with st.expander("Total Latency"):
        st.write(latency_str)

with tab4:
    # Get the user input
    user_input2 = get_text2()

    if st.button("Ask Palm2"):    
        outcomes2 = palm2_util.concurrent_call(user_input2,temperature, output_token, top_k, top_p, n_threads)

        st.session_state.past2.append(user_input2) 
        st.session_state.generated2.append(outcomes2) 

    # Display the conversation history
    with st.expander("Conversation2", expanded=True):

        for i in range(len(st.session_state["past2"])-1, -1, -1):
            st.info(st.session_state["past2"][i],icon="😊")
            st.success(st.session_state["generated2"][i], icon="🤖")
