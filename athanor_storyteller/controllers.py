from evennia.utils.logger import log_trace
from evennia.utils.utils import class_from_module
from evennia.utils.ansi import ANSIString

from athanor.utils.text import partial_match
from athanor.controllers.base import AthanorController
from athanor.utils.time import utcnow

from athanor_storyteller.gamedb import DefaultTrait, DefaultTraitDefinition, DefaultPersona
from athanor_storyteller import messages as smsg


class AthanorPersonaController( AthanorController):
    system_name = 'PERSONA'

    def do_load(self):
        from django.conf import settings

        try:
            persona_typeclass = settings.PERSONA_TYPECLASS
            self.persona_typeclass = class_from_module(persona_typeclass, defaultpaths=settings.TYPECLASS_PATHS)
        except Exception:
            log_trace()
            self.persona_typeclass = DefaultPersona

        try:
            definition_typeclass = settings.TRAIT_DEFINITION_TYPECLASS
            self.definition_typeclass = class_from_module(definition_typeclass, defaultpaths=settings.TYPECLASS_PATHS)
        except Exception:
            log_trace()
            self.definition_typeclass = DefaultTraitDefinition

        try:
            trait_typeclass = settings.TRAIT_TYPECLASS
            self.trait_typeclass = class_from_module(trait_typeclass, defaultpaths=settings.TYPECLASS_PATHS)
        except Exception:
            log_trace()
            self.trait_typeclass = DefaultTrait

    def get_user(self, session):
        return session.get_account()

    def create_persona(self, session, character, name, typeclass=None):
        if not (enactor := self.get_user(session)):
            raise ValueError("Permission denied!")
        character = self.manager.get('character').find_character(character)
        if not typeclass:
            typeclass = self.persona_typeclass
        new_persona = typeclass.create(character, name)
        entities = {'enactor': enactor, 'target': new_persona}
        smsg.Create(entities).send()
        return new_persona

    def find_persona(self, persona):
        if isinstance(persona, DefaultPersona):
            return persona
        if '/' not in persona:
            raise ValueError("Must address persona by <character>/<persona>")
        character, persona = persona.split('/', 1)
        character = self.manager.get('character').find_character(character)
        if not (candidates := DefaultPersona.objects.filter_family(db_character=character)):
            raise ValueError(f"No Personas for {character}!")
        if not (found := partial_match(persona, candidates)):
            raise ValueError(f"Persona '{persona}' not found!")
        return found

    def rename_persona(self, session, persona, new_name=None):
        if not (enactor := self.get_user(session)) and self.parent_operator(enactor):
            raise ValueError("Permission denied!")
        persona = self.find_persona(persona)
        old_name = persona.key
        new_name = persona.rename(new_name)
        entities = {'enactor': enactor, 'target': persona}
        smsg.Rename(entities, old_name=old_name).send()

    def delete_persona(self, session, persona, verify_name):
        if not (enactor := self.get_user(session)):
            raise ValueError("Permission denied!")
        persona = self.find_persona(persona)
        entities = {'enactor': enactor, 'target': persona}
        smsg.Delete(entities).send()
        persona.delete()

