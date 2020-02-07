import re
from evennia.typeclasses.models import TypeclassBase
from athanor.gamedb.base import HasAttributeGetCreate, lazy_property
from athanor_storyteller.models import PersonaDB, TraitDefinitionDB, TraitDB, PoolDefinitionDB, PoolDB


class DefaultPersona(HasAttributeGetCreate, PersonaDB, metaclass=TypeclassBase):

    def setup_template(self):
        pass

    def pre_change_template(self, new_template):
        pass

    def change_template(self, new_template):
        self.pre_change_template(new_template)
        old_class = self.__class__
        self.swap_typeclass(new_template, run_start_hooks='None')
        self.setup_template()

    def set_trait_value(self, trait, context, value):
        if not trait.db_allow_buy:
            raise ValueError(f"{trait} is not a trait that can be ")
        if value == 0 and not trait.db_allow_zero:
            raise ValueError(f"{trait} does not allow buying at Zero!")
        if not context:
            context = ''
        found_trait = None
        if not (found_trait := self.traits.filter(db_trait_definition=trait, db_icontext=context.lower())):
            found_trait = trait.trait_typeclass.create(persona=self, trait_def=trait, context=context, value=value)
        else:
            if context:
                found_trait.db_context = context
            found_trait.set_value(value)

    def get_bonus(self, identifier):
        """
        Given a TraitDefinition identifier, return any bonuses this Persona is getting
        to that trait.
        """
        return 0


class DefaultTraitDefinition(HasAttributeGetCreate, TraitDefinitionDB, metaclass=TypeclassBase):
    re_normalize_0 = re.compile(r'\s+')
    re_normalize_1 = re.compile(r"(?i)(?:^|(?<=[_\/\-\|\s()\+]))(?P<name1>[a-z]+)")
    re_normalize_2 = re.compile(r"(?i)\b(of|the|a|and|in)\b")
    re_normalize_3 = re.compile(r"(?i)(^|(?<=[(\|\/]))(of|the|a|and|in)")

    can_mark = []

    @classmethod
    def normalize_name(cls, name):
        name = cls.re_normalize_0.sub(' ', name.strip())
        name = cls.re_normalize_1.sub(name.strip(), lambda find: find.group('name1').capitalize())
        name = cls.re_normalize_2.sub(lambda find: find.group(1).lower(), name)
        name = cls.re_normalize_3.sub(lambda find: find.group(1) + find.group(2).capitalize(), name)
        return name

class DefaultTrait(HasAttributeGetCreate, TraitDB, metaclass=TypeclassBase):

    @lazy_property
    def marked(self):
        return self.get_or_create_attribute(key='marked', default=set())

    def is_marked(self, mark):
        return mark in self.marked

    def set_marked(self, mark):
        if self.is_marked(mark):
            raise ValueError(f"{self} is already marked {mark}!")
        self.marked.add(mark)

    def unset_marked(self, mark):
        if not self.is_marked(mark):
            raise ValueError(f"{self} is already marked {mark}!")
        self.marked.remove(mark)

    @classmethod
    def create(cls, persona, trait_def, context, value):
        return cls(db_persona=persona, db_trait_definition=trait_def, db_context=context, db_icontext=context.lower(), db_base_value=value)

    def __str__(self):
        if self.db_context:
            return f"{self.db_trait_definition}: {self.db_context}"
        return str(self.db_trait_definition.db_key)

    def __int__(self):
        return int(self.db_base_value)

    def _set_value(self, value):
        """
        Implements the meat of setting a value. Cuts down on super() usage.
        """
        old_value = int(self.db_value)
        self.db_base_value = value
        self.at_set_value(old_value)
        return value

    def at_set_value(self, old_value):
        """
        General abstract hook used for things like re-calculating other values.
        """
        pass

    def at_delete(self):
        pass

    def delete_value(self, value):
        self.at_delete()
        self.delete()

    def set_value(self, value):
        """
        Called by the controller to set this Trait's Value.
        """
        if self.db_trait_definition.db_allow_zero:
            if value > -1:
                return self._set_value(value)
            else:
                return self.delete_value(value)
        else:
            if value > 0:
                return self._set_value(value)
            else:
                return self.delete_value(value)

    def calculate(self, bonus=False):
        """
        Returns this trait's value for dice rolls and other purposes.
        """
        if bonus and (identifier := self.db_trait_definition.db_system_identifier):
            return int(self) + self.db_persona.get_bonus(identifier)
        return int(self)


class DefaultPoolDefinition(HasAttributeGetCreate, PoolDefinitionDB, metaclass=TypeclassBase):
    pass


class DefaultPool(HasAttributeGetCreate, PoolDB, metaclass=TypeclassBase):
    pass
