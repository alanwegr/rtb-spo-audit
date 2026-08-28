"""Synthetic OpenRTB log generator. Chunked, no big lists in RAM."""
import json
import random
import uuid
from typing import Iterator

from config import SCENARIOS

PUBLISHERS = ["nytimes.com", "cnn.com", "espn.com", "reddit.com"]
SSPS = ["google.com", "rubiconproject.com", "pubmatic.com", "xandr.com", "openx.com"]
DSPS = ["dv360-trader", "ttd-buyer", "amazon-aps", "criteo-bidder"]


def _node(asi: str, sid: str, hop: int, name: str | None = None, domain: str | None = None) -> dict:
    return {"asi": asi, "sid": sid, "rid": uuid.uuid4().hex[:12], "hp": hop, "name": name, "domain": domain}


def _schain(nodes: list[dict]) -> dict:
    return {"ver": "1.0", "complete": 1, "nodes": nodes}


def gen_auction(scenario: str = "A") -> dict:
    """1 bid request + N bid responses per scenario."""
    sid = uuid.uuid4().hex
    pub = random.choice(PUBLISHERS)
    ssp = random.choice(SSPS)
    dsp = random.choice(DSPS)
    base_cpm = round(random.uniform(0.5, 12.0), 2)
    latency_ms = random.randint(20, 300)
    net = base_cpm  # default; overwritten in branches that take a cut

    # schain + responses vary per scenario
    if scenario == "A":  # direct: 1-hop
        nodes = [_node(ssp, f"ssp-{random.randint(1000,9999)}", 1, ssp)]
        fee = 0.10
        net = base_cpm * (1 - fee)
        paths = [(dsp, base_cpm, net)]
    elif scenario == "B":  # margin leak: 3-hop
        ssp2 = random.choice(SSPS)
        nodes = [
            _node(ssp, f"ssp-{random.randint(1000,9999)}", 1, ssp),
            _node("ssp-shifty.example", f"res-{random.randint(100,999)}", 2, "Shady Reseller"),
            _node(ssp2, f"ssp-{random.randint(1000,9999)}", 3, ssp2),
        ]
        # hidden 20% skim at hop 2
        fee = 0.20
        net = base_cpm * (1 - fee) * 0.85
        paths = [(dsp, base_cpm, net)]
    else:  # C: duplication, 5 parallel
        nodes = [_node(ssp, f"ssp-{random.randint(1000,9999)}", 1, ssp)]
        paths = [
            (random.choice(DSPS), round(base_cpm * random.uniform(0.8, 1.1), 2),
             round(base_cpm * random.uniform(0.7, 0.95), 2))
            for _ in range(5)
        ]

    req = {
        "id": sid,
        "imp": [{"id": f"imp-{sid[:8]}", "bidfloor": 0.1, "bidfloorcur": "USD"}],
        "site": {"id": f"site-{pub}", "domain": pub, "publisher": {"id": f"pub-{pub}"}},
        "source": {"fd": 0, "tid": sid, "ext": {"schain": _schain(nodes)}},
        "tmax": 200,
        "at": 2,
    }
    responses = []
    for d, gross, net in paths:
        responses.append({
            "id": sid,
            "seatbid": [{"seat": d, "bid": [{
                "id": uuid.uuid4().hex, "impid": req["imp"][0]["id"],
                "price": gross, "adid": f"ad-{d}", "adm": "<div>creative</div>"
            }]}],
            "cur": "USD",
        })
    return {
        "scenario": scenario,
        "pub": pub,
        "ssp": ssp,
        "dsp": dsp,
        "gross_cpm": base_cpm,
        "net_cpm": net if scenario == "B" else paths[0][2],
        "latency_ms": latency_ms,
        "n_paths": len(paths),
        "request": req,
        "responses": responses,
    }


def stream(n: int, scenario: str = "A", seed: int = 42) -> Iterator[dict]:
    """Generator. Yields 1 auction at a time. No big list in RAM."""
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario must be in {list(SCENARIOS)}")
    random.seed(seed)
    for _ in range(n):
        yield gen_auction(scenario)


if __name__ == "__main__":
    # ponytail: self-check, fails if generator breaks
    import sys
    for sc in SCENARIOS:
        sample = gen_auction(sc)
        assert sample["request"]["id"] and sample["responses"], f"empty {sc}"
        assert sample["n_paths"] >= 1
    print("ok: 3 scenarios generate", file=sys.stderr)
