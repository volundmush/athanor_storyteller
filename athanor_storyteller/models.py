from django.db import models
from evennia.typeclasses.models import TypedObject


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
    db_object = models.ForeignKey('objects.ObjectDB', related_name='personas', on_delete=models.PROTECT)

    # The template key holds a string key that's used to relate the Persona to a Template
    # (Vampire, Mage, Solar, Lunar, etc). This will be used to locate a Class.
    db_template_key = models.CharField(max_length=255, default='mortal', null=False)


class TraitDefinitionDB(TypedObject):
    """
    TraitDefinitions are the 'rules' and structure for Abilities, Charms, Disciplines, Attributes, etc.
    """
    __settingclasspath__ = "athanor_storyteller.traits.DefaultTraitDefinition"
    __defaultclasspath__ = "athanor_storyteller.traits.DefaultTraitDefinition"
    __applabel__ = "athanor_storyteller"

    # db_key is used as a sort of per-parent unique identifier for when traversing the tree.
    db_parent = models.ForeignKey('self', related_name='children', null=True, on_delete=models.PROTECT)

    # The system identifier is a string used to identify this trait in the database for the plugin
    # system to get-create-update it. this is usually a flat and simple string, like attribute_strength
    db_system_identifier = models.CharField(max_length=255, null=True, blank=False, unique=True)

    # The child and trait typeclass fields contain python paths to which typeclasses will be used for
    # new children of this Definition, and a Trait based on this definition, respectively.
    db_child_default_typeclass = models.CharField(max_length=255, null=True, blank=False)
    db_trait_default_typeclass = models.CharField(max_length=255, null=True, blank=False)

    # The proper name of how this Trait should be displayed.
    db_formal_name = models.CharField(max_length=255, null=False, blank=False)

    # If a newly created Persona passes this TraitDefinition's default access lock,
    # the value it will be obtained at.
    db_default_value = models.BigIntegerField(default=0)

    db_allow_context = models.BooleanField(default=False, null=False)
    db_require_context = models.BooleanField(default=False, null=False)

    class Meta:
        unique_together = (('db_parent', 'db_key'), ('db_parent', 'db_formal_name'),)
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
    db_trait = models.ForeignKey(TraitDefinitionDB, related_name='traits', on_delete=models.PROTECT)
    db_context = models.CharField(max_length=255, null=False, blank=True, default='')
    db_icontext = models.CharField(max_length=255, null=False, blank=True, default='')
    db_base_value = models.BigIntegerField(default=0, null=False, blank=False)
    db_damage_value = models.BigIntegerField(default=0, null=False, blank=False)

    class Meta:
        unique_together = (('db_persona', 'db_trait', 'db_icontext'),)
        verbose_name = 'Trait'
        verbose_name_plural = 'Traits'
