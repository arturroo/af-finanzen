__author__ = "Artur Fejklowicz"

# Sources:
# - https://medium.com/@ashins1997/text-classification-dfe370bf7044
# - https://www.kaggle.com/code/shahkan/text-classification-using-logistic-regression

import pandas as pd
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from google.cloud import bigquery

client = bigquery.Client(project_id="af-finanzen")
query = 'SELECT description, Konto FROM banks.revolut_mapping'
df = client.query(query).to_dataframe()  # API request

# Labels
y = df["Konto"]

# Training data
X = df.drop("Konto", axis=1)

# Change text to numbers
le = LabelEncoder()
for col in X.columns:
    X[col] = le.fit_transform(X[col])


# Train model
model = LogisticRegression()
#model.fit(X, y)

scores = cross_val_score(model, X, y, cv=10)
print(scores.mean())

results = cross_validate(model, X, y, scoring="accuracy", cv=10)
print(results["test_score"].mean())
model = results["best_estimator_"]
print(results["best_estimator_"])

# Test model
X_test = pd.DataFrame({"tekst": ["GoodLood", "Restauracja Pajda", "AAABBB"]})
y_pred = model.predict(X_test)
print(y_pred)
