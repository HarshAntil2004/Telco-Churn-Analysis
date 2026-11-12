"""Step 3: EDA, statistical tests, churn model, risk scoring, charts, Tableau-ready export."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent.parent
OUT, IMG = ROOT / "outputs", ROOT / "images"
df = pd.read_csv(ROOT / "data" / "telco_clean.csv")
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
BLUE, RED = "#1f4e79", "#c0392b"
base = df["ChurnFlag"].mean() * 100

# ---------- 1. Statistical tests: is each factor related to churn? ----------
cats = ["Contract", "InternetService", "PaymentMethod", "TechSupport", "OnlineSecurity",
        "PaperlessBilling", "SeniorCitizen", "Partner", "Dependents", "gender", "AutoPay"]
rows = []
for c in cats:
    ct = pd.crosstab(df[c], df["ChurnFlag"])
    chi2, p, _, _ = chi2_contingency(ct)
    n = ct.values.sum()
    cramers_v = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))
    rows.append({"feature": c, "chi2": round(chi2, 1), "p_value": p, "cramers_v": round(cramers_v, 3),
                 "significant_at_5pct": p < 0.05})
tests = pd.DataFrame(rows).sort_values("cramers_v", ascending=False)
tests.to_csv(OUT / "chi_square_tests.csv", index=False)
print(tests.to_string(index=False))

# ---------- 2. Charts ----------
def bar_rate(col, title, fname, order=None):
    g = df.groupby(col)["ChurnFlag"].mean().mul(100)
    if order: g = g.reindex(order)
    else: g = g.sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 3.8))
    bars = ax.bar(g.index, g.values, color=[RED if v > base else BLUE for v in g.values])
    ax.axhline(base, ls="--", c="grey", lw=1); ax.text(len(g) - 0.5, base + 1, f"Avg {base:.1f}%", ha="right", color="grey")
    for b, v in zip(bars, g.values): ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}%", ha="center", fontsize=9)
    ax.set_ylabel("Churn rate (%)"); ax.set_title(title, loc="left", fontweight="bold")
    plt.xticks(rotation=15, ha="right"); plt.tight_layout(); fig.savefig(IMG / fname); plt.close(fig)

bar_rate("Contract", "Month-to-month customers churn 15x more than two-year", "churn_by_contract.png")
bar_rate("TenureGroup", "Nearly half of customers leave in their first year", "churn_by_tenure.png",
         ["0-12 mo", "13-24 mo", "25-48 mo", "49-72 mo"])
bar_rate("PaymentMethod", "Electronic-check payers are the biggest flight risk", "churn_by_payment.png")

# heatmap: contract x internet
pv = df.pivot_table(index="Contract", columns="InternetService", values="ChurnFlag", aggfunc="mean").mul(100)
fig, ax = plt.subplots(figsize=(6.5, 3.6))
im = ax.imshow(pv.values, cmap="Reds")
ax.set_xticks(range(len(pv.columns)), pv.columns); ax.set_yticks(range(len(pv.index)), pv.index)
for i in range(pv.shape[0]):
    for j in range(pv.shape[1]):
        ax.text(j, i, f"{pv.values[i, j]:.1f}%", ha="center", va="center",
                color="white" if pv.values[i, j] > 35 else "black", fontweight="bold")
ax.set_title("Churn rate: contract x internet service", loc="left", fontweight="bold")
plt.tight_layout(); fig.savefig(IMG / "churn_heatmap_contract_internet.png"); plt.close(fig)

# ---------- 3. Model ----------
features_num = ["tenure", "MonthlyCharges", "TotalCharges", "AddOnCount"]
features_cat = ["Contract", "InternetService", "PaymentMethod", "PaperlessBilling", "SeniorCitizen",
                "Partner", "Dependents", "TechSupport", "OnlineSecurity", "MultipleLines"]
X, y = df[features_num + features_cat], df["ChurnFlag"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
pre = ColumnTransformer([("num", StandardScaler(), features_num),
                         ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), features_cat)])

logit = Pipeline([("pre", pre), ("m", LogisticRegression(max_iter=1000, class_weight="balanced"))]).fit(Xtr, ytr)
gb = Pipeline([("pre", pre), ("m", GradientBoostingClassifier(random_state=42))]).fit(Xtr, ytr)
auc_l = roc_auc_score(yte, logit.predict_proba(Xte)[:, 1])
auc_g = roc_auc_score(yte, gb.predict_proba(Xte)[:, 1])
print(f"\nAUC logistic={auc_l:.3f}  gradient boosting={auc_g:.3f}")
pred = logit.predict(Xte)
print(classification_report(yte, pred, digits=3))
print(confusion_matrix(yte, pred))
report = classification_report(yte, pred, digits=3, output_dict=True)
pd.DataFrame({"metric": ["AUC_logistic", "AUC_gradient_boosting", "recall_churn_logistic", "precision_churn_logistic"],
              "value": [auc_l, auc_g, report["1"]["recall"], report["1"]["precision"]]}).round(3).to_csv(OUT / "model_metrics.csv", index=False)

# Logistic coefficients -> odds ratios
names = logit.named_steps["pre"].get_feature_names_out()
coefs = pd.DataFrame({"feature": names, "coef": logit.named_steps["m"].coef_[0]})
coefs["odds_ratio"] = np.exp(coefs["coef"])
coefs = coefs.reindex(coefs["coef"].abs().sort_values(ascending=False).index)
coefs.round(3).to_csv(OUT / "logistic_odds_ratios.csv", index=False)
top = coefs.head(12).iloc[::-1]
fig, ax = plt.subplots(figsize=(7.5, 4.6))
ax.barh([n.split("__")[1] for n in top["feature"]], top["coef"], color=[RED if c > 0 else BLUE for c in top["coef"]])
ax.set_title("What drives churn (logistic regression coefficients)", loc="left", fontweight="bold")
ax.set_xlabel("<- lowers churn risk | raises churn risk ->"); plt.tight_layout(); fig.savefig(IMG / "model_drivers.png"); plt.close(fig)

# ---------- 4. Risk scoring on all customers (cross-validated style: use full-data fit for scoring) ----------
final = Pipeline([("pre", pre), ("m", LogisticRegression(max_iter=1000, class_weight="balanced"))]).fit(X, y)
df["ChurnProbability"] = final.predict_proba(X)[:, 1].round(4)
df["RiskTier"] = pd.cut(df["ChurnProbability"], [-0.01, 0.3, 0.6, 1.0], labels=["Low", "Medium", "High"]).astype(str)
df["Segment"] = df["Contract"] + " | " + df["InternetService"]
tier = df.groupby("RiskTier").agg(customers=("customerID", "count"), actual_churn_rate=("ChurnFlag", "mean"),
                                  avg_monthly=("MonthlyCharges", "mean")).round(3)
print("\n", tier)

# Pareto: share of churn from top-N% riskiest customers
s = df.sort_values("ChurnProbability", ascending=False).reset_index(drop=True)
cum = s["ChurnFlag"].cumsum() / s["ChurnFlag"].sum()
for p in (0.1, 0.2, 0.3):
    print(f"Top {int(p*100)}% riskiest customers capture {cum.iloc[int(len(s)*p)-1]*100:.1f}% of churners")
fig, ax = plt.subplots(figsize=(6.5, 4))
x = np.arange(1, len(s) + 1) / len(s) * 100
ax.plot(x, cum * 100, c=RED, lw=2, label="Model-ranked"); ax.plot([0, 100], [0, 100], "--", c="grey", label="Random targeting")
ax.set_xlabel("% of customers contacted (highest risk first)"); ax.set_ylabel("% of churners reached")
ax.set_title("Targeting the riskiest 30% reaches most churners", loc="left", fontweight="bold"); ax.legend(frameon=False)
plt.tight_layout(); fig.savefig(IMG / "gains_curve.png"); plt.close(fig)

# ---------- 5. Business impact estimate ----------
high = df[df["RiskTier"] == "High"]
at_risk_rev = high.loc[high["ChurnFlag"] == 0, "MonthlyCharges"].sum()
mtm_fiber = df[(df.Contract == "Month-to-month") & (df.InternetService == "Fiber optic")]
conv = 0.15  # assumption: 15% of targeted MTM-fiber churners saved by offering a 1-year contract
saved = mtm_fiber.loc[mtm_fiber.ChurnFlag == 1, "MonthlyCharges"].sum() * conv
impact = {"mtm_fiber_customers": len(mtm_fiber), "mtm_fiber_share_of_base_pct": len(mtm_fiber) / len(df) * 100,
          "mtm_fiber_churn_rate_pct": mtm_fiber.ChurnFlag.mean() * 100,
          "mtm_fiber_monthly_rev_lost": mtm_fiber.loc[mtm_fiber.ChurnFlag == 1, "MonthlyCharges"].sum(),
          "assumed_save_rate_pct": conv * 100, "monthly_revenue_saved": saved, "annualised_revenue_saved": saved * 12,
          "high_risk_active_customers": int((high.ChurnFlag == 0).sum()), "high_risk_active_monthly_revenue": at_risk_rev}
pd.Series(impact).round(1).to_csv(OUT / "business_impact.csv", header=["value"])
print("\n", pd.Series(impact).round(1).to_string())

# ---------- 6. Tableau-ready export ----------
cols = ["customerID", "gender", "SeniorCitizen", "Partner", "Dependents", "tenure", "TenureGroup", "Contract",
        "InternetService", "PaymentMethod", "AutoPay", "PaperlessBilling", "TechSupport", "OnlineSecurity",
        "AddOnCount", "MonthlyCharges", "ChargeBand", "TotalCharges", "Churn", "ChurnFlag", "Segment",
        "ChurnProbability", "RiskTier"]
df[cols].to_csv(ROOT / "tableau" / "telco_churn_tableau.csv", index=False)
print("\nExported tableau/telco_churn_tableau.csv", df[cols].shape)
