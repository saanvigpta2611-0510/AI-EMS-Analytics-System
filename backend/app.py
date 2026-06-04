from flask import Flask, render_template, request
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.io as pio
import joblib

app =  Flask(__name__)

# ---------------------------------
# MONGODB CONNECTION
# ---------------------------------

client = MongoClient(
    "mongodb://localhost:27017/"
)

db = client["EMS_Production_DB"]

collection = db["production_data"]

# ---------------------------------
# LOAD ML MODEL
# ---------------------------------

delay_model = joblib.load(
    "models/delay_prediction_model.pkl"
)

defect_model = joblib.load(

    "models/defect_model.pkl"
)

# ---------------------------------
# DASHBOARD ROUTE
# ---------------------------------

@app.route("/")

def dashboard():

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

    # LOAD DATA FROM MONGODB

    data = list(collection.find())

    df = pd.DataFrame(data)

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

    fig1 = px.line(

        trend_data,

        x="Production_Date",

        y="Actual_Output",

        markers=True
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
        full_html=False
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
                )
        }

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

        # DOWNTIME ANALYSIS

        if machine_summary["Downtime_Minutes"] > 55:

            ai_insights.append(

                "Machine downtime exceeded safe operational limit."

            )

        # TEMPERATURE ANALYSIS

        if machine_summary["Machine_Temperature"] > 75:

            ai_insights.append(

                "Machine temperature is critically high."

            )

        # EFFICIENCY ANALYSIS

        if machine_summary["Production_Efficiency"] < 70:

            ai_insights.append(

                "Production efficiency dropped below target."

            )

        # MATERIAL ANALYSIS

        if machine_summary["Inventory_Level"] < 550:

            ai_insights.append(

                "Critical material availability is low."

            )

        # OPERATOR ANALYSIS

        if machine_summary["Operator_Experience"] < 4:

            ai_insights.append(

                "Low operator experience may affect production stability."

            )

        # MAINTENANCE RECOMMENDATION

        if machine_summary["Downtime_Minutes"] > 100 and machine_summary["Machine_Temperature"] > 100:

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

            defect_result = "HIGH DEFECT RISK"

            defect_color = "danger"

        elif defect_score >= 4:

            defect_result = "MEDIUM DEFECT RISK"

            defect_color = "warning"

        else:

            defect_result = "LOW DEFECT RISK"

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

            failure_result = "HIGH FAILURE RISK"

            failure_color = "danger"

        elif failure_score >= 9:

            failure_result = "MEDIUM FAILURE RISK"

            failure_color = "warning"

        else:

            failure_result = "LOW FAILURE RISK"

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

    # -----------------------------------
    # MACHINE SPECIFIC PERFORMANCE GRAPHS
    # -----------------------------------

    # EFFICIENCY MACHINE GRAPH

    # EFFICIENCY MACHINE GRAPH

    efficiency_machine_data = df[
        df["Machine_ID"] == best_efficiency_machine
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
        height=500
    )

    efficiency_fig.update_traces(
        hovertemplate=
        "Date: %{x}<br>" +
        "Efficiency: %{y:.2f}%<extra></extra>"
    )

    efficiency_fig.write_html(
        "backend/static/efficiency_graph.html"
    )

    # DOWNTIME MACHINE GRAPH

    # DOWNTIME MACHINE GRAPH

    downtime_machine_data = df[
        df["Machine_ID"] == highest_downtime_machine
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
        height=500
    )

    downtime_fig.write_html(
        "backend/static/downtime_graph.html"
    )

    # DEFECT MACHINE GRAPH

    # DEFECT MACHINE GRAPH

    defect_machine_data = df[
        df["Machine_ID"] == most_defect_machine
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
        height=500
    )

    defect_fig.update_traces(
        hovertemplate=
        "Date: %{x}<br>" +
        "Defects: %{y:.2f}<extra></extra>"
    )

    defect_fig.write_html(
        "backend/static/defect_graph.html"
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

        machine_details=machine_details
    )

# ---------------------------------

if __name__ == "__main__":

    app.run(debug=True)
