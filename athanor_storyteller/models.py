from evennia.utils.utils import class_from_module
from django.db import models
from evennia.typeclasses.models import TypedObject, SharedMemoryModel


class StorySystem(SharedMemoryModel):
    db_key = models.CharField(max_length=255, null=False, blank=False, unique=True)


class PersonaDB(TypedObject):
    """
    A Persona is a container for a character sheet based on an ObjectDB instance.
    In general, an Object will have only one Persona, but certain SToryteller systems
    may call for having several. It can also allow one person to manage many NPCs, or
    similar scenarios.
    """
    __settingclasspath__ = "athanor_storyteller.traits.DefaultPersona"
    __defaultclasspath__ = "athanor_storyteller.traits.DefaultPersona"
    __applabel__ = "athanor_storyteller"

    # the db_key is the Persona's 'name.'
    db_ikey = models.CharField(max_length=255, null=False, blank=False)
    db_object = models.ForeignKey('objects.ObjectDB', related_name='personas', on_delete=models.PROTECT)

    # The template key holds a string key that's used to relate the Persona to a Template
    # (Vampire, Mage, Solar, Lunar, etc). This will be used to locate a Class.
    db_template_key = models.CharField(max_length=255, default='mortal', null=False)

    db_system = models.ForeignKey(StorySystem, related_name='personas', on_delete=models.PROTECT)

    class Meta:
        unique_together = (('db_object', 'db_system', 'db_ikey'))


class TraitDefinitionDB(TypedObject):
    """
    TraitDefinitions are the 'rules' and structure for Abilities, Charms, Disciplines, Attributes, etc.
    """
    __settingclasspath__ = "athanor_storyteller.traits.DefaultTraitDefinition"
    __defaultclasspath__ = "athanor_storyteller.traits.DefaultTraitDefinition"
    __applabel__ = "athanor_storyteller"

    db_system = models.ForeignKey(StorySystem, related_name='trait_definitions', on_delete=models.PROTECT)
    # db_key is used as a sort of per-parent unique identifier for when traversing the tree.
    db_parent = models.ForeignKey('self', related_name='children', null=True, on_delete=models.PROTECT)

    # The system identifier is a string used to identify this trait in the database for the plugin
    # system to get-create-update it. this is usually a flat and simple string, like attribute_strength
    # This identifier will also be used for bonuses and other purposes.
    db_system_identifier = models.CharField(max_length=255, null=True, blank=False)

    # The child and trait typeclass fields contain python paths to which typeclasses will be used for
    # new children of this Definition, and a Trait based on this definition, respectively.
    db_child_default_typeclass = models.CharField(max_length=255, null=True, blank=False)
    db_trait_default_typeclass = models.CharField(max_length=255, null=True, blank=False)

    # If a newly created Persona passes this TraitDefinition's default access lock,
    # the value it will be obtained at.
    db_default_value = models.BigIntegerField(default=0)

    db_allow_context = models.BooleanField(default=False, null=False)
    db_require_context = models.BooleanField(default=False, null=False)

    db_can_specialize = models.BooleanField(default=False, null=False)
    db_can_roll = models.BooleanField(default=False, null=False)

    # A Trait that allows Zero can be 'purchased' at 0 so you can use it as a base for other traits.
    # This has no affect on automated add processes, only the UI.
    db_allow_zero = models.BooleanField(default=False, null=False)

    # If this is false, this trait cannot be bought. SEt this false for any TraitDefinition that
    # only serves as a 'Category' parent.
    db_allow_buy = models.BooleanField(default=True, null=False)

    # Marks whether this trait has been approved by staff or not. This only affects the UI
    # experience during Chargen. Relevant only for traits created during play.
    db_approved = models.BooleanField(default=True, null=False)

    def __str__(self):
        return str(self.db_key)

    def fullpath(self):
        par = self.db_parent
        full = [self]
        while par:
            full.append(par)
            par = par.db_parent
        return '/'.join(str(trait) for trait in reversed(full))

    @property
    def trait_typeclass(self):
        if not (default := self.db_trait_default_typeclass) and not self.db_parent:
            return self.__class__
        if default:
            return class_from_module(default)
        return self.db_parent.trait_typeclass

    class Meta:
        unique_together = (('db_system', 'db_parent', 'db_key'), ('db_system', 'db_system_identifier'))
        verbose_name = 'TraitDefinition'
        verbose_name_plural = 'TraitDefinitions'


class TraitDB(TypedObject):
    """
    This model governs the traits possessed by a specific Persona.
    """
    __settingclasspath__ = "athanor_storyteller.traits.DefaultTrait"
    __defaultclasspath__ = "athanor_storyteller.traits.DefaultTrait"
    __applabel__ = "athanor_storyteller"

    # db_key isn't really important here; don't rely on it for anything.
    db_persona = models.ForeignKey(PersonaDB, related_name='traits', on_delete=models.CASCADE)
    db_trait_definition = models.ForeignKey(TraitDefinitionDB, related_name='traits', on_delete=models.PROTECT)
    db_context = models.CharField(max_length=255, null=False, blank=True, default='')
    db_icontext = models.CharField(max_length=255, null=False, blank=True, default='')
    db_base_value = models.BigIntegerField(default=0, null=False, blank=False)
    db_damage_value = models.BigIntegerField(default=0, null=False, blank=False)

    class Meta:
        unique_together = (('db_persona', 'db_trait', 'db_icontext'),)
        verbose_name = 'Trait'
        verbose_name_plural = 'Traits'

    def fullpath(self):
        if self.db_context:
            return f"{self.db_trait_definition.fullpath()}: {self.db_context}"
        return self.db_trait_definition.fullpath()


class PoolDefinitionDB(TypedObject):
    __settingclasspath__ = "athanor_storyteller.traits.DefaultPoolDefinition"
    __defaultclasspath__ = "athanor_storyteller.traits.DefaultPoolDefinition"
    __applabel__ = "athanor_storyteller"

    db_system = models.ForeignKey(StorySystem, related_name='trait_definitions', on_delete=models.PROTECT)
    db_system_identifier = models.CharField(max_length=255, null=True, blank=False)

    class Meta:
        unique_together = (('db_system', 'db_system_identifier'), )
        verbose_name = 'PoolDefinition'
        verbose_name_plural = 'PoolDefinitions'


class PoolDB(TypedObject):
    __settingclasspath__ = "athanor_storyteller.traits.DefaultPool"
    __defaultclasspath__ = "athanor_storyteller.traits.DefaultPool"
    __applabel__ = "athanor_storyteller"

    db_persona = models.ForeignKey(PersonaDB, related_name='pools', on_delete=models.CASCADE)
    db_pool_definition = models.ForeignKey(PoolDefinitionDB, related_name='pools', on_delete=models.PROTECT)
    db_bonus_maximum = models.IntegerField(default=0, null=False, blank=False)
