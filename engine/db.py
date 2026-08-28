"""DuckDB in-memory engine. Loads JSON, materializes views, returns conn."""
import duckdb
import json
import tempfile
from pathlib import Path
from typing import Iterable

from config import MOCK_SELLERS


def load_jsonl(auctions: Iterable[dict], conn: duckdb.DuckDBPyConnection) -> int:
    """Stream auctions to a temp NDJSON file, then read_json_auto. No big strings in RAM."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".ndjson", delete=False)
    n = 0
    for a in auctions:
        tmp.write(json.dumps(a) + "\n")
        n += 1
    tmp.close()
    conn.execute(f"CREATE OR REPLACE TABLE raw AS SELECT * FROM read_json_auto('{tmp.name}')")
    Path(tmp.name).unlink(missing_ok=True)
    return n


def build_views(conn: duckdb.DuckDBPyConnection) -> None:
    """3 views: flattened auctions, unnested schain, aggregated margins."""
    # v_auctions: 1 row per auction, top-level metrics + schain as JSON
    conn.execute("""
        CREATE OR REPLACE VIEW v_auctions AS
        SELECT
            request->>'id' AS auction_id,
            scenario,
            pub,
            ssp,
            dsp,
            gross_cpm,
            net_cpm,
            latency_ms,
            n_paths,
            request->'source'->'ext'->'schain' AS schain,
            request->'imp'->0->>'id' AS imp_id
        FROM raw
    """)

    # v_schain_nodes: 1 row per (auction, hop). unnest needs a typed list, not raw JSON.
    conn.execute("""
        CREATE OR REPLACE VIEW v_schain_nodes AS
        SELECT
            auction_id,
            unnest(from_json(schain->>'nodes',
                '["json"]')) AS node
        FROM v_auctions
    """)

    # v_path_margins: aggregate take-rate per ssp x scenario
    conn.execute("""
        CREATE OR REPLACE VIEW v_path_margins AS
        SELECT
            ssp,
            scenario,
            COUNT(*) AS auctions,
            AVG(gross_cpm) AS avg_gross_cpm,
            AVG(net_cpm) AS avg_net_cpm,
            AVG(1 - net_cpm / NULLIF(gross_cpm, 0)) AS avg_take_rate
        FROM v_auctions
        GROUP BY ssp, scenario
    """)


def fresh() -> duckdb.DuckDBPyConnection:
    """New in-memory conn w/ views + mock_sellers registered as a dict."""
    conn = duckdb.connect(":memory:")
    sellers = json.loads(MOCK_SELLERS.read_text())
    # widen each seller into a struct so SQL can join on it
    rows = [(asi, v["seller_type"], v["is_confidential"], v["name"])
            for asi, v in sellers.items()]
    conn.execute("""
        CREATE TABLE sellers(
            asi VARCHAR,
            seller_type VARCHAR,
            is_confidential INTEGER,
            name VARCHAR
        )
    """)
    conn.executemany("INSERT INTO sellers VALUES (?,?,?,?)", rows)
    return conn
