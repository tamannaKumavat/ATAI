import csv
import json
import sys
from datetime import datetime

import rdflib
import spacy

from speakeasypy.src.speakeasy import Speakeasy
from speakeasypy.src.embeddings_output import Embeddings_Output
from speakeasypy.src.embeddings_recommendations import Embeddings_Recommendations
from speakeasypy.src.chatroom import Chatroom
from speakeasypy.src.sparqlinterpreter import SparqlInterpreter
from speakeasypy.src.multimedia_query_processor import MultimediaQueryProcessor
from speakeasypy.src.closedquestionprocessor import ClosedQuestionProcessor
from typing import List
import time
from transformers import pipeline, set_seed
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from IPython.display import display, Image

DEFAULT_HOST_URL = 'https://speakeasy.ifi.uzh.ch'
listen_freq = 2


class Agent:
    def __init__(self, username, password):
        self.username = username
        # Initialize the Speakeasy Python framework and login.
        self.speakeasy = Speakeasy(host=DEFAULT_HOST_URL, username=username, password=password)
        self.speakeasy.login()  # This framework will help you log out automatically when the program terminates.

    def listen(self):
        while True:
            # only check active chatrooms (i.e., remaining_time > 0) if active=True.
            rooms: List[Chatroom] = self.speakeasy.get_rooms(active=True)
            for room in rooms:
                if not room.initiated:
                    # send a welcome message if room is not initiated
                    room.post_messages(f'Hello! This is a welcome message from {room.my_alias}.')
                    room.initiated = True
                # Retrieve messages from this chat room.
                # If only_partner=True, it filters out messages sent by the current bot.
                # If only_new=True, it filters out messages that have already been marked as processed.
                for message in room.get_messages(only_partner=True, only_new=True):
                    print(
                        f"\t- Chatroom {room.room_id} "
                        f"- new message #{message.ordinal}: '{message.message}' "
                        f"- {self.get_time()}")

                    # Implement your agent here #

                    # Send a message to the corresponding chat room using the post_messages method of the room object.
                    room.post_messages(fr"Received your message: '{message.message}' ")

                    if message.message.upper().find(('SELECT')) > -1:
                        response = si.execute(message.message)
                        room.post_messages(f"'{response}'")
                    elif message.message.upper().find(('RECOMMEND')) > -1 or message.message.upper().find(('SUGGEST')) > -1\
                            or message.message.upper().find(('GIVE')) > -1 or message.message.upper().find(('PROVIDE')) > -1:
                        room.post_messages(
                            "Thank you for your input! I'm processing... your request.Please wait, this will only take a moment.")

                        response = rec.get_movie_recommendations(message.message)
                        room.post_messages(f"'{response}'")
                    elif message.message.upper().find(('IMAGE')) > -1 or message.message.upper().find(('LOOK LIKE')) > -1 or message.message.upper().find(('PICTURE')) > -1 or message.message.upper().find(('POSTER')) > -1\
                            or message.message.upper().find(('PHOTO')) > -1 or message.message.upper().find(('LOOK')) > -1:
                        response = mqp.get_image(message.message)
                        room.post_messages(f"'{response}'")
                    else:
                        if len(ner_pipeline(message.message, aggregation_strategy="simple")) > 0:
                            response = cqp.get_nlp_answers(message.message)

                        else:
                            response = ("Sorry, did not find any matches for your query. Could you please rephrase and "
                                        "try again!")
                        room.post_messages(f"'{response}'")
                    # Mark the message as processed, so it will be filtered out when retrieving new messages.
                    room.mark_as_processed(message)

                # Retrieve reactions from this chat room.
                # If only_new=True, it filters out reactions that have already been marked as processed.
                for reaction in room.get_reactions(only_new=True):
                    print(
                        f"\t- Chatroom {room.room_id} "
                        f"- new reaction #{reaction.message_ordinal}: '{reaction.type}' "
                        f"- {self.get_time()}")

                    # Implement your agent here #

                    room.post_messages(f"Received your reaction: '{reaction.type}' ")
                    room.mark_as_processed(reaction)

            time.sleep(listen_freq)

    @staticmethod
    def get_time():
        return time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime())


if __name__ == '__main__':
    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Execution started =", current_time)

    graph = rdflib.Graph()
    graph.parse('../data/14_graph.nt', format='turtle')

    RDFS = rdflib.namespace.RDFS

    si = SparqlInterpreter(graph)
    set_seed(111)
    ner_pipeline = pipeline('ner', model='planeB/roberta_movie_w_title')
    nlp = spacy.load(r"../data/output/model-best")
    entity_emb = np.load('../data/entity_embeds.npy')
    relation_emb = np.load('../data/relation_embeds.npy')
    emb = Embeddings_Output(graph, entity_emb, relation_emb)
    spacy_nlp = spacy.load("en_core_web_sm")
    cqp = ClosedQuestionProcessor(graph, ner_pipeline, spacy_nlp, si, emb)

    RDFS = rdflib.namespace.RDFS
    with open('../data/entity_ids.del', 'r') as ifile:
        ent2id = {rdflib.term.URIRef(ent): int(idx) for idx, ent in csv.reader(ifile, delimiter='\t')}
        id2ent = {v: k for k, v in ent2id.items()}
    ent2lbl = {ent: str(lbl) for ent, lbl in graph.subject_objects(RDFS.label)}
    lbl2ent = {lbl: ent for ent, lbl in ent2lbl.items()}

    rec = Embeddings_Recommendations(graph, ner_pipeline, entity_emb, relation_emb, si, ent2id, id2ent,ent2lbl, lbl2ent)

    with open('../data/images.json', 'r') as file:
        json_data = file.read()
    data_list = []
    try:
        data_list = json.loads(json_data)
    except json.decoder.JSONDecodeError as e:
        print("JSON decoding error:", e)

    mqp = MultimediaQueryProcessor(graph, ner_pipeline, lbl2ent, data_list)
    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Execution end =", current_time)

    # demo_bot = Agent("tamannasurendar.kumavat", "AskLQpVQH75HJQ")
    demo_bot = Agent("burn-molto-tartar_bot", "Jqmb0Vq5vQ2N8Q")
    demo_bot.listen()
