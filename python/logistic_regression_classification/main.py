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
query = ("""SELECT
  description
  , CASE Konto
      WHEN "PK Leben" THEN Konto
      ELSE "Andere"
    END AS Konto
FROM banks.revolut_mapping_internal
""")
df = client.query(query).to_dataframe()  # API request
# print(f"df: {df}")

# Change text to numbers
le = LabelEncoder()
for col in df.columns:
    df[f"le_{col}"] = le.fit_transform(df[col])
    print('Features', f"le_{col}", df[f"le_{col}"].to_numpy().shape)
    print('Features', f"le_{col}", df[f"le_{col}"].to_numpy())

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
y_train = y_train.to_numpy().reshape(-1, 1)
y_test = y_test.to_numpy().reshape(-1, 1)
print('X Train', X_train.shape)
print('Y Train', y_train.shape)
print('X Test', X_test.shape)
print('Y Test', y_test.shape)
#
# print(f"X_test: {X_test.to_string()}")
# print(f"y_test: {y_test.to_string()}")
#
# Train model
model = LogisticRegression()
model.fit(X_train, y_train)
#
# Testing the classifier
y_pred = model.predict(X_test)
print('Predicted',y_pred)
print('Actual data',y_test)
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

print("Precision:",metrics.precision_score(y_test, y_pred))
print("Recall:",metrics.recall_score(y_test, y_pred))



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
