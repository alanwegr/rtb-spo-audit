"""schain compliance + margin audit. Pure functions, takes a conn."""
from typing import Any
import duckdb

from config import TARGET_TAKE_RATE, SPO_SCORE_WEIGHTS


def schain_audit(conn: duckdb.DuckDBPyConnection) -> list[dict]:
    """Flag auctions w/ missing asi, unknown sellers, or unverified resellers."""
    return conn.execute("""
        SELECT
            n.auction_id,
            n.node->>'asi' AS asi,
            n.node->>'sid' AS sid,
            n.node->>'hp' AS hop,
            COALESCE(s.seller_type, 'UNKNOWN') AS seller_type,
            COALESCE(s.is_confidential, 1) AS is_confidential,
            CASE
                WHEN s.asi IS NULL THEN 'unknown_seller'
                WHEN s.is_confidential = 1 THEN 'unverified'
                WHEN s.seller_type = 'RESELLER' THEN 'unauthorized_reseller'
                ELSE 'ok'
            END AS flag
        FROM v_schain_nodes n
        LEFT JOIN sellers s ON n.node->>'asi' = s.asi
        ORDER BY n.auction_id, hop
    """).fetchall()


def margin_audit(conn: duckdb.DuckDBPyConnection) -> list[dict]:
    """Paths exceeding TARGET_TAKE_RATE flagged."""
    rows = conn.execute("""
        SELECT ssp, scenario, auctions, avg_gross_cpm, avg_net_cpm, avg_take_rate
        FROM v_path_margins
    """).fetchall()
    out = []
    for ssp, sc, n, gross, net, take in rows:
        take = take or 0
        out.append({
            "ssp": ssp, "scenario": sc, "auctions": n,
            "avg_gross_cpm": round(gross, 3),
            "avg_net_cpm": round(net, 3),
            "avg_take_rate": round(take, 4),
            "flagged": take > TARGET_TAKE_RATE,
        })
    return out


def duplication_audit(conn: duckdb.DuckDBPyConnection) -> dict:
    """QPS inflation from fan-out: avg paths per imp vs ideal 1."""
    return conn.execute("""
        SELECT
            AVG(n_paths) AS avg_paths_per_imp,
            SUM(n_paths) AS total_responses,
            COUNT(*) AS unique_auctions,
            ROUND(AVG(n_paths), 2) AS duplication_ratio
        FROM v_auctions
    """).fetchone()


def spo_score(margin: float, latency_ms: int, hop_count: int) -> float:
    """0-100 index. Higher = better. Margin efficiency normalized, latency inverse, clarity = 1/hops."""
    margin_eff = max(0, 1 - margin)  # less take = better
    latency_eff = max(0, 1 - latency_ms / 500)
    clarity = 1 / max(1, hop_count)
    w = SPO_SCORE_WEIGHTS
    return round(100 * (w["margin"] * margin_eff + w["latency"] * latency_eff + w["clarity"] * clarity), 1)


if __name__ == "__main__":
    # ponytail: end-to-end self-check
    from engine import db, generator
    conn = db.fresh()
    db.load_jsonl(generator.stream(50, "B"), conn)
    db.build_views(conn)
    margins = margin_audit(conn)
    assert any(m["flagged"] for m in margins), "B scenario should flag high take rate"
    rows = schain_audit(conn)
    assert rows and len(rows[0]) == 7, f"schain row shape: {len(rows[0]) if rows else 0} cols, flag must be idx 6"
    assert any(r[6] != "ok" for r in rows), "B scenario should produce schain flags"
    score = spo_score(0.20, 150, 3)
    assert 0 <= score <= 100
    print(f"ok: margins={len(margins)}, schain_rows={len(rows)}, sample_score={score}")
