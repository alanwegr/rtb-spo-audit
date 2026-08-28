# rtb-spo-audit

SPO + margin audit engine. OpenRTB bid logs, schain compliance, sink analysis. Single Docker, <500MB RAM, $5 VPS.

## run

```sh
docker compose up --build     # http://localhost:8501
```

## dev

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## scenarios

A: direct 1-hop · B: 3-hop w/ hidden 20% skim · C: 5 parallel bid paths per imp

## test self-checks

```sh
python -m engine.generator
python -m engine.validator
```

## deploy to vps

copy `docker-compose.yml` + project dir, `docker compose up -d`. bind :8501 to nginx/cloudflare tunnel.

## layout

```
app.py            # streamlit entry
config.py         # thresholds, scenario map
engine/           # generator, duckdb views, validator
models/           # pydantic: openrtb, schain
ui/               # kpi cards, plotly sankey
data/             # mock_sellers.json (read-only mount)
```
