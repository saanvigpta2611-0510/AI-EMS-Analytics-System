import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

rows = 10000

data = []

start_date = datetime.now() - timedelta(days=365)

machines = ['M-101', 'M-102', 'M-103', 'M-104']

lines = ['Line-1', 'Line-2', 'Line-3']

products = ['PCB', 'Sensor', 'Microchip']

materials = ['Copper', 'Silicon', 'Plastic']

for i in range(rows):

    # RANDOM TIMESTAMP
    production_datetime = start_date + timedelta(
        minutes=random.randint(0, 525600)
    )

    # SHIFT
    shift = random.choice(['A', 'B', 'C'])

    # MACHINE
    machine = random.choice(machines)

    # MACHINE TEMPERATURE
    machine_temp = round(
        random.uniform(50, 120), 2
    )

    # ADDING NULL VALUES
    if random.random() < 0.05:
        machine_temp = None

    # ADDING NOISY VALUES
    if random.random() < 0.02:
        machine_temp = 200

    # OPERATOR EXPERIENCE
    operator_exp = random.randint(1, 15)

    # NULL OPERATOR EXPERIENCE
    if random.random() < 0.04:
        operator_exp = None

    # DOWNTIME
    downtime = random.randint(0, 120)

    # MAINTENANCE STATUS
    maintenance = random.choice(
        ['Done', 'Pending']
    )

    # NULL MAINTENANCE
    if random.random() < 0.03:
        maintenance = None

    # MATERIAL QUALITY
    material_quality = random.choice(
        ['High', 'Medium', 'Low']
    )

    # INVENTORY
    inventory = random.randint(100, 1000)

    # NULL INVENTORY
    if random.random() < 0.04:
        inventory = None

    row = {

        "Production_ID": i + 1,

        "Production_DateTime":
        production_datetime,

        "Production_Date":
        production_datetime.date(),

        "Production_Hour":
        production_datetime.hour,

        "Production_Week":
        production_datetime.isocalendar()[1],

        "Production_Month":
        production_datetime.month,

        "Shift_Type":
        shift,

        "Production_Line":
        random.choice(lines),

        "Product_Type":
        random.choice(products),

        "Batch_Number":
        fake.bothify(text='BATCH-####'),

        "Machine_ID":
        machine,

        "Machine_Temperature":
        machine_temp,

        "Machine_Run_Time":
        random.randint(5,24),

        "Downtime_Minutes":
        downtime,

        "Maintenance_Status":
        maintenance,

        "Power_Consumption":
        round(random.uniform(15,60),2),

        "Operator_ID":
        random.randint(1001,1050),

        "Operator_Experience":
        operator_exp,

        "Shift_Hours":
        random.randint(6,12),

        "Material_Type":
        random.choice(materials),

        "Material_Quality":
        material_quality,

        "Supplier_ID":
        random.randint(200,250),

        "Inventory_Level":
        inventory,

        "Production_Target":
        random.randint(300,1200),

        "Actual_Output":
        random.randint(200,1100),

        "Production_Efficiency":
        round(random.uniform(60,100),2),

        "Cycle_Time":
        round(random.uniform(0.5,5.0),2),

        "Defect_Count":
        random.randint(0,20),

        "Rejection_Count":
        random.randint(0,10),

        "Factory_Temperature":
        round(random.uniform(20,40),2),

        "Humidity_Level":
        round(random.uniform(30,80),2),

        "Noise_Level":
        round(random.uniform(50,120),2)

    }

    data.append(row)

df = pd.DataFrame(data)

df.to_csv(
    "data/raw_ems_data.csv",
    index=False
)

print("Raw EMS Dataset Generated Successfully")