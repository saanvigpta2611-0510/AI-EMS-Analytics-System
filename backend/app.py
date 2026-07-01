from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.io as pio
import joblib
import spacy
from rapidfuzz import fuzz
import re
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
import os

app =  Flask(__name__)
app.secret_key = "ems_secret_key"

nlp = spacy.load(
    "en_core_web_sm"
)

BEST_MACHINE = ""
DOWNTIME_MACHINE = ""
DEFECT_MACHINE = ""

CURRENT_MACHINE = "All"
CURRENT_SHIFT = "All"
CURRENT_PRODUCT = "All"
CURRENT_DURATION = "Last 7 Days"


LAST_TOTAL_OUTPUT = 0
LAST_AVG_EFFICIENCY = 0
LAST_AVG_DOWNTIME = 0
LAST_TOTAL_DEFECTS = 0
LAST_AI_INSIGHTS = []
LAST_RISK_LEVEL = ""

def normalize_message(message):

    message = message.lower()

    replacements = {

        "helo": "hello",

        "helloo": "hello",

        "hii": "hi",

        "hiii": "hi",

        "hiiii": "hi",

        "m103": "m-103",

        "machine 103": "m-103",

        "machine103": "m-103",

        "m102": "m-102",

        "machine 102": "m-102",

        "m101": "m-101",

        "machine 101": "m-101"

    }

    for old, new in replacements.items():

        message = message.replace(
            old,
            new
        )

    return message

intent_patterns = {

    "greeting": [

        "hello",
        "hi",
        "hey"

    ],

    "best_efficiency":[
        "best efficiency",
        "highest efficiency",
        "maximum efficiency",
        "max efficiency",
        "most efficient machine",
        "machine with highest efficiency",
        "which machine has highest efficiency"
    ],

    "highest_downtime":[

        "highest downtime",

        "maximum downtime",

        "max downtime",

        "machine with highest downtime",

        "which machine has highest downtime",

        "machine having highest downtime"

    ],

    "most_defects":[

        "most defects",

        "highest defects",

        "maximum defects",

        "machine having most defects",

        "machine with most defects",

        "which machine has most defects"

    ],

    "total_defects": [

        "total defects",

        "number of defects",

        "defect count"

    ],

    "production_output": [

        "output",

        "show output",

        "production output",

        "total output",

        "output for",

        "show production"

    ],

    "root_cause":[

        "why was output low",

        "root cause",

        "reason for low output",

        "why production dropped",

        "why output low"

    ],

    "trend_analysis":[

        "trend",

        "show trend",

        "output trend",

        "efficiency trend",

        "downtime trend",

        "defect trend"

    ],

    "compare_machine":[

        "compare",

        "compare machines",

        "machine comparison"

    ]

}

def detect_intent(message):

    best_match = None

    highest_score = 0

    for intent, phrases in intent_patterns.items():

        for phrase in phrases:

            score = fuzz.partial_ratio(

                message,

                phrase

            )

            if score > highest_score:

                highest_score = score

                best_match = intent

    if highest_score > 75:

        return best_match

    return "unknown"


@app.route("/chat")

def chat():

    message = request.args.get(
        "message",
        ""
    )

    message = normalize_message(
        message
    )

    machines = re.findall(

        r'm-\d+',

        message.lower()

    )

    specific_date = None

    months = {
        "january":1,
        "february":2,
        "march":3,
        "april":4,
        "may":5,
        "june":6,
        "july":7,
        "august":8,
        "september":9,
        "october":10,
        "november":11,
        "december":12
    }

    for month_name, month_num in months.items():

        match = re.search(

            month_name + r'\s+(\d+)',

            message.lower()

        )

        if match:

            day = int(match.group(1))

            specific_date = pd.Timestamp(

                year=2026,

                month=month_num,

                day=day

            )

            break

    custom_days = None

    match = re.search(

        r'last\s+(\d+)\s+days',

        message

    )

    if match:

        custom_days = int(

            match.group(1)

        )

    custom_weeks = None

    match = re.search(
        r'last\s+(\d+)\s+weeks',
        message
    )

    if match:

        custom_weeks = int(
            match.group(1)
        )

    custom_months = None

    match = re.search(
        r'last\s+(\d+)\s+months?',
        message
    )

    if match:

        custom_months = int(
            match.group(1)
        )


    custom_years = None

    match = re.search(
        r'last\s+(\d+)\s+years?',
        message
    )

    if match:

        custom_years = int(
            match.group(1)
        )

    intent = detect_intent(message)

    # Force analytics intents

    if (
        "efficiency" in message
        or "downtime" in message
        or "defect" in message
        or "risk" in message
        or "output" in message
        or "why" in message
        or "root cause" in message
        or "reason" in message
        or "compare" in message
    ):

        if "compare" in message:

            intent = "compare_machine"

        elif (
            "trend" in message
        ):

            intent = "trend_analysis"

        elif  (
            "why" in message
            or "root cause" in message
            or "reason" in message
        ):

            intent = "root_cause"

        elif "efficiency" in message:

            intent = "best_efficiency"

        elif "downtime" in message:

            intent = "highest_downtime"

        elif "defect" in message:

            if "total" in message:

                intent = "total_defects"

            else:

                intent = "most_defects"

        elif "output" in message:

            intent = "production_output"

    data = list(collection.find())

    df = pd.DataFrame(data)

    df["Production_Date"] = pd.to_datetime(
        df["Production_Date"]
    )

    print("Dataset starts :", df["Production_Date"].min())
    print("Dataset ends   :", df["Production_Date"].max())

    filtered_df = df.copy()

    filtered_df["Production_Date"] = pd.to_datetime(
        filtered_df["Production_Date"]
    )

    latest_date = filtered_df["Production_Date"].max()

    if custom_days:

        filtered_df = df[
            df["Production_Date"]
            >= latest_date - pd.Timedelta(days=custom_days)
        ]

    elif custom_weeks:

        filtered_df = df[
            df["Production_Date"]
            >= latest_date - pd.Timedelta(weeks=custom_weeks)
        ]

    elif custom_months:

        filtered_df = df[
            df["Production_Date"]
            >= latest_date - pd.DateOffset(months=custom_months)
        ]

    elif custom_years:

        filtered_df = df[
            df["Production_Date"]
            >= latest_date - pd.DateOffset(years=custom_years)
        ]

    machine = None
    shift = None
    product = None
    duration = None
    analytics_answer = None

    global CURRENT_MACHINE
    global CURRENT_SHIFT
    global CURRENT_PRODUCT
    global CURRENT_DURATION

    if intent != "compare_machine":

        if "m-101" in message:

            machine = "M-101"

        elif "m-102" in message:

            machine = "M-102"

        elif "m-103" in message:

            machine = "M-103"

        elif "m-104" in message:

            machine = "M-104"

    if "shift a" in message:

        shift = "A"

    elif "shift b" in message:

        shift = "B"

    elif "shift c" in message:

        shift = "C"

    if "pcb" in message:

        product = "PCB"

    elif "microchip" in message:

        product = "Microchip"

    elif "sensor" in message:

        product = "Sensor"

    if "7 days" in message:

        duration = "Last 7 Days"

    elif "30 days" in message:

        duration = "Last 30 Days"

    elif "8 weeks" in message:

        duration = "Last 8 Weeks"

    elif "6 months" in message:

        duration = "Last 6 Months"

    if machine:
        CURRENT_MACHINE = machine

    if shift:
        CURRENT_SHIFT = shift

    if product:
        CURRENT_PRODUCT = product

    if duration:
        CURRENT_DURATION = duration

    # DON'T reset filtered_df

    if CURRENT_SHIFT != "All":

        filtered_df = filtered_df[
            filtered_df["Shift_Type"] == CURRENT_SHIFT
        ]

    if CURRENT_MACHINE != "All":

        filtered_df = filtered_df[
            filtered_df["Machine_ID"] == CURRENT_MACHINE
        ]

    if CURRENT_PRODUCT != "All":

        filtered_df = filtered_df[
            filtered_df["Product_Type"] == CURRENT_PRODUCT
        ]

    # Apply dashboard duration ONLY if no custom duration exists

    if (
        custom_days is None
        and custom_weeks is None
        and custom_months is None
        and custom_years is None
    ):

        if CURRENT_DURATION == "Last 7 Days":

            filtered_df = filtered_df[
                filtered_df["Production_Date"]
                >= latest_date - pd.Timedelta(days=7)
            ]

        elif CURRENT_DURATION == "Last 30 Days":

            filtered_df = filtered_df[
                filtered_df["Production_Date"]
                >= latest_date - pd.Timedelta(days=30)
            ]

        elif CURRENT_DURATION == "Last 8 Weeks":

            filtered_df = filtered_df[
                filtered_df["Production_Date"]
                >= latest_date - pd.Timedelta(weeks=8)
            ]

        elif CURRENT_DURATION == "Last 6 Months":

            filtered_df = filtered_df[
                filtered_df["Production_Date"]
                >= latest_date - pd.Timedelta(days=180)
            ]

    print("--------------------------------")
    print("CURRENT_DURATION =", CURRENT_DURATION)
    print("CUSTOM DAYS =", custom_days)
    print("CUSTOM WEEKS =", custom_weeks)
    print("CUSTOM MONTHS =", custom_months)
    print("CUSTOM YEARS =", custom_years)

    print("ROWS AFTER FILTER =", len(filtered_df))
    print("MIN DATE =", filtered_df["Production_Date"].min())
    print("MAX DATE =", filtered_df["Production_Date"].max())
    print("--------------------------------")

    trend_type = "Actual_Output"

    if "output" in message:

        trend_type = "Actual_Output"

    elif "efficiency" in message:

        trend_type = "Production_Efficiency"

    elif "downtime" in message:

        trend_type = "Downtime_Minutes"

    elif "defect" in message:

        trend_type = "Defect_Count"

    if intent == "best_efficiency":

        best_machine = (
            filtered_df.groupby("Machine_ID")["Production_Efficiency"]
            .mean()
            .idxmax()
        )

        analytics_answer = (
            best_machine +
            " has the best efficiency."
        )

        print(
            filtered_df.groupby("Machine_ID")["Production_Efficiency"]
            .mean()
        )

    elif intent == "highest_downtime":

        downtime_machine = (
            filtered_df.groupby("Machine_ID")["Downtime_Minutes"]
            .mean()
            .idxmax()
        )

        analytics_answer = (
            downtime_machine +
            " has the highest downtime."
        )

        print(
            filtered_df.groupby("Machine_ID")["Downtime_Minutes"]
            .mean()
        )

    elif intent == "most_defects":

        defect_machine = (
            filtered_df.groupby("Machine_ID")["Defect_Count"]
            .sum()
            .idxmax()
        )

        analytics_answer = (
            defect_machine +
            " has the most defects."
        )

        print(
            filtered_df.groupby("Machine_ID")["Defect_Count"]
            .sum()
        )

    elif intent == "production_output":

        total_output = int(
            filtered_df["Actual_Output"].sum()
        )

        if custom_days:

            analytics_answer = (
                "Total output for last "
                + str(custom_days)
                + " days is "
                + str(total_output)
            )

        elif custom_weeks:

            analytics_answer = (
                "Total output for last "
                + str(custom_weeks)
                + " weeks is "
                + str(total_output)
            )

        elif custom_months:

            analytics_answer = (
                "Total output for last "
                + str(custom_months)
                + " months is "
                + str(total_output)
            )

        elif custom_years:

            analytics_answer = (
                "Total output for last "
                + str(custom_years)
                + " years is "
                + str(total_output)
            )

        else:

            analytics_answer = (
                "Total output is "
                + str(total_output)
            )

        if specific_date:

            date_df = df[

                df["Production_Date"] == specific_date

            ]

            total_output = int(

                date_df["Actual_Output"].sum()

            )

            analytics_answer = (

                "Production output for "

                + specific_date.strftime("%B %d")

                + " is "

                + str(total_output)

            )

        else:

            total_output = int(

                filtered_df["Actual_Output"].sum()

            )

            analytics_answer = (

                "Total output is "

                + str(total_output)

            )

    elif intent == "root_cause":

        date_df = df[

            df["Production_Date"] == specific_date

        ]

        output = int(
            date_df["Actual_Output"].sum()
        )

        downtime = round(
            date_df["Downtime_Minutes"].mean(),
            2
        )

        efficiency = round(
            date_df["Production_Efficiency"].mean(),
            2
        )

        defects = int(
            date_df["Defect_Count"].sum()
        )

        temp = round(
            date_df["Machine_Temperature"].mean(),
            2
        )

        cause = ""

        if downtime > 60:

            cause = "Downtime was unusually high."

        elif defects > 200:

            cause = "Defects increased significantly."

        elif temp > 85:

            cause = "Machine temperature exceeded safe range."

        elif efficiency < 78:

            cause = "Efficiency dropped."

        else:

            cause = "No major abnormality detected."

        analytics_answer = (

            f"Output: {output}<br>"
            f"Downtime: {downtime} mins<br>"
            f"Efficiency: {efficiency}%<br>"
            f"Defects: {defects}<br>"
            f"Temperature: {temp}°C<br><br>"
            f"Possible Root Cause:<br>{cause}"

        )

    elif intent == "trend_analysis":

        trend_df = (
            filtered_df
            .groupby("Production_Date")[trend_type]
            .mean()
            .reset_index()
        )

        if trend_type == "Actual_Output":
            metric_name = "Production Output"
            unit = " Units"

        elif trend_type == "Production_Efficiency":
            metric_name = "Efficiency"
            unit = "%"

        elif trend_type == "Downtime_Minutes":
            metric_name = "Downtime"
            unit = " mins"

        elif trend_type == "Defect_Count":
            metric_name = "Defects"
            unit = ""

        else:
            metric_name = "Value"
            unit = ""

        avg_value = round(trend_df[trend_type].mean(), 2)

        max_row = trend_df.loc[
            trend_df[trend_type].idxmax()
        ]

        min_row = trend_df.loc[
            trend_df[trend_type].idxmin()
        ]

        first_value = trend_df.iloc[0][trend_type]
        last_value = trend_df.iloc[-1][trend_type]

        if last_value > first_value:
            overall = "Increasing 📈"

        elif last_value < first_value:
            overall = "Decreasing 📉"

        else:
            overall = "Stable ➖"

        analytics_answer = f"""

        <b>📊 Trend Analysis</b><br><br>

        <b>Overall Trend:</b> {overall}<br>

        <b>Average {metric_name}:</b> {avg_value}{unit}<br>

        <b>Highest {metric_name}:</b>
        {round(max_row[trend_type],2)}{unit}
        ({max_row['Production_Date'].strftime('%b %d')})<br>

        <b>Lowest {metric_name}:</b>
        {round(min_row[trend_type],2)}{unit}
        ({min_row['Production_Date'].strftime('%b %d')})<br><br>

        """

        if custom_months or custom_years:

            monthly = (
                filtered_df
                .groupby(filtered_df["Production_Date"].dt.strftime("%B"))
                [trend_type]
                .mean()
                .reset_index()
            )

            analytics_answer += "<b>📅 Monthly Breakdown</b><br>"

            for _, row in monthly.iterrows():

                analytics_answer += (
                    f"{row['Production_Date']} : "
                    f"{round(row[trend_type],2)}<br>"
                )

            analytics_answer += "<br>"

        elif custom_weeks:

            weekly = (
                filtered_df
                .groupby(filtered_df["Production_Date"].dt.isocalendar().week)
                [trend_type]
                .mean()
                .reset_index()
            )

            analytics_answer += "<b>📅 Weekly Breakdown</b><br>"

            for _, row in weekly.iterrows():

                analytics_answer += (
                    f"Week {row['week']} : "
                    f"{round(row[trend_type],2)}<br>"
                )

            analytics_answer += "<br>"

        elif custom_days:

            analytics_answer += "<b>📅 Daily Breakdown</b><br>"

            for _, row in trend_df.iterrows():

                analytics_answer += (

                    row["Production_Date"].strftime("%b %d")

                    + " : "

                    + str(round(row[trend_type],2))

                    + "<br>"

                )

            analytics_answer += "<br>"

        analytics_answer += f"""

        <b>💡 AI Summary</b><br>

        • Production remained {overall.lower()}.<br>

        • Average value was {avg_value}.<br>

        • Highest performance occurred on
        {max_row['Production_Date'].strftime('%b %d')}.<br>

        • Lowest performance occurred on
        {min_row['Production_Date'].strftime('%b %d')}.<br>

        """

    elif intent == "compare_machine":

        if len(machines) >= 2:

            m1 = machines[0].upper()
            m2 = machines[1].upper()

            comparison_df = df.copy()

            machine1_df = comparison_df[
                comparison_df["Machine_ID"] == m1
            ]

            machine2_df = comparison_df[
                comparison_df["Machine_ID"] == m2
            ]

            print(m1)
            print(m2)
            print(len(machine1_df))
            print(len(machine2_df))

            eff1 = round(
                machine1_df["Production_Efficiency"].mean(),
                2
            )

            eff2 = round(
                machine2_df["Production_Efficiency"].mean(),
                2
            )

            down1 = round(
                machine1_df["Downtime_Minutes"].mean(),
                2
            )

            down2 = round(
                machine2_df["Downtime_Minutes"].mean(),
                2
            )

            def1 = int(
                machine1_df["Defect_Count"].sum()
            )

            def2 = int(
                machine2_df["Defect_Count"].sum()
            )

            score1 = 0
            score2 = 0

            if eff1 > eff2:
                score1 += 1
            else:
                score2 += 1

            if down1 < down2:
                score1 += 1
            else:
                score2 += 1

            if def1 < def2:
                score1 += 1
            else:
                score2 += 1

            better_machine = m1 if score1 > score2 else m2

            analytics_answer = f"""

            <b>{m1}</b><br>
            Efficiency : {eff1}%<br>
            Downtime : {down1} mins<br>
            Defects : {def1}<br><br>

            <b>{m2}</b><br>
            Efficiency : {eff2}%<br>
            Downtime : {down2} mins<br>
            Defects : {def2}<br><br>

            <b>Recommendation:</b><br>
            {better_machine} performs better overall.

            """
        
    # if "highest downtime" in message:

    #     analytics_answer = highest_downtime_machine

    # elif "best efficiency" in message:

    #     analytics_answer = best_efficiency_machine

    # elif "most defects" in message:

    #     analytics_answer = most_defect_machine

    # elif "current risk" in message:

    #     analytics_answer = risk_level

    # elif "total defects" in message:

    #     analytics_answer = str(total_defects)

    print(message)

    return {

        "intent": intent,

        "machine": machine,

        "shift": shift,

        "product": product,

        "duration": duration,

        "analytics_answer": analytics_answer

    }

# ---------------------------------
# MONGODB CONNECTION
# ---------------------------------

client = MongoClient(
    "mongodb://localhost:27017/"
)

db = client["EMS_Production_DB"]

collection = db["production_data"]

settings_collection = db["settings"]

# ---------------------------------
# LOAD ML MODEL
# ---------------------------------

delay_model = joblib.load(
    "models/delay_prediction_model.pkl"
)

defect_model = joblib.load(

    "models/defect_model.pkl"
)

@app.route("/")

def home():

    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["role"] = "admin"

            return redirect("/admin")

        elif username == "user" and password == "user123":

            session["role"] = "user"

            return redirect("/dashboard")

        else:

            return "Invalid Login"

    return render_template(
        "login.html"
    )

@app.route("/admin_dashboard")
def admin_dashboard():

    return render_template(
        "admin_dashboard.html"
    )

@app.route("/admin")
def admin():

    if session.get("role") != "admin":

        return redirect("/login")

    settings = settings_collection.find_one()

    return render_template(

        "admin_dashboard.html",

        settings=settings

    )

@app.route("/save_settings", methods=["POST"])
def save_settings():

    temperature_limit = int(
        request.form["temperature_limit"]
    )

    efficiency_limit = int(
        request.form["efficiency_limit"]
    )

    downtime_limit = int(
        request.form["downtime_limit"]
    )

    defect_limit = int(
        request.form["defect_limit"]
    )

    inventory_limit = int(
        request.form["inventory_limit"]
    )

    runtime_limit = int(
        request.form["runtime_limit"]
    )

    settings_collection.delete_many({})

    settings_collection.insert_one({

        "temperature_limit": temperature_limit,

        "efficiency_limit": efficiency_limit,

        "downtime_limit": downtime_limit,

        "defect_limit": defect_limit,

        "inventory_limit": inventory_limit,
        
        "runtime_limit": runtime_limit

    })

    return redirect("/admin")

# ---------------------------------
# DASHBOARD ROUTE
# ---------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

@app.route("/dashboard")

def dashboard():

    if "role" not in session:

        return redirect("/login")

    prediction_result = None

    # ---------------------------------
    # GET FILTER VALUES
    # ---------------------------------

    selected_shift = request.args.get(
        "shift",
        "All"
    )

    selected_machine = request.args.get(
        "machine",
        "All"
    )

    selected_product = request.args.get(
    "product_id",
    "All"
    )

    selected_duration = request.args.get(
        "duration",
        "Last 7 Days"
    )

    global LAST_SHIFT
    global LAST_MACHINE
    global LAST_PRODUCT
    global LAST_DURATION

    LAST_SHIFT = selected_shift
    LAST_MACHINE = selected_machine
    LAST_PRODUCT = selected_product
    LAST_DURATION = selected_duration

    # LOAD DATA FROM MONGODB

    data = list(collection.find())

    df = pd.DataFrame(data)

    print(df.columns.tolist())

    original_df = df.copy()

    # ---------------------------------
    # CONVERT DATE COLUMN (because dates are plain text and pyhton cannot do week,month,dates calculations until converted to datetime)
    # ---------------------------------

    df["Production_Date"] = pd.to_datetime(   
        df["Production_Date"]
    )

    # ---------------------------------
    # MATERIAL QUALITY ENCODING
    # ---------------------------------

    df["Material_Quality"] = df[
        "Material_Quality"
    ].map({

        "Low": 1,

        "Medium": 2,

        "High": 3
    })

    # ---------------------------------
    # DURATION FILTER
    # ---------------------------------

    latest_date = df["Production_Date"].max()

    if selected_duration == "Last 7 Days":

        df = df[
            df["Production_Date"]
            >= latest_date - pd.Timedelta(days=7)
        ]

    elif selected_duration == "Last 30 Days":

        df = df[
            df["Production_Date"]
            >= latest_date - pd.Timedelta(days=30)
        ]

    elif selected_duration == "Last 8 Weeks":

        df = df[
            df["Production_Date"]
            >= latest_date - pd.Timedelta(weeks=8)
        ]

    elif selected_duration == "Last 6 Months":

        df = df[
            df["Production_Date"]
            >= latest_date - pd.Timedelta(days=180)
        ]

    # ---------------------------------
    # APPLY FILTERS
    # ---------------------------------

    if selected_shift != "All":

        df = df[
            df["Shift_Type"]
            == selected_shift
        ]

    ranking_df = df.copy()

    if selected_machine != "All":

        df = df[
            df["Machine_ID"]
            == selected_machine
        ]

    if selected_product != "All":

        df = df[
            df["Product_Type"]
            == selected_product
        ]

    # REMOVE MONGODB ID

    if "_id" in df.columns:

        df.drop("_id", axis=1, inplace=True)

    # ---------------------------------
    # KPI CALCULATIONS
    # ---------------------------------

    total_output = int(
        df["Actual_Output"].sum()
    )

    avg_efficiency = round(
        df["Production_Efficiency"].mean(),
        2
    )

    avg_downtime = round(
        df["Downtime_Minutes"].mean(),
        2
    )

    total_defects = int(
        df["Defect_Count"].sum()
    )

    # ---------------------------------
    # GRAPH 1
    # PRODUCTION TREND
    # ---------------------------------

    trend_data = df.groupby(
        "Production_Date"
    )["Actual_Output"].sum().reset_index()


    root_cause_data = df.groupby(
        "Production_Date"
    ).agg({

        "Actual_Output": "sum",

        "Downtime_Minutes": "mean",

        "Production_Efficiency": "mean",

        "Defect_Count": "sum",

        "Machine_Temperature": "mean",

        "Inventory_Level": "mean",

        "Machine_Run_Time": "mean",

        "Production_Target": "sum"

    }).reset_index()


    avg_output = root_cause_data["Actual_Output"].mean()

    avg_downtime = root_cause_data["Downtime_Minutes"].mean()

    avg_temp = root_cause_data["Machine_Temperature"].mean()

    avg_defects = root_cause_data["Defect_Count"].mean()

    avg_material = root_cause_data["Inventory_Level"].mean()

    fig1 = px.line(

        root_cause_data,

        x="Production_Date",

        y="Actual_Output",

        markers=True,

        custom_data=[
            "Downtime_Minutes",
            "Production_Efficiency",
            "Defect_Count",
            "Machine_Temperature",
            "Inventory_Level",
            "Machine_Run_Time",
            "Production_Target"
        ]
    )

    fig1.update_layout(

        template="plotly_white",

        height=400
    )

    fig1.update_traces(
        hovertemplate=
        "Date: %{x}<br>" +
        "Output: %{y:.2f}<extra></extra>"
    )

    graph1 = pio.to_html(
        fig1,
        full_html=False,
        div_id="productionTrendGraph"
    )

    # ---------------------------------
    # GRAPH 2
    # MACHINE DOWNTIME
    # ---------------------------------

    downtime_data = df.groupby(
        "Machine_ID"
    )["Downtime_Minutes"].mean().reset_index()

    fig2 = px.bar(

        downtime_data,

        x="Machine_ID",

        y="Downtime_Minutes",

        color="Downtime_Minutes"
    )

    fig2.update_layout(

        template="plotly_white",

        height=400
    )

    fig2.update_traces(
        hovertemplate=
        "Machine: %{x}<br>" +
        "Downtime: %{y:.2f} min<extra></extra>"
    )

    graph2 = pio.to_html(
        fig2,
        full_html=False
    )

    # ---------------------------------
    # AUTOMATIC AI PREDICTION
    # ---------------------------------

    prediction_result = "No Prediction"

    if len(df) > 0:

        machine_summary = {

            "Downtime_Minutes":
                round(
                    df["Downtime_Minutes"].mean(),
                    2
                ),

            "Production_Efficiency":
                round(
                    df["Production_Efficiency"].mean(),
                    2
                ),

            "Machine_Temperature":
                round(
                    df["Machine_Temperature"].mean(),
                    2
                ),

            "Operator_Experience":
                round(
                    df["Operator_Experience"].mean(),
                    2
                ),

            "Inventory_Level":
                round(
                    df["Inventory_Level"].mean(),
                    2
                ),

            "Defect_Count":
                int(
                    df["Defect_Count"].sum()
                ),

            "Machine_Run_Time":
                round(
                    df["Machine_Run_Time"].mean(),
                    2
                )
        }

        print("Temperature =", machine_summary["Machine_Temperature"])
        print("Efficiency =", machine_summary["Production_Efficiency"])
        print("Downtime =", machine_summary["Downtime_Minutes"])
        print("Inventory =", machine_summary["Inventory_Level"])
        print("Runtime =", machine_summary["Machine_Run_Time"])
        print("Defects =", machine_summary["Defect_Count"])

        # ---------------------------------
        # SMART RISK DETECTION
        # ---------------------------------

        risk_points = 0

        # DOWNTIME

        if machine_summary["Downtime_Minutes"] > 40:

            risk_points += 2

        if machine_summary["Downtime_Minutes"] > 70:

            risk_points += 3

        # TEMPERATURE

        if machine_summary["Machine_Temperature"] > 75:

            risk_points += 2

        if machine_summary["Machine_Temperature"] > 90:

            risk_points += 3

        # EFFICIENCY

        if machine_summary["Production_Efficiency"] < 85:

            risk_points += 2

        if machine_summary["Production_Efficiency"] < 65:

            risk_points += 3

        # MATERIAL AVAILABILITY

        if machine_summary["Inventory_Level"] < 550:

            risk_points += 1

        if machine_summary["Inventory_Level"] < 600:

            risk_points += 2

        # OPERATOR EXPERIENCE

        if machine_summary["Operator_Experience"] < 5:

            risk_points += 1

        if machine_summary["Operator_Experience"] < 2:

            risk_points += 2

        # ---------------------------------
        # FINAL RISK LEVEL
        # ---------------------------------

        if risk_points >= 10:

            risk_level = "HIGH"

            risk_color = "danger"

        elif risk_points >= 3:

            risk_level = "MEDIUM"

            risk_color = "warning"

        else:

            risk_level = "LOW"

            risk_color = "success"

        ai_insights = []

        settings = settings_collection.find_one()

        temp_limit = settings["temperature_limit"]
        efficiency_limit = settings["efficiency_limit"]
        downtime_limit = settings["downtime_limit"]
        defect_limit = settings["defect_limit"]
        inventory_limit = settings["inventory_limit"]
        runtime_limit = settings["runtime_limit"]

        print("Limits:")
        print(temp_limit)
        print(efficiency_limit)
        print(downtime_limit)
        print(defect_limit)
        print(inventory_limit)
        print(runtime_limit)

        # DOWNTIME ANALYSIS

        if machine_summary["Downtime_Minutes"] > downtime_limit:

            ai_insights.append(

                "Machine downtime exceeded safe operational limit."

            )

        # TEMPERATURE ANALYSIS

        temperature_alert = False

        if machine_summary["Machine_Temperature"] > temp_limit:

            ai_insights.append(

                "Machine temperature is critically high."

            )

            temperature_alert = True

        # EFFICIENCY ANALYSIS

        if machine_summary["Production_Efficiency"] < efficiency_limit:

            ai_insights.append(

                "Production efficiency dropped below target."

            )

        # MATERIAL ANALYSIS

        if machine_summary["Inventory_Level"] < inventory_limit:

            ai_insights.append(

                "Critical material availability is low."

            )

        if machine_summary["Machine_Run_Time"] < runtime_limit:

            ai_insights.append(

                "Machine runtime is below target."

            )

        # OPERATOR ANALYSIS

        if machine_summary["Operator_Experience"] < 4:

            ai_insights.append(

                "Low operator experience may affect production stability."

            )

        # DEFECT ANALYSIS

        if machine_summary["Defect_Count"] > defect_limit:

            ai_insights.append(

                "Defect count exceeded acceptable limit."

            )

        # MAINTENANCE RECOMMENDATION

        if machine_summary["Downtime_Minutes"] > downtime_limit and machine_summary["Machine_Temperature"] > temp_limit:

            ai_insights.append(

                "Preventive maintenance is strongly recommended."

            )

        if len(ai_insights) == 0:

            ai_insights.append(

                "Production conditions are operating normally."

            )

        machine_details = {

            "Downtime":
                round(
                    machine_summary["Downtime_Minutes"],
                    2
                ),

            "Temperature":
                round(
                    machine_summary["Machine_Temperature"],
                    2
                ),

            "Efficiency":
                round(
                    machine_summary["Production_Efficiency"],
                    2
                ),

            "Operator_Experience":
                round(
                    machine_summary["Operator_Experience"],
                    2
                ),

            "Material_Availability":
                round(
                    machine_summary["Inventory_Level"],
                    2
                )
        }

        input_data = [[

            machine_summary["Downtime_Minutes"],

            machine_summary["Production_Efficiency"],

            machine_summary["Machine_Temperature"],

            machine_summary["Operator_Experience"],

            machine_summary["Inventory_Level"]

        ]]

        # ---------------------------------
        # DEFECT PREDICTION INPUT
        # ---------------------------------

        defect_input = [[

            df["Machine_Temperature"].max(),

            df["Downtime_Minutes"].max(),

            df["Production_Efficiency"].min(),

            df["Operator_Experience"].min(),

            df["Material_Quality"].min()

        ]]

        defect_prediction = defect_model.predict(
            defect_input
        )[0]

        prediction = delay_model.predict(
            input_data
        )[0]

        if prediction == 1:

            prediction_result = "HIGH DELAY RISK"

        else:

            prediction_result = "LOW DELAY RISK"

        # ---------------------------------
        # MATERIAL QUALITY DISPLAY
        # ---------------------------------

        quality_value = df[
            "Material_Quality"
        ].max()

        if quality_value == 1:

            material_quality_display = "Low"

            material_quality_color = "danger"

        elif quality_value == 2:

            material_quality_display = "Medium"

            material_quality_color = "warning"

        else:

            material_quality_display = "High"

            material_quality_color = "success"

        # ---------------------------------
        # AVERAGE VALUES
        # ---------------------------------

        avg_temp = round(df[
            "Machine_Temperature"
        ].mean(),2)

        avg_downtime = round(df[
            "Downtime_Minutes"
        ].mean(),2)

        avg_efficiency = round(df[
            "Production_Efficiency"
        ].mean(),2)

        avg_material_quality = round(df[
            "Material_Quality"
        ].mean(),2)

        avg_operator_exp = round(
            df[
                "Operator_Experience"
            ].mean(),

            2
        )

        avg_inventory = round(
            df[
                "Inventory_Level"
            ].mean(),

            2
        )

        recommendations = []

        # Temperature
        if avg_temp> 85:
            recommendations.append(
                "Machine temperature is high. Improve cooling and inspect ventilation systems."
            )

        # Downtime
        if avg_downtime > 60:
            recommendations.append(
                "Downtime is above safe limits. Increase preventive maintenance frequency."
            )

        # Operator Experience
        if avg_operator_exp < 8:
            recommendations.append(
                "Operator experience is low. Conduct additional training programs."
            )

        # Material Availability
        if avg_inventory < 550:
            recommendations.append(
                "Material availability is low. Improve inventory planning and procurement."
            )

        # Material Quality
        if avg_material_quality >= 1.5:
            recommendations.append(
                "Material quality is poor. Strengthen supplier quality checks."
            )

        # If everything is healthy
        if len(recommendations) == 0:
            recommendations.append(
                "Machine is operating within acceptable limits. Continue current practices."
            )

        # ---------------------------------
        # MATERIAL QUALITY DISPLAY
        # ---------------------------------

        if avg_material_quality >= 2.5:

            material_quality_display = "High"

            material_quality_color = "success"

        elif avg_material_quality >= 1.5:

            material_quality_display = "Medium"

            material_quality_color = "warning"

        else:

            material_quality_display = "Low"

            material_quality_color = "danger"


        # ---------------------------------
        # SMART DEFECT ANALYSIS
        # ---------------------------------

        defect_score = 0


        # TEMPERATURE

        if avg_temp > 75:

            defect_score += 2

        if avg_temp > 90:

            defect_score += 3


        # MATERIAL QUALITY

        if avg_material_quality < 2.5:

            defect_score += 2

        if avg_material_quality < 1.5:

            defect_score += 4


        # EFFICIENCY

        if avg_efficiency < 80:

            defect_score += 2

        if avg_efficiency < 65:

            defect_score += 3


        # DOWNTIME

        if avg_downtime > 40:

            defect_score += 1

        if avg_downtime > 70:

            defect_score += 2


        # ---------------------------------
        # FINAL DEFECT RESULT
        # ---------------------------------

        if defect_score >= 8:

            defect_result = "HIGH RISK"

            defect_color = "danger"

        elif defect_score >= 4:

            defect_result = "MEDIUM RISK"

            defect_color = "warning"

        else:

            defect_result = "LOW RISK"

            defect_color = "success"

        # ---------------------------------
        # FAILURE RISK ANALYSIS
        # ---------------------------------

        failure_score = 0


        # MACHINE TEMPERATURE

        if avg_temp >= 90:

            failure_score += 5

        elif avg_temp >= 80:

            failure_score += 3

        else:

            failure_score += 1


        # MACHINE DOWNTIME

        if avg_downtime >= 75:

            failure_score += 4

        elif avg_downtime >= 50:

            failure_score += 2

        else:

            failure_score += 1


        # MACHINE RUNTIME

        avg_runtime = round(

            df[
                "Machine_Run_Time"
            ].mean(),

            2
        )

        if avg_runtime >= 20:

            failure_score += 4

        elif avg_runtime >= 12:

            failure_score += 2

        else:

            failure_score += 1


        # MAINTENANCE STATUS

        maintenance_counts = df[
            "Maintenance_Status"
        ].value_counts()

        maintenance_status = maintenance_counts.idxmax()


        if maintenance_status == "Overdue":

            failure_score += 5

        elif maintenance_status == "Pending":

            failure_score += 3

        else:

            failure_score += 1


        # ---------------------------------
        # FINAL FAILURE RESULT
        # ---------------------------------

        if failure_score >= 11:

            failure_result = "HIGH RISK"

            failure_color = "danger"

        elif failure_score >= 9:

            failure_result = "MEDIUM RISK"

            failure_color = "warning"

        else:

            failure_result = "LOW RISK"

            failure_color = "success"

    product_list = sorted(

        original_df["Product_Type"]
        .dropna()
        .unique()
    )

    # ---------------------------------
    # MACHINE COMPARISON ANALYTICS
    # ---------------------------------

    machine_summary = ranking_df.groupby(
        "Machine_ID"
    ).agg({

        "Production_Efficiency": "mean",

        "Downtime_Minutes": "mean",

        "Defect_Count": "sum"

    }).reset_index()


    # BEST EFFICIENCY

    best_efficiency_machine = (
        machine_summary.loc[
            machine_summary[
                "Production_Efficiency"
            ].idxmax(),

            "Machine_ID"
        ]
    )


    # HIGHEST DOWNTIME

    highest_downtime_machine = (
        machine_summary.loc[
            machine_summary[
                "Downtime_Minutes"
            ].idxmax(),

            "Machine_ID"
        ]
    )


    # MOST DEFECTS

    most_defect_machine = (
        machine_summary.loc[
            machine_summary[
                "Defect_Count"
            ].idxmax(),

            "Machine_ID"
        ]
    )

    global BEST_MACHINE
    global DOWNTIME_MACHINE
    global DEFECT_MACHINE

    BEST_MACHINE = best_efficiency_machine
    DOWNTIME_MACHINE = highest_downtime_machine
    DEFECT_MACHINE = most_defect_machine

    print("BEST =", BEST_MACHINE)
    print("DOWNTIME =", DOWNTIME_MACHINE)
    print("DEFECT =", DEFECT_MACHINE)

    # -----------------------------------
    # MACHINE SPECIFIC PERFORMANCE GRAPHS
    # -----------------------------------

    # EFFICIENCY MACHINE GRAPH

    # EFFICIENCY MACHINE GRAPH

    efficiency_machine_data = ranking_df[
        ranking_df["Machine_ID"] == best_efficiency_machine
    ]

    efficiency_trend = efficiency_machine_data.groupby(
        "Production_Date"
    )["Production_Efficiency"].mean().reset_index()

    efficiency_fig = px.line(
        efficiency_trend,
        x="Production_Date",
        y="Production_Efficiency",
        title=f"{best_efficiency_machine} Efficiency Trend",
        markers=True
    )

    efficiency_fig.update_layout(
        template="plotly_white",
        height=500,
        autosize=True
    )

    efficiency_fig.update_traces(
        hovertemplate=
        "Date: %{x}<br>" +
        "Efficiency: %{y:.2f}%<extra></extra>"
    )

    efficiency_fig.write_html(
        "backend/static/efficiency_graph.html",
        config={
            "responsive": True
        }
    )

    # DOWNTIME MACHINE GRAPH

    # DOWNTIME MACHINE GRAPH

    downtime_machine_data = ranking_df[
        ranking_df["Machine_ID"] == highest_downtime_machine
    ]

    downtime_trend = downtime_machine_data.groupby(
        "Production_Date"
    )["Downtime_Minutes"].mean().reset_index()

    downtime_fig = px.line(
        downtime_trend,
        x="Production_Date",
        y="Downtime_Minutes",
        title=f"{highest_downtime_machine} Downtime Trend",
        markers=True
    )

    downtime_fig.update_layout(
        template="plotly_white",
        height=500,
        autosize=True
    )

    downtime_fig.write_html(
        "backend/static/downtime_graph.html",
        config={
            "responsive": True
        }
    )

    # DEFECT MACHINE GRAPH

    # DEFECT MACHINE GRAPH

    defect_machine_data = ranking_df[
        ranking_df["Machine_ID"] == most_defect_machine
    ]

    defect_trend = defect_machine_data.groupby(
        "Production_Date"
    )["Defect_Count"].sum().reset_index()

    defect_fig = px.line(
        defect_trend,
        x="Production_Date",
        y="Defect_Count",
        title=f"{most_defect_machine} Defect Trend",
        markers=True
    )

    defect_fig.update_layout(
        template="plotly_white",
        height=500,
        autosize=True
    )

    defect_fig.update_traces(
        hovertemplate=
        "Date: %{x}<br>" +
        "Defects: %{y:.2f}<extra></extra>"
    )

    defect_fig.write_html(
        "backend/static/defect_graph.html",
        config={
            "responsive": True
        }
    )

    # ---------------------------------
    # OUTPUT BREAKDOWN ANALYTICS
    # ---------------------------------

    output_breakdown = None


    # ALL MACHINES + ALL PRODUCTS

    if (
        selected_machine == "All"
        and
        selected_product == "All"
    ):

        output_breakdown = (
            ranking_df.groupby(
                "Machine_ID"
            )[
                "Actual_Output"
            ]
            .sum()
            .reset_index()
        )


    # SPECIFIC MACHINE + ALL PRODUCTS

    elif (
        selected_machine != "All"
        and
        selected_product == "All"
    ):

        machine_data = df[
            df["Machine_ID"] == selected_machine
        ]

        output_breakdown = (
            machine_data.groupby(
                "Product_Type"
            )[
                "Actual_Output"
            ]
            .sum()
            .reset_index()
        )

    else:
        output_breakdown = None

    # ---------------------------------
    # DEFECT CAUSE ANALYSIS
    # ---------------------------------

    defect_causes = []


    # MECHANICAL

    if avg_downtime >= 85:

        mechanical_issue ="Bearing wear causing severe vibration instability"

    elif avg_downtime >= 70:

        mechanical_issue ="Machine shaft misalignment affecting production accuracy"

    elif avg_downtime >= 55:

        mechanical_issue ="Tool bluntness reducing production precision"

    else:

        mechanical_issue = None

    if mechanical_issue:

        defect_causes.append({

            "category": "Mechanical Defects",

            "issues": [
                mechanical_issue
            ]
        })

    # ELECTRICAL

    if avg_temp >= 95:

        thermal_issue ="Critical motor overheating detected"

    elif avg_temp >= 90:

        thermal_issue ="Cooling airflow obstruction detected"

    elif avg_temp >= 85:

        thermal_issue ="Sensor instability affecting machine calibration"

    else:

        thermal_issue = None

    if thermal_issue:

        defect_causes.append({

            "category": "Electrical Defects",

            "issues": [
                thermal_issue
            ]
        })
    

    # OPERATOR RELATED

    if avg_operator_exp <= 4:

        operator_issue ="Operator handling inconsistency increasing rejection rates"

    elif avg_operator_exp <= 6:

        operator_issue ="Improper machine calibration during shifts"

    elif avg_operator_exp <= 8:

        operator_issue ="Minor process timing mismatch detected"

    else:

        operator_issue = None

    if operator_issue:

        defect_causes.append({

            "category": "Operator Defects",

            "issues": [
                operator_issue
            ]
        })

    # MATERIAL QUALITY

    material_issue = None


    if material_quality_display == "Low":

        material_issue = (
            "Poor raw material consistency affecting production quality"
        )


    elif material_quality_display == "Medium":

        material_issue = (
            "Supplier material variation causing minor inconsistencies"
        )


    elif material_quality_display == "High":

        material_issue = (
            "Material quality operating within acceptable production standards"
        )


    if material_issue:

        defect_causes.append({

            "category": "Material Quality Issues",

            "issues": [
                material_issue
            ]
        })

    # FALLBACK

    if len(defect_causes) == 0:

        general_issue = (
            "Production system operating within stable manufacturing conditions"
        )

        defect_causes.append({

            "category": "General Manufacturing Status",

            "issues": [
                general_issue
            ]
        })


    global LAST_TOTAL_OUTPUT
    global LAST_AVG_EFFICIENCY
    global LAST_AVG_DOWNTIME
    global LAST_TOTAL_DEFECTS
    global LAST_AI_INSIGHTS
    global LAST_RISK_LEVEL

    LAST_TOTAL_OUTPUT = total_output
    LAST_AVG_EFFICIENCY = avg_efficiency
    LAST_AVG_DOWNTIME = avg_downtime
    LAST_TOTAL_DEFECTS = total_defects
    LAST_AI_INSIGHTS = ai_insights
    LAST_RISK_LEVEL = risk_level

    # ---------------------------------
    # SEND VALUES TO HTML
    # ---------------------------------

    return render_template(

        "dashboard.html",

        total_output=total_output,

        avg_efficiency=avg_efficiency,

        avg_downtime=avg_downtime,

        total_defects=total_defects,

        selected_shift=selected_shift,

        selected_machine=selected_machine,

        selected_duration=selected_duration,

        graph1=graph1,

        graph2=graph2,

        prediction_result=prediction_result,

        product_list=product_list,

        selected_product=selected_product,

        ai_insights=ai_insights,

        risk_level=risk_level,

        risk_color=risk_color,

        defect_result=defect_result,

        defect_color=defect_color,

        material_quality_display=material_quality_display,

        material_quality_color=material_quality_color,

        failure_result=failure_result,

        failure_color=failure_color,

        avg_runtime=avg_runtime,

        maintenance_status=maintenance_status,

        avg_temp=avg_temp,

        best_efficiency_machine=best_efficiency_machine,

        highest_downtime_machine=highest_downtime_machine,

        most_defect_machine=most_defect_machine,

        avg_operator_exp=avg_operator_exp,

        avg_inventory=avg_inventory,

        output_breakdown=output_breakdown,

        df=df,

        defect_causes=defect_causes,

        recommendations=recommendations,

        temperature_alert=temperature_alert,

        machine_details=machine_details
    )

@app.route("/download_report")
def download_report():

    total_output = LAST_TOTAL_OUTPUT
    avg_efficiency = LAST_AVG_EFFICIENCY
    avg_downtime = LAST_AVG_DOWNTIME
    total_defects = LAST_TOTAL_DEFECTS

    import os

    pdf_path = os.path.join(
        os.path.dirname(__file__),
        "production_report.pdf"
    )

    pdf = SimpleDocTemplate(pdf_path)

    styles = getSampleStyleSheet()

    content = []

    from datetime import datetime

    content.append(
        Paragraph(
            f"Generated On : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
            styles["Normal"]
        )
    )

    content.append(Spacer(1,20))

    content.append(Spacer(1,12))

    content.append(
        Paragraph(
            "EMS Production Analytics Report",
            styles["Title"]
        )
    )

    content.append(Spacer(1,20))

    content.append(
        Paragraph(
            "Report Filters",
            styles["Heading2"]
        )
    )

    content.append(
        Paragraph(
            f"Duration : {LAST_DURATION}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Shift : {LAST_SHIFT}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Machine : {LAST_MACHINE}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Product : {LAST_PRODUCT}",
            styles["Normal"]
        )
    )

    content.append(Spacer(1,20))

    content.append(
        Paragraph(
            f"Total Output : {total_output}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Average Efficiency : {avg_efficiency}%",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Average Downtime : {avg_downtime} mins",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Total Defects : {total_defects}",
            styles["Normal"]
        )
    )

    content.append(Spacer(1,20))

    content.append(
        Paragraph(
            "AI Manufacturing Insights",
            styles["Heading2"]
        )
    )

    for insight in LAST_AI_INSIGHTS:

        content.append(
            Paragraph(
                "• " + insight,
                styles["Normal"]
            )
        )

    content.append(Spacer(1,20))

    content.append(
        Paragraph(
            f"Risk Level : {LAST_RISK_LEVEL}",
            styles["Heading2"]
        )
    )

    pdf.build(content)

    print("PDF SAVED AT:", pdf_path)

    return send_file(
        pdf_path,
        as_attachment=True
    )

# ---------------------------------

if __name__ == "__main__":

    app.run(debug=True)
