"""
Authors: Ayobami Akingbade & Sam Havens
Company: CarLabs
Date: November 13, 2018

Pulled from the PR that we opened into Rasa NLU on October 11, 2018.
"""

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
from rasa_nlu.extractors import EntityExtractor
from rasa_nlu.training_data import Message, TrainingData
from rasa_nlu.utils import write_json_to_file

from innatis.extractors.composite_data_extractor import CompositeDataExtractor
from fuzzywuzzy import process

from word2number import w2n

try:
    # Python 2
    from __builtin__ import str as builtin_str
except ImportError:
    # Python 3
    from builtins import str as builtin_str

COMPOSITE_ENTITIES_FILE_NAME = "composite_entities.json"

class CompositeEntityExtractor(EntityExtractor):

    name = "composite_entity_extractor"
    requires = ["entities"]
    provides = ["composite_entities"]
    defaults = {
        "fuzzy_matching": False,
        "fuzzy_threshold": 90
    }

    def __init__(self, component_config=None, composite_entities=None):
        # type: (Optional[Dict[Text, Text]]) -> None
        super(CompositeEntityExtractor, self).__init__(component_config)
        if composite_entities:
            self.composite_entities = composite_entities
        else:
            self.composite_entities = {
                'lookup_tables': [],
                'composite_entities': []
            }

    def train(self, training_data, cfg, **kwargs):
        compositeDataExtractor = CompositeDataExtractor()
        lookup_tables, composite_entities = compositeDataExtractor.get_data(
            language=cfg.language)
        self.composite_entities['lookup_tables'] = lookup_tables
        self.composite_entities['composite_entities'] = composite_entities

    def process(self, message, **kwargs):
        # type: (Message, **Any) -> None
        entities = message.get("entities", [])[:]
        self.split_composite_entities(entities)
        self.convert_non_composite_entities(entities)
        message.set("entities", entities, add_to_output=True)

    def persist(self, model_dir):
        # type: (Text) -> Optional[Dict[Text, Any]]
        if self.composite_entities:
            composite_entities_file = os.path \
                                        .join(model_dir,
                                              COMPOSITE_ENTITIES_FILE_NAME)
            write_json_to_file(composite_entities_file,
                               self.composite_entities,
                               separators=(',', ': '))

    @classmethod
    def load(cls,
             model_dir=None,  # type: Optional[Text]
             model_metadata=None,  # type: Optional[Metadata]
             cached_component=None,  # type: Optional[CompositeEntitiesMapper]
             **kwargs  # type: **Any
             ):
            # type: (...) -> CompositeEntitiesMapper

        meta = model_metadata.for_component(cls.name)
        file_name = meta.get("composite_entities_file",
                             COMPOSITE_ENTITIES_FILE_NAME)
        composite_entities_file = os.path.join(model_dir, file_name)

        if os.path.isfile(composite_entities_file):
            composite_entities = utils.read_json_file(composite_entities_file)
        else:
            composite_entities = {
                'lookup_tables': [],
                'composite_entities': []
            }
            warnings.warn("Failed to load composite entities file from '{}'"
                          "".format(composite_entities_file))

        return cls(meta, composite_entities)

    def get_relevance(self,
                      broad_value,
                      composite_composite_examples):
        relevance_score = 0
        for example in composite_composite_examples:
            if example in broad_value:
                relevance_score += 1
        return relevance_score

    def merge_two_dicts(self, x, y):
        z = x.copy()
        z.update(y)
        return z

    def break_on_lookup_tables(self, each_lookup,
                               child_name,
                               broad_value):
        # fuzzy matching should go here
        for lookup_entry, alias in each_lookup.items():
            find_index = broad_value.find(lookup_entry.lower())
            if(find_index > -1):
                return {
                    child_name: alias
                }
        return {}

    def split_by_lookup_tables(self, composite_child, broad_value):
        broken_entity = {}
        child_name = composite_child[1:]

        if child_name in self.composite_entities['lookup_tables']:
            broken_entity = self.merge_two_dicts(
                broken_entity,
                self.break_on_lookup_tables(self.composite_entities['lookup_tables'][child_name],
                                            child_name,
                                            broad_value))
        return broken_entity

    def find_number_in_words(self, word):
        match = False
        try:
            match = w2n.word_to_num(builtin_str(word))
        except ValueError:
            pass
        return match

    def find_number_by_regex(self, child_name, broad_value):
        match = False
        expression = r'\d+'
        if(child_name == 'year'):
            expression = r'\d{4}'
        match = re.findall(expression, broad_value)
        if match:
            match = match[0]
        return match

    def split_by_sys(self, composite_child, broad_value):
        broken_entity = {}
        if(composite_child in ['@number', '@year']):
            child_name = composite_child[1:]
            match = self.find_number_by_regex(child_name, broad_value)
            if not match:
                match = self.find_number_in_words(broad_value)
            if match:
                broken_entity[child_name] = int(match)
        return broken_entity

    def split_one_level(self, composite_child, broad_value):
        broken_entity = {}
        broken_entity = self.merge_two_dicts(
            broken_entity,
            self.split_by_lookup_tables(
                composite_child,
                broad_value)
        )
        broken_entity = self.merge_two_dicts(
            broken_entity,
            self.split_by_sys(
                composite_child,
                broad_value)
        )
        return broken_entity

    def get_most_relevant_composite(self,
                                    composite_composites,
                                    broad_value):
        highest_relevance_score = 0
        composite_examples = []
        relevance_score = self.get_relevance(
            broad_value, composite_composites)
        if(relevance_score > highest_relevance_score):
            highest_relevance_score = relevance_score
            composite_examples = composite_composites
        return {
            "highest_relevance_score": highest_relevance_score,
            "composite_examples": composite_examples
        }

    def add_most_relevant_composite(self,
                                    most_relevant_composite,
                                    broken_entity,
                                    child_name,
                                    broad_value
                                    ):
        if(most_relevant_composite['highest_relevance_score'] > 0):
            broken_entity[child_name] = {}
            ce = most_relevant_composite['composite_examples']
            composite_children = [child for child in ce if child[0] == '@']
            for composite_child in composite_children:
                broken_entity[child_name] = self.merge_two_dicts(
                    broken_entity[child_name],
                    self.split_one_level(
                        composite_child,
                        broad_value)
                )
        return broken_entity

    def split_two_levels(self, composite_child, broad_value):
        broken_entity = {}
        child_name = composite_child[1:]
        for each_composite in self.composite_entities['composite_entities']:
            if(each_composite['name'] == child_name):
                composite_composites = each_composite['composites']
                most_relevant_composite = self.get_most_relevant_composite(
                    composite_composites, broad_value)
                broken_entity = self.add_most_relevant_composite(
                    most_relevant_composite,
                    broken_entity,
                    child_name,
                    broad_value
                )
        return broken_entity

    def split_composite_entity(self, composite_entry, entity):
        broken_entity = {}
        broad_value = entity["value"].lower()
        composite_children = composite_entry['composites']
        for composite_child in composite_children:
            if(composite_child[0] == '@'):

                broken_entity = self.merge_two_dicts(
                    broken_entity,
                    self.split_one_level(
                        composite_child,
                        broad_value
                    )
                )

                broken_entity = self.merge_two_dicts(
                    broken_entity,
                    self.split_two_levels(
                        composite_child,
                        broad_value
                    )
                )

        entity["value"] = broken_entity
        self.add_processor_name(entity)

    def convert_non_composite_entities(self, entities):
        # Add fuzzy matching here
        lookup_table = self.composite_entities['lookup_tables']
        for entity in entities:
            entity_name = entity["entity"]
            entity_value = entity["value"]
            if not isinstance(entity_value, str):
                continue

            if self.component_config["fuzzy_matching"]:
                if entity_name.lower() in lookup_table:
                    fuzzy_matched_value = process.extractOne(
                        entity_value,
                        lookup_table[entity_name].keys(),
                        score_cutoff=self.component_config["fuzzy_threshold"]
                    )
                    if fuzzy_matched_value:
                        entity["value"] = lookup_table[entity_name.lower()][fuzzy_matched_value[0]]
                        self.add_processor_name(entity)
            elif entity_name.lower() in lookup_table and entity_value.lower() in lookup_table[entity_name.lower()]:
                entity["value"] = lookup_table[entity_name.lower()][entity_value.lower()]
                self.add_processor_name(entity)

    def split_composite_entities(self, entities):
        for each_entity in entities:
            entity = each_entity["entity"]
            ces = self.composite_entities['composite_entities']
            for composite_entry in ces:
                if(composite_entry['name'] == entity):
                    self.split_composite_entity(composite_entry, each_entity)
