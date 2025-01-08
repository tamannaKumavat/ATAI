import csv
import difflib

import pandas as pd

from speakeasypy import CrowdSoruce


class ClosedQuestionProcessor:

    def __init__(self, graph, ner_pipeline, nlp, sparql_query_interpreter, emb):
        self.graph = graph
        self.ner_pipeline = ner_pipeline
        self.nlp = nlp
        self.sparql_query_interpreter = sparql_query_interpreter
        self.emb = emb

    def get_relation(self, question, entity_name):
        text = question.replace(entity_name, '').replace('?', '').replace('.', '')
        relations = []
        doc = self.nlp(text)
        relation_word = []
        p_id = ''
        relation = ''
        for token in doc:
            if token.pos_ in ['NOUN', 'VERB', 'PROPN']:
                if token.text not in relations:
                    if token.lemma_.upper() != 'MOVIE':
                        relation_word.append(token.lemma_)
        relation = " ".join(relation_word)
        for key, synonyms in self.synonym_properties.items():
            if relation in synonyms:
                relation = key
        if relation == 'rating':
            p_id = 'ddis:rating'
        with open('./../data/entity_relations.csv', mode="r") as file:
            reader = csv.reader(file)

            # Iterate over rows
            for i, row in enumerate(reader):
                # Each row is a dictionary with keys as header values
                if relation.lower() == row[0].lower():
                    p_id = row[1].replace('http://www.wikidata.org/prop/direct/', 'wdt:')
            return p_id

    def get_exact_relation(self, input_string, string_list, threshold=0.8):
        # close_matches = difflib.get_close_matches(input_string, string_list, n=1, cutoff=threshold)
        # return close_matches
        for item in string_list:
            if input_string.upper().find((item.upper())) > -1:
                return str

    # def get_exact_relation(self, relation):
    #     rel = None
    #     for key, synonyms in self.synonym_properties.items():
    #         if relation in synonyms:
    #             rel = key
    #     if rel is None:
    #         for key, synonyms in self.synonym_properties.items():
    #             if len(self.checkSimilarity(relation, synonyms)) > 0:
    #                 rel = key
    #     return rel

    def get_nlp_answers(self, question):
        try:
            entity_name = ''
            entity_relation = ''
            entities = self.ner_pipeline(question, aggregation_strategy="simple")
            for entity in entities:
                entity_name = entity['word']
                print(entity_name)
                # print(f"{entity['word']}: {entity['entity_group']} ({entity['score']:.2f})")

            doc = self.nlp(question)
            entity_relation = self.get_relation(question, entity_name)

            entity_name_fixed = entity_name.strip().strip('"')
            entity_name_fixed = entity_name_fixed.replace("-", "–")
            query, role_predicate = self.create_sparql_query(entity_name_fixed, entity_relation)
            if role_predicate == 'Invalid role':
                return "Sorry, did not find any matches for your query. Could you please rephrase and try again!"
            response = self.sparql_query_interpreter.execute(query)
            print(response)
            if response is None:
                entity_id = self.sparql_query_interpreter.find_entity_id(entity_name_fixed)
                crd = CrowdSoruce()
                response = crd.crowdsource_search(entity_id, role_predicate)
                if response is None:
                    embedded_output = self.emb.get_output_from_embeddings(entity_name_fixed, role_predicate)
                    response = embedded_output
                    if response is not None:
                        pd_ser = pd.Series(response)
                        res_string = ', '.join(f"{index + 1}: {value}" for index, value in enumerate(pd_ser.values))
                        response = res_string.encode('ascii', 'xmlcharrefreplace')
                        response = "The answer suggested by the embeddings is: " + response.decode('ascii')
            return response
        except Exception as e:
            print(e)
            return e

    def create_sparql_query(self, entity, relation):
        try:
            prefixes = """ PREFIX ddis: <http://ddis.ch/atai/>
    
                        PREFIX wd: <http://www.wikidata.org/entity/>
    
                        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    
                        PREFIX schema: <http://schema.org/>"""

            query, role_predicate = self.get_movie_query(entity, relation)
            sparql = prefixes + query
            print(sparql)
            return sparql, role_predicate
        except Exception as e:
            print(e)
            return "Exception occurred in forming the query for your question:", e

    def get_movie_query(self, movie_title, role, imdb_rating=None):

        if role.find(('ddis:rating')) > -1:
            sparql_query = f"""
            SELECT ?rating WHERE
            {{
            ?movie wdt:P31 wd:Q11424.
            ?movie rdfs:label "{movie_title}"@en.
            ?movie {role} ?rating.
            ?role rdfs:label ?role_label.
            }}
            LIMIT 1
            """
        else:
            sparql_query = f"""
                SELECT ?role_label WHERE
                {{
                ?movie wdt:P31 wd:Q11424.
                ?movie rdfs:label "{movie_title}"@en.
                ?movie {role} ?role.
                ?role rdfs:label ?role_label.
                }}
                LIMIT 1
                """

        return sparql_query, role

    synonym_properties = {
        'director': {'direct', 'make', 'create', 'director'},
        'cast member': {'cast member', 'actor', 'actress', 'cast', 'play role', 'star', 'act', 'play'},
        'genre': {'type', 'kind', 'genre'},
        'publication date': {'release', 'date', 'airdate', 'publication', 'launch', 'broadcast', 'release date', 'tell publication date', 'publication date'},
        'executive producer': {'producer', 'produce', 'showrunner', 'executive producer'},
        'screenwriter': {'scriptwriter', 'screenwriter', 'screenplay', 'teleplay', 'writer', 'script', 'scenarist',
                         'write'},
        'based on': {'base on', 'story', 'base', 'based on'},
        'country of origin': {'origin', 'country', 'country of origin'},
        'filming location': {'flocation', 'location'},
        'director of photography': {'cinematographer', 'DOP', 'dop','director of photography'},
        'film editor': {'editor'},
        'production designer': {'designer'},
        'box office': {'box', 'office', 'funding', 'box office'},
        'cost': {'budget', 'cost'},
        'nominated for': {'nomination', 'award', 'finalist', 'shortlist', 'selection', 'nominated for'},
        'costume designer': {'costume', 'designer', 'costume designer'},
        'official website': {'website', 'site'},
        'narrative website': {'nlocation'},
        'production company': {'company', 'production'},
        'review score': {'user', 'review', 'score', 'rate'},
        'award received': {'award', 'honor', 'decoration', 'award received'},
        'place of birth': {'birthplace', 'place of birth'},
    }
