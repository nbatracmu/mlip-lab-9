import pandas as pd
import pickle
import json
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from pathlib import Path

with open('models/classifier.pkl', 'rb') as f:
    model = pickle.load(f)

df = pd.read_csv('data/processed/test.csv')

X_test = df.drop('target', axis=1)
y_test = df['target']

y_pred = model.predict(X_test)

# TODO: Calculate metrics using the imported sklearn functions
accuracy = None   # TODO
precision = None  # TODO
recall = None     # TODO
f1 = None         # TODO

# TODO: Populate the metrics dictionary
metrics = {}

Path('metrics').mkdir(exist_ok=True)
with open('metrics/scores.json', 'w') as f:
    json.dump(metrics, f, indent=2)

print(f"Evaluation metrics: {metrics}")
