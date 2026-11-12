"""Step 2: Execute every query in sql/analysis_queries.sql and export results to CSV."""
import re, sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
con = sqlite3.connect(ROOT / "data" / "telco.db")
sql = (ROOT / "sql" / "analysis_queries.sql").read_text()
queries = [q.strip() for q in sql.split(";") if re.search(r"\bSELECT\b", q)]
names = re.findall(r"-- (Q\d+)\.", sql)
for name, q in zip(names, queries):
    res = pd.read_sql_query(q, con)
    res.to_csv(ROOT / "outputs" / f"sql_{name.lower()}.csv", index=False)
    print(f"\n=== {name} ({len(res)} rows) ===")
    print(res.head(8).to_string(index=False))
con.close()
