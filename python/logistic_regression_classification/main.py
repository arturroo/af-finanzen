import pandas as pd
from sklearn.linear_model import LogisticRegression
from google.cloud import bigquery

client = bigquery.Client(project_id="af-finanzen")
query = 'SELECT description, Konto FROM banks.revolut_mapping'
df = client.query(query).to_dataframe()  # API request

# Labels
y = df["Konto"]

# Training data
X = df.drop("Konto", axis=1)

# Train model
model = LogisticRegression()
model.fit(X, y)

# Test model
X_test = pd.DataFrame({"tekst": ["GoodLood", "Restauracja Pajda", "AAABBB"]})
y_pred = model.predict(X_test)
print(y_pred)
