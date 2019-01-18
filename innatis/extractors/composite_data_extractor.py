from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import warnings
import re

from builtins import str
from typing import Any
from typing import Dict
from typing import Optional
from typing import Text

from rasa_nlu import utils

from rasa_nlu.train import create_argument_parser
from rasa_nlu.training_data.loading import _guess_format

from rasa_nlu.training_data.formats import DialogflowReader
from rasa_nlu.training_data.formats.dialogflow import DIALOGFLOW_ENTITIES

RASA_NLU = "rasa_nlu"

class CompositeDataExtractor():

    def get_data(self, language):
        lookup_tables = {}
        composite_entities = []

        cmdline_args = create_argument_parser().parse_args()
        files = utils.list_files(cmdline_args.data)

        for file in files:
            fformat = _guess_format(file)
            file_content = utils.read_json_file(file)
            if fformat == DIALOGFLOW_ENTITIES:
                entity = file_content['name']
                dialogflowReader = DialogflowReader()
                examples_js = dialogflowReader._read_examples_js(fn=file, language=language, fformat=fformat)
                lookup_table = self._extract_lookup_tables(examples_js)
                if lookup_table:
                    lookup_tables[entity] = lookup_table
                composite_entity = self._extract_composite_entities(
                            entity,
                            examples_js)
                if(composite_entity):
                    composite_entities.append(composite_entity)

            if fformat == RASA_NLU:
                rasa_nlu_data = file_content['rasa_nlu_data']
                composite_entities = rasa_nlu_data['composite_entities']
                lookup_tables = rasa_nlu_data['lookup_tables']

        return lookup_tables, composite_entities

    def _extract_composite_entities(self, entity, synonyms):
        """Extract the composite entities"""
        composite_entities = set()
        words = [
            s["value"].split(" ") for s in synonyms
            if "value" in s and "@" in s["value"]]
        words = self._flatten(words)
        for word in words:
            composite_entities = self._add_to_composites(
                                    word,
                                    composite_entities)
        if len(composite_entities) == 0:
            return False
        return {
            'name': entity,
            'composites': list(composite_entities)
        }

    def _add_to_composites(self, each, composite_entities):
        if each:
            if(each[0:11] == '@sys.number'):
                composite_entities.add("@" + each[12:])
            else:
                composite_entities.add(each.split(':')[0])
        return composite_entities

    def _extract_lookup_tables(self, examples):
        """Extract the lookup table from the entity synonyms"""
        return {
            synonym: spec["value"] for spec in examples for synonym in spec["synonyms"] if "@" not in synonym
        }

    def _flatten(self, list_of_lists):
        return [item for items in list_of_lists for item in items]
