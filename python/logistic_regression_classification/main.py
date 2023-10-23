__author__ = "Artur Fejklowicz"

# Sources:
# - https://medium.com/@ashins1997/text-classification-dfe370bf7044
# - https://www.kaggle.com/code/shahkan/text-classification-using-logistic-regression

import pandas as pd
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn import metrics
from google.cloud import bigquery

client = bigquery.Client(project="af-finanzen")
query = 'SELECT description, Konto FROM banks.revolut_mapping_internal'
df = client.query(query).to_dataframe()  # API request
# print(f"df: {df}")

# Change text to numbers
df_encoded = df
le = LabelEncoder()
for col in df_encoded.columns:
    df_encoded[col] = le.fit_transform(df_encoded[col])

# Labels
labels = df_encoded["Konto"]
# Training data
features = df_encoded.drop("Konto", axis=1)

# print(f"X: {X.to_string()}")

# Split the data for train and test
# Splitting train : test to 80 : 20 ratio
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2)

# Train model
model = LogisticRegression()
model.fit(X_train, y_train)

# Testing the classifier
y_predicted = model.predict(X_test)
print('Predicted',y_predicted)
print('Actual data',y_test)
y_predicted_probability = model.predict_proba(X_test)
print('Predicted probability',y_predicted_probability)

# A confusion matrix is a table that is used to evaluate the performance of a classification model. Diagonal values represent accurate predictions, while non-diagonal elements are inaccurate predictions.
cnf_matrix = metrics.confusion_matrix(y_test, y_predicted)
print(f"Confusion matrix\n",cnf_matrix)

print("Accuracy:",metrics.accuracy_score(y_test, y_predicted))
print("Precision:",metrics.precision_score(y_test, y_predicted, average="micro"))
print("Recall:",metrics.recall_score(y_test, y_predicted, average="micro"))

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
