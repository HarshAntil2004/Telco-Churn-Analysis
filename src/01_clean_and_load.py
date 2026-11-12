"""Step 1: Clean raw Telco data with pandas and load it into a SQLite database."""
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
raw = pd.read_csv(ROOT / "data" / "telco_raw.csv")

df = raw.copy()
df.columns = [c.strip() for c in df.columns]
# TotalCharges has blank strings for brand-new customers (tenure = 0)
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].str.strip(), errors="coerce")
df["TotalCharges"] = df["TotalCharges"].fillna(0.0)
df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})
df["ChurnFlag"] = (df["Churn"] == "Yes").astype(int)

# Derived business fields
df["TenureGroup"] = pd.cut(df["tenure"], bins=[-1, 12, 24, 48, 72],
                           labels=["0-12 mo", "13-24 mo", "25-48 mo", "49-72 mo"])
df["TenureGroup"] = df["TenureGroup"].astype(str)
df["ChargeBand"] = pd.cut(df["MonthlyCharges"], bins=[0, 35, 70, 95, 200],
                          labels=["Low (<35)", "Mid (35-70)", "High (70-95)", "Premium (95+)"]).astype(str)
addons = ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"]
df["AddOnCount"] = (df[addons] == "Yes").sum(axis=1)
df["AutoPay"] = df["PaymentMethod"].str.contains("automatic").map({True: "Yes", False: "No"})

assert df["customerID"].is_unique
print("Rows:", len(df), "| Churn rate: %.2f%%" % (df["ChurnFlag"].mean() * 100))

df.to_csv(ROOT / "data" / "telco_clean.csv", index=False)

con = sqlite3.connect(ROOT / "data" / "telco.db")
df.to_sql("customers", con, if_exists="replace", index=False)
con.close()
print("Saved data/telco_clean.csv and data/telco.db")
