from threading import Thread, Event, Condition
from streamlit.runtime.scriptrunner import add_script_run_ctx

import utils.variables as env
from utils.store import ChainsStore
from utils.store import ParameterStore

from utils.enterprise_search import EnterpriseSearch

class RAG():

    cond = Condition()

    # Search Enterprise
    # Vector database search

    def enteprise_search(self,event, job_name, user_input):

        #print(f"Thread {job_name} started \n")
        
        es = EnterpriseSearch()
        ChainsStore.es_search_result = es.retrieve_discovery_engine(ParameterStore.es_url, ParameterStore.num_es, user_input )
        ChainsStore.context, ChainsStore.context_with_reference = es.parse_discovery_results(ChainsStore.es_search_result)

        event.set()
        with RAG.cond:
            RAG.cond.notify()

        #print(f"Thread {job_name} done")

    def vectordb_search(self, event, job_name, user_input):
        
        #print(f"Thread {job_name} started \n")

        # Need to add the logic.
        ChainsStore.vectordb_search_result = ""

        event.set()
        with RAG.cond:
            RAG.cond.notify()

        #print(f"Thread {job_name} done")

    def rag_search(self, user_input):
        print(f"[RAG][rag_search] user input : {user_input}")

        event1 = Event()
        event2 = Event()

        with RAG.cond:
            thread1_name = "Enteprise_Search"
            thread1 = Thread(target=self.enteprise_search, args=(event1, thread1_name, user_input ))
            add_script_run_ctx(thread1)
            thread1.start()

            thread2_name = "VectorDB_Search"
            thread2 = Thread(target=self.vectordb_search, args=(event2, thread2_name, user_input))
            add_script_run_ctx(thread2)
            thread2.start()

            while not (event1.is_set() and event2.is_set()):
                #print("Entering cond.wait")
                RAG.cond.wait()
                #print("Exited cond.wait ({}, {})".format(event1.is_set(), event2.is_set()))

        
        print("[RAG][rag_search] All Search threads done")

