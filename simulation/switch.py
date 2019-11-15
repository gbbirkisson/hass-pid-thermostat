import logging


def fake_switch(name):
    return _Switch(name)


class _Switch:
    def __init__(self, name):
        self._on = False
        self._name = name

    def __call__(self, on):
        if self._on != on:
            logging.debug('FakeSwitch {} set {}'.format(self._name, 'ON' if on else 'OFF'))
            self._on = on

    def is_on(self):
        return self._on
