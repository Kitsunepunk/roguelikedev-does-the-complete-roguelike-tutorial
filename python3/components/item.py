class Item:
    def __init__(self, use_func, targeting=False, targeting_msg=None, **kwargs):
        self.use_func = use_func
        self.targeting = targeting
        self.targeting_msg = targeting_msg
        self.function_kwargs = kwargs
