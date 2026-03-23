import pandas as pd
import pickle
import yaml
from sklearn.ensemble import RandomForestClassifier
from pathlib import Path

# TODO: Load parameters from params.yaml
# Hint: look at how preprocess.py reads its parameters

n_estimators = None  # TODO
max_depth = None     # TODO
random_state = None  # TODO

data_path = None     # TODO: path to the processed training data

df = pd.read_csv(data_path)

X_train = df.drop('target', axis=1)
y_train = df['target']

model = RandomForestClassifier(
    n_estimators=n_estimators,
    max_depth=max_depth,
    random_state=random_state
)

model.fit(X_train, y_train)

Path('models').mkdir(exist_ok=True)
with open('models/classifier.pkl', 'wb') as f:
    pickle.dump(model, f)

print(f"Trained model with n_estimators={n_estimators}, max_depth={max_depth}")
