import pandas as pd
import nltk
from nltk.corpus import stopwords
import urllib.request
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer


class FeatureEngineering:
    def __init__(self, vectorizer: str = "TFiDF", raw_data: pd.DataFrame = None):
        self.vectorizer = vectorizer
        self.raw_data = raw_data
        self.label_encoder = {'Others':0, 'PK Artur': 1, 'PK Leben': 2, 'PK Reisen': 3, 'SK Ferien': 4}
    
    @staticmethod
    def get_stop_words():
        stops_eng = set(stopwords.words('english'))
        stops_ger = set(stopwords.words('german'))
        stops_ita = set(stopwords.words('italian'))
        stops_spa = set(stopwords.words('spanish'))
        stops_fra = set(stopwords.words('french'))
        link = "https://raw.githubusercontent.com/bieli/stopwords/master/polish.stopwords.txt"
        lines=[]
        responce = urllib.request.urlopen(link)
        stops_pol = responce.read().decode().split(f"\n")

        return list(stops_eng.union(stops_ger).union(stops_ita).union(stops_spa).union(stops_fra).union(stops_pol))

    def bow_vectorizer(self):
        count_vect = CountVectorizer()
