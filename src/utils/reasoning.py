from threading import Thread, Event, Condition
from streamlit.runtime.scriptrunner import add_script_run_ctx

import utils.variables as env
from utils.store import ChainsStore
from utils.store import ParameterStore
from utils.palm2 import Palm2_Util


class Reasoning():

    cond = Condition()
    palm2_util = Palm2_Util.instance()

    
    # 2nd step
        # Public search
        # Summarization
        # Reasining 


    def public_search(self,event, job_name, user_input):

        #print(f"Thread {job_name} started \n")

        # Build a prompt for public search. ( no context )
        ChainsStore.public_search_prompt = Reasoning.palm2_util.build_query(user_input= user_input, 
                                                            context = "", 
                                                            prompt = env.public_prompt,
                                                            step="PUBLIC_SEARCH")

        # Public Search
        ChainsStore.public_search_result = Reasoning.palm2_util.generate_response(prompt = ChainsStore.public_search_prompt,
                                                                        temperature=ParameterStore.temperature, 
                                                                        output_token=ParameterStore.output_token, 
                                                                        top_k=ParameterStore.top_k, 
                                                                        top_p=ParameterStore.top_p)

        event.set()
        with Reasoning.cond:
            Reasoning.cond.notify()

        #print(f"Thread {job_name} done")

    def context_summarize(self, event, job_name, user_input):
        
        #print(f"Thread {job_name} started \n")

        # Context Summarization
        ChainsStore.summary_prompt = Reasoning.palm2_util.build_query(user_input= user_input, 
                                                            context = ChainsStore.context_with_reference,  # use context_with_reference
                                                            prompt = env.summary_prompt,
                                                            step="SUMMARIZATION")

        # set temperature to use the facts from the context.
        temperature = 0.2

        ChainsStore.summary_outcomes = Reasoning.palm2_util.generate_response(prompt= ChainsStore.summary_prompt,
                                                                  temperature=temperature, 
                                                                  output_token=ParameterStore.output_token, 
                                                                  top_k=ParameterStore.top_k, 
                                                                  top_p=ParameterStore.top_p)
        event.set()
        with Reasoning.cond:
            Reasoning.cond.notify()

        #print(f"Thread {job_name} done")

    def context_reasoning(self, event, job_name, user_input):
        
        #print(f"Thread {job_name} started \n")
        ChainsStore.reasoning_prompt = Reasoning.palm2_util.build_query(user_input=user_input, 
                                                              context=ChainsStore.context_with_reference, # use context_with_reference
                                                              prompt=ParameterStore.reasoning_prompt_env,
                                                              step="REASONING")
        
        # set temperature to use the facts from the context.
        temperature = 0.2
        ChainsStore.reasoning_outcomes = Reasoning.palm2_util.generate_response(prompt=ChainsStore.reasoning_prompt,
                                                                    temperature=temperature, 
                                                                    output_token=ParameterStore.output_token, 
                                                                    top_k=ParameterStore.top_k, 
                                                                    top_p=ParameterStore.top_p)

        event.set()
        with Reasoning.cond:
            Reasoning.cond.notify()

        #print(f"Thread {job_name} done")

    def consolidate(self, user_input):

        print(f"[Reasoning][consolidate] User input : {user_input}")

        event1 = Event()
        event2 = Event()
        event3 = Event()

        with Reasoning.cond:
            thread1_name = "Public Search"
            thread1 = Thread(target=self.public_search, args=(event1, thread1_name, user_input ))
            add_script_run_ctx(thread1)
            thread1.start()

            thread2_name = "Context Summarization"
            thread2 = Thread(target=self.context_summarize, args=(event2, thread2_name, user_input))
            add_script_run_ctx(thread2)
            thread2.start()

            thread3_name = "Context Reasoning"
            thread3 = Thread(target=self.context_reasoning, args=(event3, thread3_name, user_input))
            add_script_run_ctx(thread3)
            thread3.start()

            while not (event1.is_set() and event2.is_set() and event3.is_set()):
                #print("Entering cond.wait")
                Reasoning.cond.wait()
                #print("Exited cond.wait ({}, {})".format(event1.is_set(), event2.is_set(), event3.is_set()))

            # print(f"public_search_result: {ChainsStore.public_search_result}")
            # print(f"summary_outcomes: {ChainsStore.summary_outcomes}")
            # print(f"reasoning_outcomes: {ChainsStore.reasoning_outcomes}")

            print("[Reasoning][consolidate] All Reasoning thread done")


    def final_request(self, user_input):

        print(f"[Reasoning][final_request] User input : {user_input}")

        ChainsStore.final_context = "\nSUMMARY : " + ChainsStore.summary_outcomes +"\n\n\n REASONING : " + ChainsStore.reasoning_outcomes 
        
        # +"\n\n\n PUBLIC SEARCH : " + ChainsStore.public_search_result

        ChainsStore.final_prompt = Reasoning.palm2_util.build_query(user_input = user_input, 
                                                          context = ChainsStore.final_context, 
                                                          prompt = env.final_prompt,
                                                          step="FINAL")
        
        ChainsStore.final_outcomes = Reasoning.palm2_util.generate_response(prompt=ChainsStore.final_prompt,
                                                                temperature=ParameterStore.temperature, 
                                                                output_token=ParameterStore.output_token, 
                                                                top_k=ParameterStore.top_k, 
                                                                top_p=ParameterStore.top_p)

        print(f"[Reasoning][final_request] Done.")
