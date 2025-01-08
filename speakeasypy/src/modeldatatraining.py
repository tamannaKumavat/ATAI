import os
import spacy
import pandas as pd
from spacy.tokens import DocBin

df = pd.read_csv('../../data/training_data.csv', encoding = "ISO-8859-1")

dataset = []
for index, row in df.iterrows():
    question = row['doc']
    loc = row['loc']
    intent = row['intent']
    strtest = (question, {'entities': [(loc, intent)]})
    dataset.append(strtest)

# the DocBin will store the example documents
nlp = spacy.blank("en")
db = DocBin()
for text, annotations in dataset:
    doc = nlp(text)
    ents = []
    start = 0
    end = 0
    indexes = []
    label = ""
    for vals in annotations['entities'][0]:
        if "," in vals:
            indexes = vals.split(",")
            start = int(indexes[0])
            end = int(indexes[1])
        else:
            label = vals
    span = doc.char_span(start, end, label=label)
    ents.append(span)
    doc.ents = ents
    db.add(doc)
db.to_disk("../../data/movie-question-intent.spacy")


nlp1 = spacy.load(r"..\..\data\output\model-best") #load the best model
doc = nlp1("who is the screenwriter of Star Wars: Episode VI - Return of the Jedi? ") # input sample text
for ent in doc.ents:
    print(f"Named Entity: {ent.text}, Label: {ent.label_}")

doc = nlp1("Who was the actor in The Masked Gang: Cyprus? ") # input sample text
for ent in doc.ents:
    print(f"Named Entity: {ent.text}, Label: {ent.label_}")

doc = nlp1("Who is the director of Batman 1989?") # input sample text
for ent in doc.ents:
    print(f"Named Entity: {ent.text}, Label: {ent.label_}")
