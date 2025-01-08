import rdflib
import pandas as pd
from sklearn.metrics import pairwise_distances
from difflib import SequenceMatcher


class Embeddings_Recommendations:

    def __init__(self, graph, ner_pipeline, entity_emb, relation_emb, sparql_query_interpreter, ent2id, id2ent,ent2lbl, lbl2ent):
        self.graph = graph
        self.ner_pipeline = ner_pipeline
        self.entity_emb = entity_emb
        self.relation_emb = relation_emb
        self.sparql_query_interpreter = sparql_query_interpreter
        self.ent2id = ent2id
        self.id2ent = id2ent
        self.ent2lbl = ent2lbl
        self.lbl2ent = lbl2ent

    def get_movie_recommendations(self, question):
        try:
            entity_names = []
            entities = self.ner_pipeline(question, aggregation_strategy="simple")
            for entity in entities:
                entity_names.append(entity['word'].strip())
            print(entity_names)
            if(len(entity_names) > 0):
               return self.get_output_from_embeddings(entity_names)
            else:
                query = '''
    
    PREFIX ddis: <http://ddis.ch/atai/>   
    
    PREFIX wd: <http://www.wikidata.org/entity/>   
    
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>   
    
    PREFIX schema: <http://schema.org/>   
    
      
    
    SELECT ?lbl WHERE {  
    
        ?movie wdt:P31 wd:Q11424 .  
    
        ?movie ddis:rating ?rating .  
    
        ?movie rdfs:label ?lbl .  
    
    }  
    
    ORDER BY DESC(?rating)   
    
    LIMIT 10
    
        '''
                res_list = self.sparql_query_interpreter.execute_with_multiple_responses(query)
                # res_string = ', '.join(res_list)
                res_string = '\n'.join(f"{index+1}: {value}" for index, value in enumerate(res_list))
                result = "Certainly!! I think, you might like these movies: " + "\n" + res_string
                print(result)
                return result
        except Exception as e:
            print(e)
            return "Sorry, not able to provide solution to your query ", e

    def get_output_from_embeddings(self, entity_names):
        try:

            WD = rdflib.Namespace('http://www.wikidata.org/entity/')
            ent2id = self.ent2id
            id2ent = self.id2ent
            ent2lbl = self.ent2lbl
            lbl2ent = self.lbl2ent

            # load the embeddings
            entity_emb = self.entity_emb
            head = 0.0
            matched_entity_list = []
            for entity in entity_names:
                best_match = None
                best_similarity = 0
                try:
                  movie_id = lbl2ent[entity]
                  matched_entity_list.append(entity)
                except Exception as e:
                    for key in lbl2ent.keys():
                        similarity_ratio = SequenceMatcher(None, entity, key).ratio()
                        if similarity_ratio > best_similarity:
                            best_similarity = similarity_ratio
                            best_match = key
                    movie_id = lbl2ent[best_match]
                    matched_entity_list.append(best_match)

                if movie_id is not None:
                    movie_id = movie_id.replace('http://www.wikidata.org/entity/', '')
                    movie_id = ent2id[WD[movie_id]]

                    head = head + entity_emb[movie_id]
            distances = pairwise_distances(head.reshape(1, -1), entity_emb).reshape(-1)

            # and sort them by distance
            most_likely = distances.argsort()

            # we print rank, entity ID, entity label, and distance
            likely_output = pd.DataFrame([
                    (id2ent[idx][len(WD):], ent2lbl[id2ent[idx]], distances[idx], rank+1)
                    for rank, idx in enumerate(most_likely[:15])],
                    columns=('Entity', 'Label', 'Score', 'Rank'))
            pd_ser = pd.Series(likely_output['Label'])
            filtered_series = pd_ser[~pd_ser.isin(matched_entity_list)]
            # res_string = ', '.join(filtered_series.values)
            res_string = '\n'.join(f"{index+1}: {value}" for index, value in enumerate(filtered_series.values))

            result = "Certainly!! I think, you might like these movies: " + "\n" + res_string
            print(result)
            return result
        except Exception as e:
            print(e)
            return "Sorry, not able to provide solution to your query ", e
