import pandas as pd


class CrowdSoruce:

    def crowdsource_search(self, ent, rel):
        '''
        crowdsource searching
        If an answer is available, return the Input3ID as the answer and count the number of 'CORRECT' and 'INCORRECT' labels for all matching results.
        '''
        data = pd.read_csv('./../data/clean_crowd_data.csv')
        res = data[(data['Input1ID']== f"wd:{ent}" ) & (data['Input2ID']==f"{rel}")]
        ans = res['Input3ID'].str.strip('wd:').unique()  # Extract Input3IDs as the answer
        # Initialize counters for 'CORRECT' and 'INCORRECT'
        correct_count = (res['AnswerLabel'] == 'CORRECT').sum()
        incorrect_count = (res['AnswerLabel'] == 'INCORRECT').sum()

        id = res['HITTypeId'].unique()[0]

        data = data[data['HITTypeId'] == id]

        data = data.groupby(['HITId', 'AnswerLabel']).size().reset_index(name='count' ) 
        data['count'].astype(int)
        data = data.pivot(index='HITId', columns='AnswerLabel', values='count' ) 
        data.fillna(0,inplace=True)
        data['P_i'] = (data['CORRECT']**2 + data['INCORRECT']**2 - 3)/6 
        data['P_i' ].astype(float)
        P_c = data['CORRECT'].sum()/(3*len (data))
        P_i = data['INCORRECT'].sum()/(3*len(data))
        P = data['P_i'].sum()/len(data)
        P_e = P_c**2 + P_i**2
        kappa = round(((P - P_e)/(1 - P_e)),3)

        return f"The answers are '{ans}'. [Crowd, the inter-rate is {kappa}. The answer distribution for this specific task was '{correct_count}' support votes, '{incorrect_count}' reject votes]"
    

