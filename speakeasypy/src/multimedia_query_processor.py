import csv
import json
from datetime import datetime
from difflib import SequenceMatcher

import numpy as np
import rdflib
import spacy
from transformers import pipeline

from speakeasypy import Embeddings_Output


class MultimediaQueryProcessor:

    def __init__(self, graph, ner_pipeline, lbl2ent, images_json_list):
        self.graph = graph
        self.ner_pipeline = ner_pipeline
        self.lbl2ent = lbl2ent
        self.images_json_list = images_json_list

    def find_object_by_property(self, objects, property_name, target_value):
        for obj in objects:
            if property_name in obj:
                if property_name == 'cast':
                    if target_value in obj[property_name] and obj['type'] == 'event':
                        print(obj)
                        return obj
                elif property_name == 'movie':
                    if target_value in obj[property_name] and obj['type'] == 'poster':
                        print(obj)
                        return obj
        return None

    def get_q_id(self, entity):

        best_similarity = 0
        best_match = None
        q_id = ''

        try:
            q_id = self.lbl2ent[entity.strip()]
        except Exception as e:
            for key in self.lbl2ent.keys():
                similarity_ratio = SequenceMatcher(None, entity, key).ratio()
                if similarity_ratio > best_similarity:
                    best_similarity = similarity_ratio
                    best_match = key
            q_id = self.lbl2ent[best_match]

        if q_id is not None:
            q_id = q_id.replace('http://www.wikidata.org/entity/', '')

        return q_id


    def get_image(self, question):
        try:

            WD = rdflib.Namespace('http://www.wikidata.org/entity/')
            WDT = rdflib.Namespace('http://www.wikidata.org/prop/direct/')


            actor_name = ''
            movie_name = ''
            q_id = ''
            imdb_id_val = ''
            image_result = ''
            result = ''

            entities = self.ner_pipeline(question, aggregation_strategy="simple")
            for entity in entities:
                if entity['entity_group'] == 'ACTOR':
                    actor_name = entity['word']
                    q_id = self.get_q_id(actor_name)

                    imdb_id = {str(o) for o in self.graph.objects(WD[q_id], WDT.P345) if o.startswith('nm')}
                    if len(imdb_id) == 1:
                        imdb_id_val = list(imdb_id)[0]
                    result = self.find_object_by_property(self.images_json_list, "cast", imdb_id_val)
                elif entity['entity_group'] == 'TITLE':
                    movie_name = entity['word']
                    q_id = self.get_q_id(movie_name)

                    imdb_id = {str(o) for o in self.graph.objects(WD[q_id], WDT.P345) if o.startswith('tt')}
                    if len(imdb_id) == 1:
                        imdb_id_val = list(imdb_id)[0]
                    result = self.find_object_by_property(self.images_json_list, "movie", imdb_id_val)
                print(actor_name)
                print(movie_name)

            if result is not None:
                image_result = 'image:' + result['img'].replace('.jpg', '')
            return image_result

        except Exception as e:
            print(e)
            return e

# if __name__ == '__main__':
#     # with open('../../data/images.json', 'r') as file:
#     #     json_data = file.read()
#     # data_list = []
#     # try:
#     #     data_list = json.loads(json_data)
#     # except json.decoder.JSONDecodeError as e:
#     #     print("JSON decoding error:", e)
#     #
#     # mqp = MultimediaQueryProcessor(None, None, None, None, None, None, None, data_list)
#     #
#     # result = mqp.find_object_by_property(data_list, "cast", 'nm0000932')
#     # print(result)
#     now = datetime.now()
#
#     current_time = now.strftime("%H:%M:%S")
#     print("Current Time =", current_time)
#     graph = rdflib.Graph()
#     graph.parse('../../data/14_graph.nt', format='turtle')
#     RDFS = rdflib.namespace.RDFS
#     # WD = rdflib.Namespace('http://www.wikidata.org/entity/')
#     # WDT = rdflib.Namespace('http://www.wikidata.org/prop/direct/')
#
#     # print(
#     #     {str(o) for o in graph.objects(WD.Q40523, WDT.P345) if o.startswith('nm')})
#     print({s for s in graph.subjects(None, RDFS.label) if s.startswith('Julia Roberts')})
#
#     ner_pipeline = pipeline('ner', model='planeB/roberta_movie_w_title')
#     nlp = spacy.load(r"../../data/output/model-best")
#     entity_emb = np.load('../../data/entity_embeds.npy')
#     relation_emb = np.load('../../data/relation_embeds.npy')
#     emb = Embeddings_Output(graph, entity_emb, relation_emb)
#
#     with open('../../data/entity_ids.del', 'r') as ifile:
#         ent2id = {rdflib.term.URIRef(ent): int(idx) for idx, ent in csv.reader(ifile, delimiter='\t')}
#         id2ent = {v: k for k, v in ent2id.items()}
#     ent2lbl = {ent: str(lbl) for ent, lbl in graph.subject_objects(RDFS.label)}
#     lbl2ent = {lbl: ent for ent, lbl in ent2lbl.items()}
#
#     with open('../../data/images.json', 'r') as file:
#         json_data = file.read()
#     data_list = []
#     try:
#         data_list = json.loads(json_data)
#     except json.decoder.JSONDecodeError as e:
#         print("JSON decoding error:", e)
#
#     mqp = MultimediaQueryProcessor(graph, ner_pipeline, lbl2ent, data_list)
#     print(mqp.get_image('Show me a picture of Halle Berry.'))
#     now = datetime.now()
#
#     current_time = now.strftime("%H:%M:%S")
#     print("Current Time =", current_time)
