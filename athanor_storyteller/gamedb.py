from evennia.typeclasses.models import TypeclassBase
from athanor_storyteller.models import PersonaDB, TraitDefinitionDB, TraitDB


class DefaultPersona(PersonaDB, metaclass=TypeclassBase):
    pass


class DefaultTraitDefinition(TraitDefinitionDB, metaclass=TypeclassBase):
    pass


class DefaultTrait(TraitDB, metaclass=TypeclassBase):
    pass

