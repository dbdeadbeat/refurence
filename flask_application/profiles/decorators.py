def ajax_catch_error(func):
    def func_wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print "BAD", e
    return func_wrapper
