import os


class Component:
    pass


def env(key, default=None):
    return os.environ.get(key, default)


def env_float(key, default=None):
    r = env(key, str(default))
    if r is None:
        return default
    return float(r)


def env_int(key, default=None):
    r = env(key, str(default))
    if r is None:
        return default
    return int(r)


def env_bool(key, default=None):
    r = env(key, str(default))
    if r is None:
        default
    return r.lower() in ['1', 'true', 'yes', 'y']


def device_and_component_info(postfix=None):
    COMPONENT_ID = env('COMPONENT_ID', 'boiler')

    if postfix is not None:
        COMPONENT_ID = COMPONENT_ID + "_" + postfix

    COMPONENT_NAME = env('COMPONENT_NAME', COMPONENT_ID.replace('_', ' ').title())

    return COMPONENT_ID, COMPONENT_NAME
