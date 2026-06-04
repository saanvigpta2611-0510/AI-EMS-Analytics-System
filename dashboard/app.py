import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

# ---------------------------------
# PAGE CONFIG
# ---------------------------------

st.set_page_config(
    page_title="EMS Analytics Dashboard",
    layout="wide"
)

# ---------------------------------
# TITLE
# ---------------------------------

st.title("AI-Based EMS Production Analytics System")

st.markdown("---")

# ---------------------------------
# CONNECT TO MONGODB
# ---------------------------------

client = MongoClient(
    "mongodb://localhost:27017/"
)

db = client["EMS_Production_DB"]

collection = db["production_data"]

# ---------------------------------
# LOAD DATA FROM MONGODB
# ---------------------------------

data = list(collection.find())

df = pd.DataFrame(data)

# ---------------------------------
# REMOVE MONGODB ID COLUMN
# ---------------------------------

if "_id" in df.columns:
    df.drop("_id", axis=1, inplace=True)

# ---------------------------------
# SIDEBAR FILTERS
# ---------------------------------

st.sidebar.header("FILTER OPTIONS")

# SHIFT FILTER

selected_shift = st.sidebar.selectbox(
    "Select Shift",
    ["All"] + list(df["Shift_Type"].unique())
)

# MACHINE FILTER

selected_machine = st.sidebar.selectbox(
    "Select Machine",
    ["All"] + list(df["Machine_ID"].unique())
)

# MATERIAL FILTER

selected_material = st.sidebar.selectbox(
    "Material Quality",
    ["All"] + list(df["Material_Quality"].unique())
)

# ---------------------------------
# APPLY FILTERS
# ---------------------------------

filtered_df = df.copy()

if selected_shift != "All":
    filtered_df = filtered_df[
        filtered_df["Shift_Type"] == selected_shift
    ]

if selected_machine != "All":
    filtered_df = filtered_df[
        filtered_df["Machine_ID"] == selected_machine
    ]

if selected_material != "All":
    filtered_df = filtered_df[
        filtered_df["Material_Quality"]
        == selected_material
    ]

# ---------------------------------
# KPI CALCULATIONS
# ---------------------------------

total_output = int(
    filtered_df["Actual_Output"].sum()
)

avg_efficiency = round(
    filtered_df["Production_Efficiency"].mean(),
    2
)

avg_downtime = round(
    filtered_df["Downtime_Minutes"].mean(),
    2
)

total_defects = int(
    filtered_df["Defect_Count"].sum()
)

# ---------------------------------
# KPI DISPLAY
# ---------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Output",
    total_output
)

col2.metric(
    "Avg Efficiency",
    f"{avg_efficiency}%"
)

col3.metric(
    "Avg Downtime",
    avg_downtime
)

col4.metric(
    "Total Defects",
    total_defects
)

st.markdown("---")

# ---------------------------------
# GRAPH 1
# SHIFT VS EFFICIENCY
# ---------------------------------

shift_analysis = filtered_df.groupby(
    "Shift_Type"
)["Production_Efficiency"].mean().reset_index()

fig1 = px.bar(
    shift_analysis,
    x="Shift_Type",
    y="Production_Efficiency",
    title="Shift vs Production Efficiency"
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# ---------------------------------
# GRAPH 2
# MACHINE DOWNTIME
# ---------------------------------

machine_analysis = filtered_df.groupby(
    "Machine_ID"
)["Downtime_Minutes"].mean().reset_index()

fig2 = px.bar(
    machine_analysis,
    x="Machine_ID",
    y="Downtime_Minutes",
    title="Machine Downtime Analysis"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# ---------------------------------
# GRAPH 3
# MATERIAL QUALITY VS DEFECTS
# ---------------------------------

defect_analysis = filtered_df.groupby(
    "Material_Quality"
)["Defect_Count"].mean().reset_index()

fig3 = px.bar(
    defect_analysis,
    x="Material_Quality",
    y="Defect_Count",
    title="Material Quality vs Defects"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)