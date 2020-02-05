from evennia.utils.utils import lazy_property
from athanor_storyteller.handlers import PersonaHandler


class StorytellerCharacterMixin(object):

    @lazy_property
    def persona(self):
        return PersonaHandler(self)