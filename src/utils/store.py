

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

class Instance_Store(SingletonInstane):
 
    context = None
    context_with_reference = None
    prompt = None
    outcomes = None

    chat = None

    def __init__(self):

        """ Initialize VertexAI instance in a way of langchain library. """
        print("Create instance of Instance_Store")
