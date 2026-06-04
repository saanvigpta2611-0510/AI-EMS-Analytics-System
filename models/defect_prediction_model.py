import pandas as pd

from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import accuracy_score

import joblib


# LOAD DATASET

df = pd.read_csv(
    "data/cleaned_ems_data.csv"
)

# ---------------------------------
# CONVERT MATERIAL QUALITY
# ---------------------------------

df["Material_Quality"] = df[
    "Material_Quality"
].map({

    "Low": 1,

    "Medium": 2,

    "High": 3
})


# FEATURES

X = df[[

    "Machine_Temperature",

    "Downtime_Minutes",

    "Production_Efficiency",

    "Operator_Experience",

    "Material_Quality"

]]


# TARGET

y = df["Defect_Status"]


# TRAIN TEST SPLIT

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.2,

    random_state=42
)


# MODEL

model = RandomForestClassifier()

model.fit(
    X_train,
    y_train
)


# PREDICTIONS

predictions = model.predict(X_test)


# ACCURACY

accuracy = accuracy_score(
    y_test,
    predictions
)

print(
    "Model Accuracy:",
    accuracy
)


# SAVE MODEL

joblib.dump(
    model,
    "models/defect_model.pkl"
)

print(
    "Defect prediction model saved."
)