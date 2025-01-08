import csv
import numpy as np
import os
import rdflib
import pandas as pd
from sklearn.metrics import pairwise_distances


class Embeddings_Output:

    def __init__(self, graph, entity_emb, relation_emb):
        self.graph = graph
        self.entity_emb = entity_emb
        self.relation_emb = relation_emb

       

    def get_output_from_embeddings(self, entity, role_predicate):
        try:
            role_predicate = role_predicate.replace("wdt:", "")

            WD = rdflib.Namespace('http://www.wikidata.org/entity/')
            WDT = rdflib.Namespace('http://www.wikidata.org/prop/direct/')
            DDIS = rdflib.Namespace('http://ddis.ch/atai/')
            RDFS = rdflib.namespace.RDFS
            SCHEMA = rdflib.Namespace('http://schema.org/')

            # load the embeddings
            entity_emb = self.entity_emb
            relation_emb = self.relation_emb
            # load the dictionaries
            with open('./../data/entity_ids.del', 'r') as ifile:
                ent2id = {rdflib.term.URIRef(ent): int(idx) for idx, ent in csv.reader(ifile, delimiter='\t')}
                id2ent = {v: k for k, v in ent2id.items()}
            with open('./../data/relation_ids.del', 'r') as ifile:
                rel2id = {rdflib.term.URIRef(rel): int(idx) for idx, rel in csv.reader(ifile, delimiter='\t')}
                id2rel = {v: k for k, v in rel2id.items()}
            ent2lbl = {ent: str(lbl) for ent, lbl in self.graph.subject_objects(RDFS.label)}
            lbl2ent = {lbl: ent for ent, lbl in ent2lbl.items()}
            main_entity = lbl2ent[entity].replace('http://www.wikidata.org/entity/', '')

            head = entity_emb[ent2id[WD[main_entity]]]

            pred = relation_emb[rel2id[WDT[role_predicate]]]
            # add vectors according to TransE scoring function.
            lhs = head + pred
            # compute distance to *any* entity
            dist = pairwise_distances(lhs.reshape(1, -1), entity_emb).reshape(-1)
            # find most plausible entities
            most_likely = dist.argsort()
            # compute ranks of entities
            ranks = dist.argsort().argsort()

            likely_output = pd.DataFrame([
                (id2ent[idx][len(WD):], ent2lbl[id2ent[idx]], dist[idx], rank + 1)
                for rank, idx in enumerate(most_likely[:3])],
                columns=('Entity', 'Label', 'Score', 'Rank'))
            response = ""
            print(likely_output['Label'])

            return likely_output['Label']
        except Exception as e:
            print(e)
            return "Sorry, not able to provide solution to your query ", e
