

"""
An Entity ( as in Entity Component System design ).
"""
import uuid


class Entity:  # Should be a very simple record.

    def __init__(self, *components):
        self.id = uuid.uuid4()  # is this actually useful ?
        # TODO : Some better /more optimized way ?
        self.components = dict()
        # filling in the components
        for c in components:
            self.components[type(c)] = c

    def __hash__(self):
        """ Unique Id for entity """
        return hash((self.id, self.components))

    # iterable interface, but access via type
    def __iter__(self):
        return (c for c in self.components.values())

    def __getitem__(self, item):
        return self.components.get(item)

    # TODO : getattr to component dict...

#TODO : World as a collection of identities + event loop management...