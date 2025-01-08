import random


class SparqlInterpreter:

    def __init__(self, graph):
        self.graph = graph

    def execute(self, query):
        try:
            # List of strings
            string_list = ["I think it is ANSWER.",
                           "I think the answer to your question is ANSWER",
                           "The answer is ANSWER"]

            # Select a random string from the list
            random_string = random.choice(string_list)
            response = [str(s) for s, in self.graph.query(query)]
            res = None
            if len(response) > 0:
                res = random_string.replace('ANSWER', response[0])
                res = res.encode('ascii', 'xmlcharrefreplace')
                res = res.decode('ascii')
            return res
        except Exception as e:
            print(e)
            return e

    def execute_with_multiple_responses(self, query):
        try:
            response = [str(s) for s, in self.graph.query(query)]
            return response
        except Exception as e:
            print(e)
            return e

    def find_entity_id(self, entity):

        query_template = f'''
          prefix wdt: <http://www.wikidata.org/prop/direct/>
          prefix wd: <http://www.wikidata.org/entity/>

          SELECT ?ent WHERE {{
              ?ent rdfs:label "{entity}"@en .
          }}'''

        # check if entity is empty
        if entity:
            entity_id = self.graph.query(query_template)
            output = [str(s) for s, in entity_id]
            # check if output is empty
            if output:
                return output[0].replace('http://www.wikidata.org/entity/', '')
            else:
                return None
        else:
            return None
