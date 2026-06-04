import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# LOAD CLEANED DATASET

df = pd.read_csv("data/cleaned_ems_data.csv")

print("\nDATASET LOADED\n")

# ---------------------------------
# BASIC DATA UNDERSTANDING
# ---------------------------------

print("FIRST 5 ROWS:\n")

print(df.head())

print("\nDATASET SHAPE:\n")

print(df.shape)

print("\nCOLUMN NAMES:\n")

print(df.columns)

# ---------------------------------
# KPI CALCULATIONS
# ---------------------------------

total_production = df["Actual_Output"].sum()

avg_efficiency = df["Production_Efficiency"].mean()

total_defects = df["Defect_Count"].sum()

avg_downtime = df["Downtime_Minutes"].mean()

print("\n----- KPI VALUES -----\n")

print("TOTAL PRODUCTION:", total_production)

print("AVERAGE EFFICIENCY:", round(avg_efficiency,2))

print("TOTAL DEFECTS:", total_defects)

print("AVERAGE DOWNTIME:", round(avg_downtime,2))

# ---------------------------------
# SHIFT ANALYSIS
# ---------------------------------

shift_analysis = df.groupby(
    "Shift_Type"
)["Production_Efficiency"].mean()

print("\nSHIFT ANALYSIS:\n")

print(shift_analysis)

# ---------------------------------
# MACHINE ANALYSIS
# ---------------------------------

machine_analysis = df.groupby(
    "Machine_ID"
)["Downtime_Minutes"].mean()

print("\nMACHINE DOWNTIME ANALYSIS:\n")

print(machine_analysis)

# ---------------------------------
# DEFECT ANALYSIS
# ---------------------------------

defect_analysis = df.groupby(
    "Material_Quality"
)["Defect_Count"].mean()

print("\nDEFECT ANALYSIS:\n")

print(defect_analysis)

# ---------------------------------
# VISUALIZATION 1
# SHIFT VS EFFICIENCY
# ---------------------------------

plt.figure(figsize=(6,4))

sns.barplot(
    x=shift_analysis.index,
    y=shift_analysis.values
)

plt.title("Shift vs Production Efficiency")

plt.xlabel("Shift")

plt.ylabel("Average Efficiency")

plt.show()

# ---------------------------------
# VISUALIZATION 2
# MACHINE DOWNTIME
# ---------------------------------

plt.figure(figsize=(6,4))

sns.barplot(
    x=machine_analysis.index,
    y=machine_analysis.values
)

plt.title("Machine Downtime Analysis")

plt.xlabel("Machine")

plt.ylabel("Average Downtime")

plt.show()

# ---------------------------------
# VISUALIZATION 3
# MATERIAL QUALITY VS DEFECTS
# ---------------------------------

plt.figure(figsize=(6,4))

sns.barplot(
    x=defect_analysis.index,
    y=defect_analysis.values
)

plt.title("Material Quality vs Defects")

plt.xlabel("Material Quality")

plt.ylabel("Average Defects")

plt.show()

print("\nEDA COMPLETED SUCCESSFULLY")