"""
multiprocessing.dummy의 Pool 클래스를 사용한다.
"""
from multiprocessing.dummy import Pool as ThreadPool

"""
실제 작업 리스트가 수행하는 함수로 return을 할 수도 있고 직접 처리를 할 수도 있다.
"""
def working(work):
    temp_dict = {}
    temp_dict[work] = work
    #print (temp_dict)
    return temp_dict
    
"""
Thread Pool을 생성하고 pool에 작업 리스트를 할당하는 함수이다.
이 또한 pool.map으로부터 결과를 받게 되면, list 형식으로 데이터를 리턴 받게 된다.
"""
def workThread(worklist, threadnum = 10):
    pool = ThreadPool(threadnum)
    result = pool.map(working, worklist)
    print (result)
    pool.close()
    pool.join()

    return result

number_list = ["shins"]
result = workThread(number_list,3)
print (result)
