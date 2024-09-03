__author__ = "Artur Fejklowicz"

import numpy as np
# Sources:
# - https://medium.com/@ashins1997/text-classification-dfe370bf7044
# - https://www.kaggle.com/code/shahkan/text-classification-using-logistic-regression
# - https://www.kaggle.com/code/satishgunjal/multiclass-logistic-regression-using-sklearn
# - https://medium.com/@cmukesh8688/tf-idf-vectorizer-scikit-learn-dbc0244a911a
# - https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn import metrics
from google.cloud import bigquery
import matplotlib.pyplot as plt
import nltk.stem.snowball
from sklearn.metrics import ConfusionMatrixDisplay
import nltk
from nltk.corpus import stopwords
#nltk.download('stopwords')

def load_lines_from_file(filename):
    """Loads newline-delimited strings from a file into a list."""
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines]  # Remove trailing newlines
            return lines
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None


client = bigquery.Client(project="af-finanzen")
query = ("""SELECT
  description
  , Konto
FROM banks.revolut_mapping_internal
""")
df = client.query(query).to_dataframe()  # API request
print(f"df.head()\n {df.head(25)}")
print(df.groupby("Konto").Konto.count())
df.groupby("Konto").Konto.count().plot.bar(ylim=0)
plt.show()

# write a cunftion to change list into pandas series
def change_list_into_pandas_series(list_to_change):
    """
    This function takes a list and returns a pandas series.

    Args:
        list_to_change: A list to be converted into a pandas series.

    Returns:
        A pandas series.
    """
    return pd.Series(list_to_change)

# Create a list of strings
list_of_strings = ["apple", "banana", "cherry", "durian"]

# Convert the list into a pandas series
series_of_strings = change_list_into_pandas_series(list_of_strings)

# Print the pandas series
print(series_of_strings)


# stemmer_pl = nltk.stem.snowball.SnowballStemmer("polish")

# Bag of Words vectorization method that takes under consideration ratio of word frequency in single element to whole document

# ngram_range from bard.google.com
# The `ngram_range` parameter in `TfidfVectorizer` in scikit-learn determines the range of n-grams to be extracted from the text documents. An n-gram is a sequence of n consecutive words in a text document. For example, a unigram is a single word, a bigram is a sequence of two words, and a trigram is a sequence of three words.
# By specifying an `ngram_range`, you can control which n-grams are included in the feature set. For instance, an `ngram_range` of (1, 1) indicates that only unigrams will be extracted, while an `ngram_range` of (1, 2) allows unigrams and bigrams. The choice of `ngram_range` depends on the specific task at hand.
# Here's a breakdown of how the `ngram_range` parameter affects text representation:
# * **Unigrams:** Unigrams represent individual words and capture the frequency of each word in the text. They are useful for tasks like document classification, where the overall topic or sentiment of the document is important.
# * **Bigrams:** Bigrams capture the relationships between pairs of words and can be more indicative of the meaning or context of a phrase. This can be helpful for tasks like sentiment analysis, where the combination of words can convey a stronger emotional tone than individual words alone.
# * **Trigrams:** Trigrams analyze the context of triplets of words, providing even more granularity in capturing the meaning and nuances of language. This can be useful for tasks that require a deeper understanding of the linguistic structure of a text, such as machine translation or information extraction.
# In summary, the `ngram_range` parameter in `TfidfVectorizer` allows you to tailor the text representation to the specific task at hand. By choosing the appropriate range of n-grams, you can capture the relevant information from the text while reducing dimensionality and improving the performance of downstream learning tasks.

#vectorizer = TfidfVectorizer(min_df=1, stop_words="english", sublinear_tf=True, norm='l2', ngram_range=(1, 5))

stops_eng = set(stopwords.words('english'))
stops_ger = set(stopwords.words('german'))
stops_ita = set(stopwords.words('italian'))
stops_spa = set(stopwords.words('spanish'))
stops_fra = set(stopwords.words('french'))
stops_pol = set(load_lines_from_file("polish.txt"))
stops = stops_eng.union(stops_ger).union(stops_ita).union(stops_spa).union(stops_fra)
if stops_pol:
    stops = stops.union(stops_pol)
stops = list(stops)
print(f"stops:\n{stops}")
print(f"stops type:\n{type(stops)}")

vectorizer = TfidfVectorizer(
    min_df=0.0001,
    # stop_words=["i", "o", "a", "z", "-", "w", "na", "at", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
    #             "(2", "(2)", "(3", "(3)", "(4", "(4)", "(5", "(5)", "(6", "(6)", "(7", "(7)", "(8", "(8)", "(9", "(9)", "(0"],
    stop_words=stops,
    max_features=5000,
    sublinear_tf=True, norm='l2', ngram_range=(1, 1))
final_features = vectorizer.fit_transform(df['description']).toarray()
print(f"final_features.shape:\n{final_features.shape}")
#np.set_printoptions(threshold=np.inf)
#print(f"final_featurese:\n{final_features}")

X = df['description']
Y = df['Konto']
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.25)

pipeline = Pipeline([('vect', vectorizer),
                     ('chi',  SelectKBest(chi2, k="all")),
                     ('clf',  LogisticRegression(multi_class='ovr', solver='liblinear', random_state=0))])

model = pipeline.fit(X_train, y_train)

ytest = np.array(y_test)

# confusion matrix and classification report(precision, recall, F1-score)
classification_report = classification_report(ytest, model.predict(X_test))
confusion_matrix_training = confusion_matrix(np.array(y_train), model.predict(X_train))
confusion_matrix_testing = confusion_matrix(ytest, model.predict(X_test))

print(classification_report)

print("Confusion Matrix: on training data")
print(confusion_matrix_training)
disp = ConfusionMatrixDisplay(confusion_matrix=confusion_matrix_training)
disp.plot()
plt.show()

print("Confusion Matrix: on testing data")
print(confusion_matrix_testing)
disp = ConfusionMatrixDisplay(confusion_matrix=confusion_matrix_testing)
disp.plot()
plt.show()



print(f"shape y_test {y_test.shape} X_test {X_test.shape}")
#for idx, y in y_test.items():
##    #print(f"model.predict(X_test)\n{model.predict(X_test)}")
#    pred = model.predict([X_test[idx]])
#    print(f"{1 if y == pred else 0} y {y}    pred: {pred}    x {X_test[idx]} ")
#    #print(f"idx {idx} y {y}")
