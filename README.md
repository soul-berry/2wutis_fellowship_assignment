# Volatility‑Regime Adaptive Intraday Momentum (Python Trading System)

This project implements and extends an intraday momentum strategy for SPY in Python. The goal is to turn the research model into a realistic, end‑to‑end trading system with:

- Clean, modular code.
- Historical backtesting on minute data.
- Integration with the Alpaca API for data and (paper) order submission.

The strategy trades intraday on a highly liquid US ETF (SPY) using a **volatility‑regime adaptive breakout**:

- Compute prior‑day realized volatility.
- Standardize it using a rolling z‑score.
- Adapt the breakout band multiplier \(k\) and position size as functions of the volatility regime.
- Generate a single “first‑touch” intraday signal per day and close all positions by the end of the session.
- Include realistic transaction costs and position size caps.

---

## 1. Repository structure

The current structure focuses on a single adaptive strategy, backtesting, and a minimal Alpaca integration:

```text
.
├── README.md
├── requirements.txt
├── .env                # your Alpaca keys (not committed)
├── output/             # backtest results (CSV files)
├── src/
│   ├── data/
│   │   ├── transforms.py       # feature engineering for intraday data
│   │   └── alpaca_client.py    # historical data + order submission via Alpaca
│   ├── strategy/
│   │   └── adaptive_vol_regime.py   # core strategy class
│   ├── backtest/
│   │   ├── backtester.py       # backtest runner utilities
│   │   └── metrics.py          # performance metric calculations
│   └── trading/
│       └── live_trader.py      # minimal live/paper trading loop
├── tests/
│   ├── test3.py                # thin script to run backtests on local CSV
│   └── ...                     # other experimental/test scripts
├── run_backtest_alpaca.py      # end‑to‑end backtest using Alpaca historical data
└── run_live_trader.py          # live/paper trading demo using Alpaca
```

- `src/strategy`: strategy logic (adaptive volatility‑regime intraday breakout).
- `src/data`: data ingestion (Alpaca client) and feature engineering.
- `src/backtest`: backtest runner and performance metrics.
- `src/trading`: minimal live trading loop for Alpaca paper trading.
- `output/`: generated CSVs with daily PnL, equity curves, and parameter grid results.

---

## 2. Setup and installation

### 2.1. Clone repository

```bash
git clone <your-repo-url>.git
cd intraday-momentum-system
```

### 2.2. Create virtual environment

On Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2.3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configuration and API keys

The project uses environment variables for Alpaca configuration, loaded from a `.env` file.

1. Create a free **Alpaca paper trading** account.
2. In the Alpaca dashboard, generate an **API Key ID** and **Secret Key** (paper account).
3. Create a `.env` file in the project root with:

```env
ALPACA_API_KEY=your_api_key_id_here
ALPACA_SECRET_KEY=your_secret_key_here
```

The file `src/data/alpaca_client.py` uses `python-dotenv` to load this `.env` so keys are available via `os.environ`.

---

## 4. How the system works

### 4.1. Data ingestion and features

- Historical minute bars are fetched from Alpaca’s Market Data API (or loaded from an existing CSV).
- Data is normalized into a standard schema with:
  - `timestamp`, `date`, `time`, `minute`,
  - `open`, `high`, `low`, `close`, `volume`.
- `src/data/transforms.py` computes intraday features:
  - log returns,
  - minute‑of‑day index,
  - move from session open,
  - rolling intraday “noise” profile.

These features are the inputs to the strategy.

### 4.2. Strategy logic (AdaptiveVolRegimeStrategy)

`src/strategy/adaptive_vol_regime.py` defines the main strategy class:

- **Volatility regime estimation**
  - Compute prior‑day realized volatility from intraday returns.
  - Standardize via a rolling window to obtain a volatility z‑score.
  - Compute an adaptive breakout multiplier \(k_{\text{adaptive}}\) as a function of \(k_{\text{base}}\), \(\lambda\), and the z‑score.
- **Noise bands and signals**
  - Use the rolling intraday “noise” profile to build upper and lower bands around the open.
  - Generate a raw signal when price first breaches these bands.
  - Use a **first‑touch per day** rule: only the first breach leads to an entry.
  - Force flat position by the market close.
- **Position sizing and risk controls**
  - Position size scales inversely with recent volatility, capped at `max_size`.
  - Additional volatility cap further reduces size on extreme days.
  - A time‑of‑day filter restricts entries to a fixed intraday window (e.g. 10:00–15:30).
- **Transaction costs**
  - `cost_bps` models costs per unit of traded notional.
  - Backtests compute trade size changes per day and subtract costs from returns.

The method `run(self, df)` takes a prepared intraday DataFrame and returns:

- `data_ext`: intraday data with positions and net returns per bar,
- `daily_rv`: daily volatility and position size information,
- `train_dates` and `test_dates`: date lists for train/test split.

---

## 5. Backtesting

### 5.1. Components

- `src/backtest/backtester.py`:
  - `load_historical_from_alpaca(symbol, start, end)` uses `AlpacaClient` to pull minute bars.
  - `run_backtest(df_raw, strategy)`:
    - Prepares features,
    - Runs the strategy,
    - Aggregates bar‑level returns to daily PnL.

- `src/backtest/metrics.py`:
  - `compute_performance_stats(daily_pnl)` returns:
    - mean daily PnL,
    - daily volatility,
    - annualized return,
    - annualized volatility,
    - Sharpe ratio (assuming 0 risk‑free rate).

### 5.2. Historical backtest using Alpaca

The script `run_backtest_alpaca.py` performs an end‑to‑end backtest:

1. Load historical minute data from Alpaca for a configured date range.
2. Instantiate `AdaptiveVolRegimeStrategy` with chosen parameters (e.g. `k_base=2.0`, `noise_window=15`, `train_ratio=0.7`, `cost_bps=1.0`).
3. Run `run_backtest` to get intraday outputs and daily PnL.
4. Split daily PnL into train and test using the dates from the strategy.
5. Compute performance metrics for overall, train, and test periods.
6. Save a CSV with:
   - `date`,
   - `daily_pnl`,
   - `equity_curve` (cumulative product of 1 + daily PnL).

#### How to run the Alpaca backtest

From the project root (with `.venv` activated and `.env` configured):

```bash
python run_backtest_alpaca.py
```

The script prints summary metrics and writes:

- `output/daily_pnl_equity_alpaca.csv`

You may also have local‑CSV‑based runners under `tests/` (e.g. `test3.py`) that:

- Load pre‑saved `output/historical_bars.csv`,
- Run the same strategy and metric pipeline,
- Save `output/daily_pnl_equity.csv` and one‑row metric tables for specific parameter combinations.

---

## 6. Live / paper trading

### 6.1. Live trader design

`src/trading/live_trader.py` contains a minimal **polling‑based** live trader:

- Uses `AlpacaClient` to repeatedly fetch the latest minute bars for the configured symbol.
- Rebuilds today’s intraday DataFrame and features.
- Calls `AdaptiveVolRegimeStrategy.run` to obtain the latest desired position.
- Compares desired position to current position and computes a delta.
- Logs the intended trade and, if enabled, sends a paper market order via Alpaca.

This loop is intentionally simple: it demonstrates how the model can be wired into a real‑time trading API without aiming for a production‑grade execution engine.

### 6.2. Running the live demo (paper)

US market hours (09:30–16:00 ET) correspond roughly to **15:30–22:00 CET** for you. Run the live script only during those hours so minute bars are available.

From the project root:

```bash
python run_live_trader.py
```

Recommended workflow:

1. Ensure `.env` is configured with Alpaca **paper** keys.
2. Run `run_live_trader.py` with **order submission commented out** in `send_orders`, so it only logs target positions and intended trades.
3. Observe the console logs (roughly once per minute):
   - Latest target position,
   - Current position,
   - Whether an order would be submitted.
4. When confident, uncomment the `submit_market_order` call to actually place paper trades.

**Important:** this live loop is for demonstration and learning only. It does not handle all failure modes, connectivity issues, or regulatory constraints.

---

## 7. Assumptions, limitations, and future work

**Key assumptions**

- Strategy trades one highly liquid US ETF (SPY) to minimize slippage and market impact.
- Transaction costs are modeled as simple basis‑point charges per traded notional.
- All positions are closed by the end of the regular session (no overnight risk).
- Train/test split is time‑based, using an early period for calibration and a later period for evaluation.

**Limitations**

- Slippage, partial fills, and detailed microstructure effects are simplified.
- Single‑asset focus; no portfolio‑level risk management or capital allocation across multiple strategies.
- Live trading is implemented as a simple polling loop, not a robust streaming/production framework.
- Parameter sensitivity exists; the edge is small and fragile to higher costs and different regimes, as shown by the parameter grid experiments.

**Possible future extensions**

- Introduce a baseline strategy module and compare directly with the adaptive strategy (same infrastructure).
- More realistic execution modeling (limit orders, participation constraints).
- Multi‑asset portfolio and cross‑sectional signals.
- Additional broker adapters (IBKR, Lynx) and pluggable data providers.
- Containerization (Docker) and simple cloud deployment for scheduled backtests or always‑on paper trading.

---

## 8. How to review this project

If you are reviewing this repository:

1. Start with `README.md` to understand high‑level design and assumptions.
2. Inspect `src/strategy/adaptive_vol_regime.py` for the core trading logic.
3. Look at `src/data/transforms.py` to see how intraday features are defined.
4. Check `src/backtest/backtester.py` and `metrics.py` for backtesting and performance evaluation.
5. Review `src/data/alpaca_client.py` and `src/trading/live_trader.py` to see how the system connects to Alpaca for historical and live data.

This setup demonstrates a realistic path from research model to a basic, API‑integrated trading system suitable for discussion in the fellowship assignment.