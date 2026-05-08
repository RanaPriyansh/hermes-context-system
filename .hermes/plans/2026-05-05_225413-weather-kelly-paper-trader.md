# Weather-Kelly Polymarket Paper Trader Implementation Plan

> **For Hermes:** Use `subagent-driven-development` skill to implement this plan task-by-task after the operator exits plan mode.

**Goal:** Build a new paper-only repository that tests the real WeatherTraderBot secret: calibrated high-temperature probability distributions + Polymarket microstructure discipline, with KL/Kelly as gauges rather than cargo-cult triggers.

**Architecture:** A read-only collector discovers active Polymarket weather temperature bucket events, parses each bucket, pulls executable CLOB order books, estimates model probabilities from weather forecasts, computes spread/fee-adjusted edge, writes paper signals, simulates fills, and evaluates settled outcomes. The repo must contain no live-trading wallet code in the first version.

**Tech Stack:** Python 3.11+, `httpx`/`requests`, `pydantic`, `PyYAML`, `numpy`, optional `scipy`, `pytest`, `ruff`, `rich`; Polymarket Gamma/CLOB/Data public APIs; NOAA/NWS/Open-Meteo forecast adapters behind a common provider interface.

---

## Plan-mode note

This plan mode turn creates **only this markdown plan**:

- Plan path: `.hermes/plans/2026-05-05_225413-weather-kelly-paper-trader.md`
- Intended new repo path: `/root/projects/weather-kelly-trader`
- Intended package name: `weather_kelly`

No repo, code, cron job, systemd service, live order module, or downstream artifact is created by this plan.

---

## Strategic thesis and chosen wedge

The contrarian secret is not “KL divergence prints money.” KL is a meter. The edge, if it exists, is:

1. Weather markets are short-dated categorical probability distributions.
2. Retail markets misprice tails and stale bucket ranges.
3. Forecast distributions can be better calibrated than market prices for 0–48h high-temperature events.
4. Profit only survives if we account for overround, bid/ask spread, depth, fees, resolution text, and station/source mismatch.

**Chosen wedge:** Start with **NYC highest-temperature bucket markets only** for the first 48h paper run.

Why NYC first:

- The verified WeatherTraderBot data showed major NYC high-temperature wins.
- NYC markets are liquid enough to paper-test executable fills.
- US weather source resolution is easier to audit than global locations.
- One city prevents the usual bot death spiral: five APIs, ten units, wrong station, fake confidence.

London, Seoul, Hong Kong, Beijing are Phase 2 after the parser, forecast adapter, and settlement loop prove themselves on NYC.

---

## First users / operator segment

Initial user is us: an operator who wants to know if this strategy can make money paper-trading for a few days.

Potential later users if evidence is strong:

- Prediction-market traders who want weather-market signals.
- Quant hobbyists who want a transparent weather edge dashboard.
- Copy-trading/signal subscribers, if live evidence eventually exists.

No monetization before paper evidence. No live-trading promises.

---

## Current context / assumptions

Evidence already checked:

- `@WeatherTraderBot` shows roughly `+$162k` P&L and `1,653` trades publicly.
- Closed high-temperature positions fetched from Data API showed roughly:
  - `1,008` high-temperature positions
  - `+$53.1k` P&L
  - `43.8%` win rate
  - `2.29` profit factor
  - `23.7%` ROI on cost
- The viral KL example was mathematically wrong:
  - For `p=0.22`, `q=0.105`, one-term `p log2(p/q)` is about `0.235` bits.
  - Correct binary KL is about `0.080` bits.

Implementation assumptions:

- First repo is local under `/root/projects/weather-kelly-trader`.
- First run is paper-only with read-only Polymarket APIs.
- No private keys, no wallet signing, no geoblock bypasses, no live execution.
- We use executable CLOB ask prices for simulated buys, not stale Gamma `outcomePrices` alone.
- Weather provider quality is a first-class experiment, not an afterthought.

---

## Safety / trust / compliance constraints

Hard rules for v0:

- Paper-only. No live trade placement.
- No wallet/private-key environment variables.
- No live CLOB client methods named `place_order`, `sign_order`, or `submit_order`.
- No geoblock bypasses.
- Every simulated fill must include `paper: true` and `fill_source: simulated_clob_ask`.
- Signals must be saved even when zero signals exist to avoid stale artifacts.
- If market resolution text or station/source is ambiguous, mark `resolution_confidence: low` and do not trade unless explicitly allowed in config.
- Never evaluate profitability from open/unsettled markets as final P&L.

Paper risk defaults:

- Starting bankroll: `$500`
- Max stake per market: `$10`
- Max event exposure: `$25`
- Max daily new exposure: `$75`
- Fractional Kelly cap: `0.25x Kelly`
- Minimum simulated order size: Polymarket book min size or `$1`, whichever is higher for paper accounting
- Fees: use weather fee assumption from Polymarket fees page, default `1.25%` unless event-specific fee can be detected

---

## Proposed repository layout

```text
/root/projects/weather-kelly-trader/
  README.md
  pyproject.toml
  .gitignore
  .env.example
  configs/
    paper.yaml
    cities.yaml
  src/weather_kelly/
    __init__.py
    cli.py
    config.py
    models.py
    timeutils.py
    logging_utils.py
    polymarket/
      __init__.py
      gamma.py
      clob.py
      data_api.py
      market_grouping.py
    parsing/
      __init__.py
      temperature_market.py
      resolution_text.py
    weather/
      __init__.py
      city_registry.py
      distribution.py
      calibration.py
      providers/
        __init__.py
        base.py
        nws.py
        open_meteo.py
        noaa_gefs.py
    edge/
      __init__.py
      kl.py
      signal.py
      sizing.py
    paper/
      __init__.py
      ledger.py
      executor.py
      portfolio.py
    settlement/
      __init__.py
      resolver.py
      scoreboard.py
    dashboard/
      __init__.py
      app.py
  tests/
    fixtures/
      gamma_nyc_event.json
      clob_book_yes.json
      nws_hourly_forecast.json
      settled_positions_weathertraderbot_sample.json
    test_temperature_parser.py
    test_kl_math.py
    test_distribution.py
    test_signal_generation.py
    test_paper_ledger.py
    test_settlement_scoreboard.py
  scripts/
    run_paper_loop.sh
    summarize_paper.py
  data/                 # gitignored runtime artifacts
    raw/
    signals/
    paper/
    settlement/
    reports/
```

---

## Runtime artifact contracts

### `data/signals/latest.json`

Always write this file on every scan, even if there are no signals.

```json
{
  "timestamp": "2026-05-05T22:54:13+02:00",
  "mode": "paper",
  "provider": "nws_calibrated_normal_v0",
  "event_count": 0,
  "market_count": 0,
  "signal_count": 0,
  "signals": []
}
```

Signal object shape:

```json
{
  "signal_id": "nyc-2026-05-06-66-67f-yes-20260505T210000Z",
  "event_slug": "highest-temperature-in-nyc-on-may-6-2026",
  "market_slug": "highest-temperature-in-nyc-on-may-6-2026-66-67f",
  "question": "Will the highest temperature in New York City be between 66-67°F on May 6?",
  "city": "NYC",
  "date_local": "2026-05-06",
  "bucket": {"kind": "range", "unit": "F", "low": 66, "high": 67},
  "side": "YES",
  "model_probability": 0.42,
  "market_best_ask": 0.35,
  "market_best_bid": 0.34,
  "market_normalized_probability": 0.331,
  "edge_abs": 0.07,
  "edge_roi": 0.20,
  "binary_kl_bits": 0.014,
  "categorical_kl_bits": 0.052,
  "kelly_fraction": 0.108,
  "recommended_stake_usd": 10.0,
  "max_fill_shares": 28.57,
  "depth_usd_at_or_below_limit": 120.0,
  "fee_assumption": 0.0125,
  "resolution_confidence": "medium",
  "reason": "p_gt_ask_after_fee_and_spread; depth_ok; event_exposure_ok"
}
```

### `data/paper/ledger.jsonl`

One JSON line per simulated event.

```json
{"timestamp":"2026-05-05T22:55:00+02:00","type":"paper_fill","signal_id":"...","market_slug":"...","side":"YES","shares":28.57,"price":0.35,"stake_usd":10.0,"fee_usd":0.125,"paper":true}
```

### `data/settlement/scoreboard.csv`

CSV headers:

```csv
settled_at,event_slug,market_slug,city,date_local,bucket,side,shares,entry_price,entry_cost_usd,settle_value_usd,pnl_usd,roi_pct,model_probability,entry_ask,binary_kl_bits,categorical_kl_bits,provider,resolution_confidence
```

---

## Core formulas to implement

### Binary KL, not viral one-term KL

```python
import math

EPS = 1e-9

def clamp_prob(x: float) -> float:
    return min(1.0 - EPS, max(EPS, float(x)))

def binary_kl_bits(p: float, q: float) -> float:
    p = clamp_prob(p)
    q = clamp_prob(q)
    return p * math.log2(p / q) + (1 - p) * math.log2((1 - p) / (1 - q))

def edge_roi(p: float, executable_price: float) -> float:
    p = clamp_prob(p)
    q = clamp_prob(executable_price)
    return p / q - 1.0

def kelly_fraction(p: float, executable_price: float) -> float:
    p = clamp_prob(p)
    q = clamp_prob(executable_price)
    return max(0.0, (p - q) / (1.0 - q))
```

### Bucket probability from a high-temperature distribution

For integer Fahrenheit buckets, include rounding boundary logic:

- Exact `70°F`: probability high temp rounds to `70`.
- Range `66-67°F`: probability high temp rounds to `66` or `67`.
- `65°F or below`: probability high temp rounds to `<=65`.
- `74°F or higher`: probability high temp rounds to `>=74`.

Default MVP distribution:

- Get forecast hourly temperatures for city/date.
- Compute forecast high temperature.
- Apply calibrated error model by horizon and city.
- Convert to bucket probabilities.

Initial calibration prior:

```yaml
calibration:
  default_error_sigma_f_by_horizon_days:
    0: 2.0
    1: 3.0
    2: 4.0
  min_sigma_f: 1.5
  max_sigma_f: 6.0
```

This is intentionally humble. We paper-test whether it beats market prices. If not, we upgrade to true ensemble extraction.

---

## Step-by-step implementation plan

### Task 0: Create the local repo scaffold

**Objective:** Create a fresh local git repo for the project.

**Files:**
- Create repo root: `/root/projects/weather-kelly-trader`

**Steps:**

```bash
mkdir -p /root/projects/weather-kelly-trader
cd /root/projects/weather-kelly-trader
git init -b main
```

**Verification:**

```bash
git status --short
```

Expected: clean empty repo on `main`.

**Commit:** none yet until bootstrap files exist.

---

### Task 1: Bootstrap Python package and developer tooling

**Objective:** Create installable Python package with test/lint commands.

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `.env.example`
- Create: `src/weather_kelly/__init__.py`
- Create: `tests/`

**Implementation notes:**

`pyproject.toml` should define:

- package: `weather-kelly-trader`
- module: `weather_kelly`
- console script: `weather-kelly = weather_kelly.cli:main`
- dependencies: `httpx`, `pydantic`, `PyYAML`, `numpy`, `rich`, optional `scipy`
- dev dependencies: `pytest`, `ruff`

`.gitignore` must ignore:

```gitignore
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.env
data/
*.db
*.sqlite
```

**Verification:**

```bash
cd /root/projects/weather-kelly-trader
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
python -c 'import weather_kelly; print(weather_kelly.__version__)'
pytest -q
ruff check .
```

Expected: import succeeds; tests either zero-test clean or initial smoke test passes.

**Commit:**

```bash
git add .
git commit -m "chore: bootstrap weather kelly trader repo"
```

---

### Task 2: Add config and city registry

**Objective:** Define paper risk settings and supported city metadata.

**Files:**
- Create: `configs/paper.yaml`
- Create: `configs/cities.yaml`
- Create: `src/weather_kelly/config.py`
- Create: `src/weather_kelly/weather/city_registry.py`
- Test: `tests/test_config.py`

**`configs/paper.yaml` starter:**

```yaml
mode: paper
bankroll_usd: 500
poll_interval_seconds: 300
allowed_cities: [NYC]
max_stake_per_market_usd: 10
max_event_exposure_usd: 25
max_daily_new_exposure_usd: 75
fractional_kelly: 0.25
weather_fee_rate: 0.0125
min_edge_abs: 0.03
min_edge_roi: 0.20
min_binary_kl_bits: 0.01
min_depth_usd: 10
max_spread: 0.04
require_resolution_confidence: medium
write_zero_signal_file: true
```

**`configs/cities.yaml` starter:**

```yaml
cities:
  NYC:
    display_name: New York City
    timezone: America/New_York
    latitude: 40.7829
    longitude: -73.9654
    unit: F
    candidate_station_ids: [KNYC]
    resolution_notes: "Verify from market description; default assumes Central Park/KNYC-like NYC high temperature."
```

**Verification:**

```bash
pytest tests/test_config.py -q
```

Expected: config loads, paper mode enforced, NYC metadata exists.

**Commit:**

```bash
git add configs src/weather_kelly tests/test_config.py
git commit -m "feat: add paper config and city registry"
```

---

### Task 3: Implement correct KL/Kelly math with tests

**Objective:** Prevent the viral math error from entering the codebase.

**Files:**
- Create: `src/weather_kelly/edge/kl.py`
- Create: `tests/test_kl_math.py`

**Required tests:**

- `binary_kl_bits(0.22, 0.105)` is approximately `0.0800`.
- one-term KL helper, if implemented, returns approximately `0.2348` for `0.22, 0.105` and is clearly labeled as not binary KL.
- `edge_roi(0.22, 0.105)` is approximately `1.095`.
- `kelly_fraction(0.22, 0.105)` is approximately `0.1285`.
- probabilities clamp away from `0` and `1`.

**Verification:**

```bash
pytest tests/test_kl_math.py -q
```

Expected: all pass.

**Commit:**

```bash
git add src/weather_kelly/edge/kl.py tests/test_kl_math.py
git commit -m "feat: add correct KL and Kelly math"
```

---

### Task 4: Add Polymarket Gamma discovery client

**Objective:** Discover active weather high-temperature events and markets.

**Files:**
- Create: `src/weather_kelly/polymarket/gamma.py`
- Create: `src/weather_kelly/polymarket/market_grouping.py`
- Create fixtures: `tests/fixtures/gamma_nyc_event.json`
- Test: `tests/test_gamma_client.py`

**Implementation requirements:**

Use public API only:

```text
GET https://gamma-api.polymarket.com/public-search?q=highest%20temperature%20in%20NYC
GET https://gamma-api.polymarket.com/events?slug=<event_slug>
```

Parse double-encoded fields:

- `outcomes`
- `outcomePrices`
- `clobTokenIds`

Do not trust `outcomePrices` for execution; store it as informational only.

**Verification:**

```bash
pytest tests/test_gamma_client.py -q
python -m weather_kelly.cli discover --city NYC --limit 5 --json
```

Expected: CLI prints active NYC high-temperature event candidates with event slug and market count.

**Commit:**

```bash
git add src/weather_kelly/polymarket tests/fixtures tests/test_gamma_client.py
git commit -m "feat: discover Polymarket weather events"
```

---

### Task 5: Implement temperature market parser

**Objective:** Convert market questions into exact bucket definitions.

**Files:**
- Create: `src/weather_kelly/parsing/temperature_market.py`
- Test: `tests/test_temperature_parser.py`

**Parser must support examples:**

```text
Will the highest temperature in New York City be 71°F or below on May 5?
Will the highest temperature in New York City be between 72-73°F on May 5?
Will the highest temperature in New York City be 74°F or higher on May 5?
Will the highest temperature in NYC be between 45-46°F on March 30?
```

**Parsed bucket model:**

```python
{
  "city": "NYC",
  "unit": "F",
  "date_text": "May 5",
  "kind": "range",      # one of: below_or_equal, range, above_or_equal, exact
  "low": 72,
  "high": 73
}
```

**Verification:**

```bash
pytest tests/test_temperature_parser.py -q
```

Expected: all example strings parse; unsupported phrasing raises a typed `UnsupportedMarketQuestion` error.

**Commit:**

```bash
git add src/weather_kelly/parsing tests/test_temperature_parser.py
git commit -m "feat: parse temperature bucket markets"
```

---

### Task 6: Add CLOB orderbook client and executable price model

**Objective:** Use best ask/depth for paper fills rather than stale midpoint/last price.

**Files:**
- Create: `src/weather_kelly/polymarket/clob.py`
- Create fixture: `tests/fixtures/clob_book_yes.json`
- Test: `tests/test_clob_client.py`

**Endpoints:**

```text
GET https://clob.polymarket.com/book?token_id=<YES_TOKEN>
GET https://clob.polymarket.com/midpoint?token_id=<YES_TOKEN>
GET https://clob.polymarket.com/spread?token_id=<YES_TOKEN>
```

**Orderbook helpers:**

- `best_bid()`
- `best_ask()`
- `spread()`
- `depth_usd_at_or_below(limit_price)`
- `simulate_market_buy(stake_usd, max_price)`

**Verification:**

```bash
pytest tests/test_clob_client.py -q
python -m weather_kelly.cli book --event highest-temperature-in-nyc-on-may-6-2026 --bucket '66-67F'
```

Expected: prints best bid, best ask, spread, top depth, and min order size.

**Commit:**

```bash
git add src/weather_kelly/polymarket/clob.py tests/test_clob_client.py tests/fixtures/clob_book_yes.json
git commit -m "feat: add CLOB orderbook execution model"
```

---

### Task 7: Add weather forecast provider interface

**Objective:** Make forecast data pluggable so we can compare providers without rewriting signal logic.

**Files:**
- Create: `src/weather_kelly/weather/providers/base.py`
- Create: `src/weather_kelly/weather/distribution.py`
- Create: `src/weather_kelly/weather/calibration.py`
- Test: `tests/test_distribution.py`

**Provider interface:**

```python
class ForecastProvider(Protocol):
    name: str

    def forecast_high_distribution(
        self,
        city: City,
        date_local: date,
        generated_at: datetime,
    ) -> TemperatureDistribution:
        ...
```

**Distribution requirements:**

- `cdf(x)`
- `prob_between(low, high, inclusive=True)`
- `prob_below_or_equal(x)`
- `prob_above_or_equal(x)`
- `bucket_probability(bucket)`

**Verification:**

```bash
pytest tests/test_distribution.py -q
```

Expected: bucket probabilities sum to approximately `1.0` across a full event bucket set.

**Commit:**

```bash
git add src/weather_kelly/weather tests/test_distribution.py
git commit -m "feat: add forecast provider interface and bucket distribution"
```

---

### Task 8: Implement NYC NWS calibrated forecast provider

**Objective:** Create a fast, reliable MVP weather model for NYC without heavy GRIB tooling.

**Files:**
- Create: `src/weather_kelly/weather/providers/nws.py`
- Create fixture: `tests/fixtures/nws_hourly_forecast.json`
- Test: `tests/test_nws_provider.py`

**Data source pattern:**

1. `GET https://api.weather.gov/points/{lat},{lon}`
2. Follow `forecastHourly` URL.
3. Extract hourly temperatures for target local date.
4. Compute forecast high.
5. Apply calibrated normal/Laplace error prior from config.

**Important:** This is v0. The implementation must label provider output as `nws_calibrated_normal_v0`, not pretend to be true GEFS ensemble probability.

**Verification:**

```bash
pytest tests/test_nws_provider.py -q
python -m weather_kelly.cli forecast --city NYC --date YYYY-MM-DD
```

Expected: prints forecast high, sigma, and bucket probabilities.

**Commit:**

```bash
git add src/weather_kelly/weather/providers/nws.py tests/test_nws_provider.py tests/fixtures/nws_hourly_forecast.json
git commit -m "feat: add NYC NWS calibrated forecast provider"
```

---

### Task 9: Add Open-Meteo fallback provider for non-US later

**Objective:** Prepare Phase 2 city expansion without blocking NYC v0.

**Files:**
- Create: `src/weather_kelly/weather/providers/open_meteo.py`
- Test: `tests/test_open_meteo_provider.py`

**Rules:**

- Disabled by default for paper trading unless config explicitly enables it.
- Output provider name must include `fallback`.
- Signals generated from fallback provider should be tagged `provider_confidence: experimental`.

**Verification:**

```bash
pytest tests/test_open_meteo_provider.py -q
```

Expected: adapter parses fixture and creates a distribution.

**Commit:**

```bash
git add src/weather_kelly/weather/providers/open_meteo.py tests/test_open_meteo_provider.py
git commit -m "feat: add experimental global forecast fallback"
```

---

### Task 10: Add NOAA GEFS provider skeleton and research gate

**Objective:** Keep the repo honest about the true target: ensemble forecast distributions.

**Files:**
- Create: `src/weather_kelly/weather/providers/noaa_gefs.py`
- Create: `docs/noaa-gefs-provider-notes.md`
- Test: `tests/test_noaa_gefs_provider.py`

**Scope for v0:**

- Implement provider class and config hooks.
- Add tests around fixture parsing if a small sample fixture is practical.
- If GRIB tooling is not installed, provider should fail gracefully with `ProviderUnavailable`.
- Do not block paper v0 on heavy GEFS extraction.

**Verification:**

```bash
pytest tests/test_noaa_gefs_provider.py -q
python -m weather_kelly.cli forecast --provider noaa-gefs --city NYC --date YYYY-MM-DD
```

Expected if dependencies missing: clean `ProviderUnavailable` with remediation message, not stack trace.

**Commit:**

```bash
git add src/weather_kelly/weather/providers/noaa_gefs.py docs/noaa-gefs-provider-notes.md tests/test_noaa_gefs_provider.py
git commit -m "feat: scaffold NOAA GEFS provider"
```

---

### Task 11: Implement signal generation

**Objective:** Combine event buckets, executable asks, model probabilities, overround normalization, edge, KL, and sizing inputs.

**Files:**
- Create: `src/weather_kelly/edge/signal.py`
- Create: `src/weather_kelly/edge/sizing.py`
- Test: `tests/test_signal_generation.py`

**Signal gate requirements:**

Reject if any are true:

- market closed or inactive
- missing YES token
- parser cannot identify bucket
- forecast provider unavailable
- resolution confidence below config threshold
- best ask missing
- spread greater than config `max_spread`
- depth below `min_depth_usd`
- event exposure cap exceeded
- `edge_abs < min_edge_abs`
- `edge_roi < min_edge_roi`
- `binary_kl_bits < min_binary_kl_bits`

Size stake as:

```text
stake = min(
  max_stake_per_market_usd,
  remaining_event_exposure_usd,
  remaining_daily_exposure_usd,
  bankroll_usd * fractional_kelly * kelly_fraction,
  depth_limited_stake_usd
)
```

**Verification:**

```bash
pytest tests/test_signal_generation.py -q
python -m weather_kelly.cli scan --config configs/paper.yaml --city NYC --write
```

Expected: writes `data/signals/latest.json`; zero-signal file still has fresh timestamp.

**Commit:**

```bash
git add src/weather_kelly/edge tests/test_signal_generation.py
git commit -m "feat: generate executable weather edge signals"
```

---

### Task 12: Implement paper ledger and simulated executor

**Objective:** Turn signals into auditable paper fills without live side effects.

**Files:**
- Create: `src/weather_kelly/paper/ledger.py`
- Create: `src/weather_kelly/paper/executor.py`
- Create: `src/weather_kelly/paper/portfolio.py`
- Test: `tests/test_paper_ledger.py`

**Rules:**

- Append-only ledger JSONL.
- Deduplicate by `signal_id` unless the signal explicitly allows multiple fills.
- Simulate fill against CLOB ask depth.
- Charge fee assumption.
- Track open positions by market slug + side.
- Never import or call live trading libraries.

**Verification:**

```bash
pytest tests/test_paper_ledger.py -q
python -m weather_kelly.cli paper-tick --config configs/paper.yaml
python -m weather_kelly.cli portfolio --config configs/paper.yaml
```

Expected: paper fills append to `data/paper/ledger.jsonl`; portfolio summary prints bankroll, open exposure, realized/unrealized paper P&L.

**Commit:**

```bash
git add src/weather_kelly/paper tests/test_paper_ledger.py
git commit -m "feat: add paper execution ledger"
```

---

### Task 13: Implement settlement resolver and scoreboard

**Objective:** Evaluate paper trades against resolved market outcomes.

**Files:**
- Create: `src/weather_kelly/settlement/resolver.py`
- Create: `src/weather_kelly/settlement/scoreboard.py`
- Test: `tests/test_settlement_scoreboard.py`

**Resolution source order:**

1. Polymarket market closed/resolved state and final outcome price from Gamma/CLOB.
2. Data API closed positions style fields if available for similar market metadata.
3. Weather station observations only as diagnostic, not final payout authority, until resolution source is proven.

**Metrics:**

- settled trades
- win rate
- gross win/loss
- profit factor
- total cost
- ROI on cost
- average/median P&L
- Brier score vs market
- log loss vs market
- P&L by bucket type and city

**Verification:**

```bash
pytest tests/test_settlement_scoreboard.py -q
python -m weather_kelly.cli settle --config configs/paper.yaml
python -m weather_kelly.cli report --config configs/paper.yaml
```

Expected: writes `data/settlement/scoreboard.csv` and `data/reports/latest.md`.

**Commit:**

```bash
git add src/weather_kelly/settlement tests/test_settlement_scoreboard.py
git commit -m "feat: settle paper trades and score edge"
```

---

### Task 14: Add CLI commands and rich summaries

**Objective:** Make the project operable from terminal and future cron/systemd.

**Files:**
- Create/modify: `src/weather_kelly/cli.py`
- Create: `src/weather_kelly/logging_utils.py`
- Create: `src/weather_kelly/timeutils.py`
- Test: `tests/test_cli_smoke.py`

**Commands:**

```bash
weather-kelly discover --city NYC --limit 5
weather-kelly forecast --city NYC --date YYYY-MM-DD
weather-kelly scan --config configs/paper.yaml --city NYC --write
weather-kelly paper-tick --config configs/paper.yaml
weather-kelly portfolio --config configs/paper.yaml
weather-kelly settle --config configs/paper.yaml
weather-kelly report --config configs/paper.yaml
```

**Verification:**

```bash
pytest tests/test_cli_smoke.py -q
weather-kelly --help
```

Expected: all commands show help and do not crash without network in fixture mode.

**Commit:**

```bash
git add src/weather_kelly/cli.py src/weather_kelly/logging_utils.py src/weather_kelly/timeutils.py tests/test_cli_smoke.py
git commit -m "feat: add weather kelly CLI"
```

---

### Task 15: Add minimal operator dashboard

**Objective:** Provide fast visibility into signals, fills, exposure, and score without overbuilding.

**Files:**
- Create: `src/weather_kelly/dashboard/app.py`
- Modify: `pyproject.toml` optional extra `dashboard`
- Test: `tests/test_dashboard_smoke.py`

**MVP dashboard content:**

- Latest scan timestamp
- Signal count
- Top 10 signals by edge ROI
- Open paper positions
- Event exposure
- Settled P&L summary
- Provider status and warnings

**Implementation option:** Use a simple static HTML/Markdown report first. Only add Streamlit/FastAPI if the static report feels insufficient.

**Verification:**

```bash
python -m weather_kelly.cli report --config configs/paper.yaml --html data/reports/latest.html
```

Expected: `data/reports/latest.html` exists and opens locally.

**Commit:**

```bash
git add src/weather_kelly/dashboard tests/test_dashboard_smoke.py
git commit -m "feat: add operator dashboard report"
```

---

### Task 16: Add paper loop script

**Objective:** Run the bot for 48h in paper mode with recoverable logs.

**Files:**
- Create: `scripts/run_paper_loop.sh`
- Create: `scripts/summarize_paper.py`
- Modify: `README.md`

**Script behavior:**

- Activate venv.
- Run `scan` then `paper-tick` every 5 minutes.
- Run `settle` and `report` every hour.
- Append logs to `data/logs/paper-loop.log`.
- Exit on unhandled crash so process manager can restart.

**Verification:**

```bash
bash scripts/run_paper_loop.sh --once
```

Expected: one full paper tick completes; artifacts are created under `data/`.

**Commit:**

```bash
git add scripts README.md
git commit -m "feat: add paper loop runner"
```

---

### Task 17: Add final integration and packaging smoke

**Objective:** Prove the repo works from a fresh install and does not rely on local accidents.

**Verification commands:**

```bash
cd /root/projects/weather-kelly-trader
python3 -m venv /tmp/weather-kelly-smoke-venv
. /tmp/weather-kelly-smoke-venv/bin/activate
pip install -e '.[dev]'
weather-kelly --help
weather-kelly scan --config configs/paper.yaml --city NYC --write
weather-kelly paper-tick --config configs/paper.yaml
weather-kelly report --config configs/paper.yaml
pytest -q
ruff check .
```

Expected:

- CLI works from fresh venv.
- No package discovery failure from ignored `data/` dir.
- Tests pass.
- Report generated.

**Commit:**

```bash
git add .
git commit -m "test: verify end-to-end paper trading smoke"
```

---

### Task 18: Optional GitHub repo creation

**Objective:** Push the new repo to GitHub only after local tests pass.

**Preferred:** private repo first.

```bash
cd /root/projects/weather-kelly-trader
gh repo create weather-kelly-trader --private --source . --push --description "Paper-only Polymarket weather edge scout"
```

Fallback if `gh` is not available: use `GITHUB_TOKEN` + GitHub API as documented in `github-repo-management` skill.

**Verification:**

```bash
git remote -v
gh repo view weather-kelly-trader
```

Expected: remote exists, repo pushed.

**Commit:** already committed locally; push only.

---

## 48-hour paper trading runbook

### Pre-run gate

Do not start 48h paper run until all are true:

- `pytest -q` passes
- `ruff check .` passes
- `weather-kelly scan --write` creates fresh `data/signals/latest.json`
- zero-signal behavior verified
- no live trading code exists
- config says `mode: paper`
- dashboard/report shows current timestamp and provider name

### Day 0: build and dry run

- Implement Tasks 0–17.
- Run one manual paper tick.
- Inspect every generated signal manually.
- If any signal has wrong city/date/unit/bucket, stop and fix parser before running loop.

### Day 1: first unattended paper loop

- Start loop in foreground or supervised background.
- Check after 30 minutes:
  - fresh scan timestamps
  - no stale signal reuse
  - no duplicate fills
  - no unexpected high exposure
- Do not tune thresholds intraday unless there is a bug. Changing thresholds mid-run corrupts the experiment.

### Day 2: second paper day and first evaluation

- Continue same config.
- Run settlement/report hourly.
- Produce `data/reports/48h-paper-review.md` with:
  - number of signals
  - number of fills
  - open exposure
  - settled P&L
  - unresolved P&L marked separately
  - log-loss/Brier comparison vs market where possible
  - parser/provider failures

---

## Success metrics and willingness-to-pay signals

For this internal experiment, success means evidence good enough to keep investing engineering time.

48h success signals:

- Parser correctly handles `>=95%` of NYC active high-temp bucket questions.
- At least one full event is scanned, signaled, paper-filled or explicitly rejected with transparent reasons.
- No stale artifacts or duplicate fills.
- Report can explain why each signal fired or did not fire.
- If trades settle, realized P&L is non-negative after simulated fees; if not enough settled trades, log-loss/Brier improves over market-implied distribution.

Longer-run success signals:

- At least `30` settled paper trades.
- Profit factor `>1.5` after spread/fee simulation.
- Positive ROI on cost.
- Brier/log-loss better than market on settled events.
- Edge persists after removing the top 1 outlier win.

Willingness-to-pay signals if productized later:

- A trader asks for alerts before live market move.
- A trader wants API/webhook access to signals.
- A copy-trading user asks for audited historical paper/live performance.
- Someone pays for a weather market dashboard even without auto-execution.

---

## Business model experiments, only after evidence

Do not monetize v0. If paper evidence becomes real:

1. Private Telegram alert feed for weather-market signals.
2. Paid dashboard with signal history, edge decomposition, and post-settlement scorecards.
3. API/webhook for traders.
4. Eventually managed paper-to-live strategy, but only after legal/geographic/trading-risk review.

---

## Risks, tradeoffs, and mitigations

### Risk: wrong resolution source

A model can predict Central Park while Polymarket resolves on a different station/source.

Mitigation:

- Parse market description.
- Store `resolution_confidence`.
- No trade if low confidence.
- Use Polymarket outcome as final settlement truth.

### Risk: forecast model is too weak

A deterministic NWS forecast plus normal error prior may not beat market.

Mitigation:

- Label provider honestly.
- Compare providers.
- Add NOAA GEFS true ensemble provider after MVP.
- Judge by log-loss/Brier, not vibe.

### Risk: tail buckets look amazing but are fake edge

Low-price tails produce huge ROI claims and lots of -100% losses.

Mitigation:

- Minimum probability floor.
- Depth/spread gates.
- Fractional Kelly cap.
- Report performance with and without top outlier.

### Risk: overfitting to WeatherTraderBot history

We can accidentally copy only winning examples.

Mitigation:

- Forward paper only.
- Do not tune after seeing same-day outcomes.
- Keep immutable run config hashes in reports.

### Risk: stale signals trigger fake fills

Mitigation:

- Always write zero-signal artifact.
- Include timestamp freshness checks.
- Deduplicate by `signal_id`.

### Risk: live-trading creep

Mitigation:

- No wallet code in v0.
- Tests assert live-order terms are absent or disabled.
- Separate explicit plan required for live execution.

---

## Kill criteria

Stop or pivot if any of these happen:

- Parser cannot confidently parse active NYC high-temp markets after one implementation pass.
- Forecast provider is unavailable or stale during market windows for two consecutive days.
- After `30+` settled paper trades, profit factor is `<1.1` or ROI on cost is negative.
- Log-loss/Brier does not beat normalized market probabilities after enough settled events.
- Positive P&L disappears when the single best trade is removed.
- Average executable spread/fee consumes more than half the modeled edge.
- We discover market resolution is systematically mismatched with our weather source.

---

## Open questions and next irreversible decision

Open questions:

- What exact source does each NYC Polymarket high-temp market use for resolution?
- Should NYC use KNYC/Central Park, another station, or Polymarket’s own adjudication source?
- Is NWS calibrated normal good enough, or do we need true GEFS immediately?
- How often do these markets close before official resolution, causing stale CLOB states?
- Is there enough depth at mispriced asks for more than toy size?

Next irreversible decision:

- After the local repo passes smoke tests, decide whether to run a 48h paper loop continuously and freeze the config for the full experiment. Once the paper run starts, do not tune thresholds until the review window ends.

---

## Final execution gate

When leaving plan mode, execute in this order:

1. Create `/root/projects/weather-kelly-trader`.
2. Implement Tasks 0–17 with tests and commits.
3. Run one manual dry paper tick.
4. Review generated signals manually.
5. If clean, start 48h paper loop.
6. After 48h, produce `data/reports/48h-paper-review.md` and decide keep/kill/pivot.
