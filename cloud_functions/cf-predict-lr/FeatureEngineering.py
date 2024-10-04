import pandas as pd
#from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from typing import Union


class FeatureEngineering:
    def __init__(self, raw_data: pd.DataFrame = None, vectorizer: Union[TfidfVectorizer, CountVectorizer] = None, ):
        self.raw_data = raw_data
        self.vectorizer = vectorizer
        if isinstance(self.vectorizer, TfidfVectorizer):
            self.vectorizer_type = 'tfidf'
        elif isinstance(self.vectorizer, CountVectorizer):
            self.vectorizer_type = 'bow'
        else:
            self.vectorizer_type = 'unknown'

        self.label_encoder = {'Others':0, 'PK Artur': 1, 'PK Leben': 2, 'PK Reisen': 3, 'SK Ferien': 4}
    

    def get_features(self) -> pd.Series:
        self.X_pred = self.vectorizer.transform(self.raw_data['description'])
        return self.X_pred