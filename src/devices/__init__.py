def call_children(children, func_name, *args, **kwargs):
    for c in children:
        getattr(c, func_name)(*args, **kwargs)
