import pandas as pd
import numpy as np

# LOAD RAW DATASET

df = pd.read_csv("data/raw_ems_data.csv")

print("\nDATASET LOADED SUCCESSFULLY\n")

# -----------------------------
# CHECK NULL VALUES
# -----------------------------

print("NULL VALUES:\n")

print(df.isnull().sum())

# -----------------------------
# HANDLE NULL VALUES
# -----------------------------

# MACHINE TEMPERATURE
df["Machine_Temperature"].fillna(
    df["Machine_Temperature"].mean(),
    inplace=True
)

# OPERATOR EXPERIENCE
df["Operator_Experience"].fillna(
    df["Operator_Experience"].median(),
    inplace=True
)

# MAINTENANCE STATUS
df["Maintenance_Status"].fillna(
    "Pending",
    inplace=True
)

# INVENTORY LEVEL
df["Inventory_Level"].fillna(
    df["Inventory_Level"].median(),
    inplace=True
)

print("\nNULL VALUES CLEANED\n")

# -----------------------------
# HANDLE OUTLIERS
# -----------------------------

# REMOVE EXTREME MACHINE TEMPERATURES

df = df[
    df["Machine_Temperature"] < 150
]

print("OUTLIERS REMOVED\n")

# -----------------------------
# FEATURE ENGINEERING
# -----------------------------

# DELAY STATUS

df["Delay_Status"] = np.where(
    (df["Downtime_Minutes"] > 50) &
    (df["Production_Efficiency"] < 75),
    1,
    0
)

# DEFECT STATUS

df["Defect_Status"] = np.where(
    (df["Machine_Temperature"] > 95) &
    (df["Material_Quality"] == "Low"),
    1,
    0
)

# FAILURE RISK

df["Failure_Risk"] = np.where(
    (df["Downtime_Minutes"] > 70) &
    (df["Maintenance_Status"] == "Pending"),
    1,
    0
)

# PREDICTED OUTPUT

df["Predicted_Output"] = (
    df["Actual_Output"]
    + np.random.randint(-20, 20, len(df))
)

print("FEATURE ENGINEERING COMPLETED\n")

# -----------------------------
# SAVE CLEANED DATASET
# -----------------------------

df.to_csv(
    "data/cleaned_ems_data.csv",
    index=False
)

print("CLEANED DATASET SAVED SUCCESSFULLY")