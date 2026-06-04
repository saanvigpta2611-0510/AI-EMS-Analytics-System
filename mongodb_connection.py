from pymongo import MongoClient
import pandas as pd

# ---------------------------------
# CONNECT TO MONGODB
# ---------------------------------

client = MongoClient(
    "mongodb://localhost:27017/"
)

print("MongoDB Connected Successfully")

# ---------------------------------
# CREATE DATABASE
# ---------------------------------

db = client["EMS_Production_DB"]

print("Database Created")

# ---------------------------------
# CREATE COLLECTION
# ---------------------------------

collection = db["production_data"]

print("Collection Created")

# ---------------------------------
# LOAD CLEANED DATASET
# ---------------------------------

df = pd.read_csv(
    "data/cleaned_ems_data.csv"
)

print("Dataset Loaded")

# ---------------------------------
# CONVERT DATAFRAME TO DICTIONARY
# ---------------------------------

data = df.to_dict(
    orient="records"
)

print("Data Converted")

# ---------------------------------
# INSERT DATA INTO MONGODB
# ---------------------------------

collection.insert_many(data)

print("Dataset Inserted Into MongoDB")