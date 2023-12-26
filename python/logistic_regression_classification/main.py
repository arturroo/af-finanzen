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


client = bigquery.Client(project="af-finanzen")
query = ("""SELECT
  description
  , Konto
  --, CASE Konto
  --    WHEN "PK Leben" THEN Konto
  --    ELSE "Andere"
  --  END AS Konto
FROM banks.revolut_mapping_internal
""")
df = client.query(query).to_dataframe()  # API request
print(f"df.head()\n {df.head(25)}")
print(df.groupby("Konto").Konto.count())
df.groupby("Konto").Konto.count().plot.bar(ylim=0)
#plt.show()

# stemmer_pl = nltk.stem.snowball.SnowballStemmer("polish")
#vectorizer = TfidfVectorizer(min_df=1, stop_words="english", sublinear_tf=True, norm='l2', ngram_range=(1, 5))
vectorizer = TfidfVectorizer(
    min_df=1,
    stop_words=["i", "o", "a", "z", "-", "na", "at", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "w"],
    sublinear_tf=True, norm='l2', ngram_range=(1, 4))
final_features = vectorizer.fit_transform(df['description']).toarray()
print(f"final_features.shape: {final_features.shape}")

X = df['description']
Y = df['Konto']
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.25)

pipeline = Pipeline([('vect', vectorizer),
                     ('chi',  SelectKBest(chi2, k="all")),
                     ('clf', LogisticRegression(multi_class='ovr', solver='liblinear', random_state=0))])

model = pipeline.fit(X_train, y_train)

ytest = np.array(y_test)

# confusion matrix and classification report(precision, recall, F1-score)
print(classification_report(ytest, model.predict(X_test)))
print(confusion_matrix(ytest, model.predict(X_test)))

print(f"shape y_test {y_test.shape} X_test {X_test.shape}")
#for idx, y in y_test.items():
##    #print(f"model.predict(X_test)\n{model.predict(X_test)}")
#    pred = model.predict([X_test[idx]])
#    print(f"{1 if y == pred else 0} y {y}    pred: {pred}    x {X_test[idx]} ")
#    #print(f"idx {idx} y {y}")

exit()


# Change text to numbers
le = LabelEncoder()
for col in df.columns:
    df[f"le_{col}"] = le.fit_transform(df[col])
    #print('Features', f"le_{col}", df[f"le_{col}"].to_numpy().shape)
    #print('Features', f"le_{col}", df[f"le_{col}"].to_numpy())

#print(df.sort_values("le_description").to_string())
print(df.sort_values("le_description"))
# (df.groupby('Konto').text.count().plot.bar(ylim=0))
# plt.show()

# Labels
y = df["le_Konto"]
# Data
# X = df.drop("Konto", axis=1)
X = df["le_description"]

# print(f"X: {X.to_string()}")
# print(f"y: {y.to_string()}")
# print(df.iloc[357])
#
#
# Split the data for train and test
# Splitting train : test to 80 : 20 ratio
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
X_train = X_train.to_numpy().reshape(-1, 1)
X_test = X_test.to_numpy().reshape(-1, 1)
#y_train = y_train.to_numpy().reshape(-1, 1)
#y_test = y_test.to_numpy().reshape(-1, 1)
y_train = y_train.to_numpy()
y_test = y_test.to_numpy()
print('X Train', X_train.shape)
print('X Train', X_train)
print('Y Train', y_train.shape)
print('Y Train', y_train)
print('X Test', X_test.shape)
print('Y Test', y_test.shape)
#
# print(f"X_test: {X_test.to_string()}")
# print(f"y_test: {y_test.to_string()}")
#
# Train model
model = LogisticRegression(multi_class='ovr', solver='liblinear')
model.fit(X_train, y_train)
#
# Testing the classifier
y_pred = model.predict(X_test)
#print('Predicted',y_pred)
#print('Actual data',y_test)
# y_predicted_probability = model.predict_proba(X_test)
# print('Predicted probability',y_predicted_probability)
#
# # A confusion matrix is a table that is used to evaluate the performance of a classification model. Diagonal values represent accurate predictions, while non-diagonal elements are inaccurate predictions.
cnf_matrix = metrics.confusion_matrix(y_test, y_pred)
print(f"Confusion matrix\n",cnf_matrix)
#
print("Accuracy:",metrics.accuracy_score(y_test, y_pred))
#print("Precision:",metrics.precision_score(y_test, y_pred, average="micro"))
#print("Recall:",metrics.recall_score(y_test, y_pred, average="micro"))

#print("Precision:",metrics.precision_score(y_test, y_pred))
#print("Recall:",metrics.recall_score(y_test, y_pred))

#y_pred = model.predict(np.array(["Fajna restauracja", "Arbon Tankstelle"]).reshape(-1, 1))
y_pred = model.predict(np.array([400, 500]).reshape(-1, 1))
print('Predicted',y_pred)

print(metrics.classification_report(y_test, model.predict(X_test)))








#
# scores = cross_val_score(model, X, y, cv=10)
# print(scores.mean())
#
# results = cross_validate(model, X, y, scoring="accuracy", cv=10)
# print(results["test_score"].mean())
# model = results["best_estimator_"]
# print(results["best_estimator_"])
#
# # Test model
# X_test = pd.DataFrame({"tekst": ["GoodLood", "Restauracja Pajda", "AAABBB"]})
# y_pred = model.predict(X_test)
# print(y_pred)
