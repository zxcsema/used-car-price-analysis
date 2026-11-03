"""Перенос исходных клиентов и рассчитанных в ноутбуке таблиц в схему sms_ab."""
from pathlib import Path
from io import StringIO
from hashlib import sha256
import json
import os

import numpy as np
import pandas as pd
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def copy_frame(cur, frame, table):
    buffer = StringIO()
    frame.to_csv(buffer, index=False)
    buffer.seek(0)
    query = sql.SQL("COPY sms_ab.{} ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)").format(
        sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, frame.columns)))
    cur.copy_expert(query.as_string(cur), buffer)


def main():
    metadata = json.loads((ROOT / "results/analysis_metadata.json").read_text())
    if sha256((ROOT / "data/uplift_train.csv.gz").read_bytes()).hexdigest() != metadata["source_sha256"]:
        raise ValueError("Исходный CSV изменился: сначала повторно выполните ноутбук.")
    users = pd.read_csv(ROOT / "data/uplift_train.csv.gz", dtype={"client_id": "string"})
    users = users[["client_id", "treatment_flg", "target"]]
    if (users.isna().any().any() or users.client_id.duplicated().any()
            or not users[["treatment_flg", "target"]].isin([0, 1]).all().all()):
        raise ValueError("Проблема исходных клиентов: загрузка отменена.")
    tables = ["experiment_summary", "planning_results", "available_mde",
              "sim_aa_summary", "sim_aa_histogram", "sim_power_results"]
    frames = {t: pd.read_csv(ROOT / f"results/{t}.csv") for t in tables}
    expected = pd.read_csv(ROOT / "results/group_summary.csv")
    with psycopg2.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute((ROOT / "sql/schema.sql").read_text())
            # Одна транзакция: читатели не увидят наполовину загруженные таблицы.
            names = sql.SQL(", ").join(sql.Identifier("sms_ab", t) for t in ["experiment_users", *tables])
            cur.execute(sql.SQL("TRUNCATE {}").format(names))
            copy_frame(cur, users, "experiment_users")
            for table, frame in frames.items():
                copy_frame(cur, frame, table)
            cur.execute("""SELECT treatment_flg, COUNT(*), SUM(target), AVG(target::float8)
                           FROM sms_ab.experiment_users GROUP BY treatment_flg ORDER BY treatment_flg""")
            actual = cur.fetchall()
            np.testing.assert_allclose(np.array(actual, dtype=float),
                expected[["treatment_flg", "clients", "buyers", "conversion"]].to_numpy(float), rtol=1e-12)
            row = frames["experiment_summary"].iloc[0]
            np.testing.assert_allclose(actual[1][3]-actual[0][3], row.effect, atol=1e-12)
            reader = os.environ["REDASH_PG_USER"]
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (reader,))
            exists = cur.fetchone()
            # Этот проект управляет только собственной технической ролью.
            if reader == "sms_ab_reader":
                verb = "ALTER" if exists else "CREATE"
                cur.execute(sql.SQL(verb + " ROLE {} LOGIN PASSWORD %s").format(sql.Identifier(reader)),
                            (os.environ["REDASH_PG_PASSWORD"],))
                cur.execute(sql.SQL("GRANT USAGE ON SCHEMA sms_ab TO {}").format(sql.Identifier(reader)))
                cur.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA sms_ab TO {}").format(sql.Identifier(reader)))
                cur.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA sms_ab GRANT SELECT ON TABLES TO {}").format(sql.Identifier(reader)))
            counts = {}
            for t in ["experiment_users", *tables]:
                cur.execute(sql.SQL("SELECT COUNT(*) FROM sms_ab.{}").format(sql.Identifier(t)))
                counts[t] = cur.fetchone()[0]
    report = {"rows": counts, "client_aggregates_match_notebook": True,
              "effect_matches_notebook": True}
    (ROOT / "results/postgres_check.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
