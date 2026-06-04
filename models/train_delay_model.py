import pandas as pd

from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import accuracy_score

import joblib

# ---------------------------------
# LOAD CLEANED DATASET
# ---------------------------------

df = pd.read_csv(
    "data/cleaned_ems_data.csv"
)

print("Dataset Loaded")

# ---------------------------------
# FEATURE SELECTION
# ---------------------------------

X = df[[
    "Downtime_Minutes",
    "Production_Efficiency",
    "Machine_Temperature",
    "Operator_Experience",
    "Inventory_Level"
]]

# TARGET COLUMN

y = df["Delay_Status"]

print("Features Selected")

# ---------------------------------
# TRAIN TEST SPLIT
# ---------------------------------

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.2,

    random_state=42
)

print("Train Test Split Completed")

# ---------------------------------
# MODEL TRAINING
# ---------------------------------

model = RandomForestClassifier(

    n_estimators=100,

    random_state=42
)

model.fit(
    X_train,
    y_train
)

print(X.shape)

print("Model Training Completed")

# ---------------------------------
# MODEL PREDICTIONS
# ---------------------------------

predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions
)

print(
    "Model Accuracy:",
    round(accuracy * 100, 2),
    "%"
)

# ---------------------------------
# SAVE MODEL
# ---------------------------------

joblib.dump(

    model,

    "models/delay_prediction_model.pkl"
)

print("Model Saved Successfully")