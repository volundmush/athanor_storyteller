import re
from django.conf import settings

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
        if not (found := partial_match(category, candidates)):
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

    def find_template(self, template):
        if not template:
            raise ValueError("Nothing entered for Template!")
        if isinstance(template, DefaultPersona):
            return template
        if not (found := partial_match(template, settings.STORYTELLER_TEMPLATES.keys())):
            raise ValueError(f"No template {template}")
        return settings.STORYTELLER_TEMPLATES[found]

    def change_template(self, session, persona, template):
        if not (enactor := self.get_user(session)):
            raise ValueError("Permission denied!")
        persona = self.find_persona(persona)
        old_template = persona.__class__
        template = self.find_template(template)
        persona.change_template(template)
        entities = {'enactor': enactor, 'target': persona}
        smsg.Template(entities, old_template=old_template)

    def parse_trait(self, trait):
        if ':' in trait:
            path, context = trait.split(':', 1)
            path = path.strip()
            context = context.strip()
        else:
            path = trait
            context = ''
        if '/' in path:
            path = [stripped for p in path.split('/') if (stripped := p.strip())]
        else:
            path = [path.strip()]
        trait = None
        searched = list()
        for entry in path:
            searched.append(entry)
            candidates = DefaultTraitDefinition.objects.filter_family(parent=None)
            if not (found := partial_match(entry, candidates)):
                raise ValueError(f"Cannot locate trait: {'/'.join(searched)}")
            trait = found
        if context and not trait.db_allow_context:
            raise ValueError(f"{trait} does not allow Contexts!")
        if trait.db_require_context and not context:
            raise ValueError(f"{trait} requires a Context!")
        return (trait, context)

    def find_trait(self, persona, trait):
        if not trait:
            raise ValueError("Nothing entered for trait!")
        match = self.re_trait(trait).groupdict()

    def set_trait_value(self, session, persona, trait, value):
        if not (enactor := self.get_user(session)):
            raise ValueError("Permission denied!")
        persona = self.find_persona(persona)
        trait = self.find_trait(persona, trait)
        persona.set_trait_value(trait, value)