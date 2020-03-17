import logging

from hass.components import Switch


class SSR(Switch):
    def __init__(self, mqtt, switch_func):
        super().__init__(mqtt, 'ssr')
        self._on = False
        self._switch_func = switch_func

    def state_get(self):
        return self._on

    def state_set(self, state):
        if self._on != state:
            self._on = state
            logging.debug('SSR set {}'.format('ON' if self._on else 'OFF'))
            self._switch_func(state)
            return True
        return False

    def __call__(self, state):
        self.state_set(state)
