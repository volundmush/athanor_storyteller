from evennia.typeclasses.models import TypeclassBase
from athanor_storyteller.models import PersonaDB, TraitDefinitionDB, TraitDB


class DefaultPersona(PersonaDB, metaclass=TypeclassBase):

    def setup_template(self):
        pass

    def pre_change_template(self, new_template):
        pass

    def change_template(self, new_template):
        self.pre_change_template(new_template)
        old_class = self.__class__
        self.swap_typeclass(new_template, run_start_hooks='None')
        self.setup_template()



class DefaultTraitDefinition(TraitDefinitionDB, metaclass=TypeclassBase):
    pass


class DefaultTrait(TraitDB, metaclass=TypeclassBase):
    pass

