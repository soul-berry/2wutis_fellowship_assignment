
# Volatility‑Regime Adaptive Intraday Momentum (Python Trading System)

This project is a Python re‑implementation and extension of my original R case study on intraday SPY momentum. The goal is to turn the research model into a realistic end‑to‑end trading system with proper architecture, live broker integration, and deployment readiness.

## 1. Project overview

The strategy trades intraday on highly liquid US securities (e.g. SPY) using a **volatility‑regime adaptive breakout**:

- Compute prior‑day realized volatility.
- Standardize it using a rolling z‑score.
- Adapt the breakout band and position size as a function of the volatility regime.
- Generate first‑touch intraday signals and close all positions at the end of the session.
- Include transaction costs and realistic constraints.

This repository contains:

- Clean, modular Python code.
- Historical backtesting using broker data.
- Paper‑trading integration via Alpaca’s API.
- Containerization with Docker and a minimal cloud deployment setup.

***

## 2. Repository structure

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── config/
│   └── settings.yaml
├── data/
│   ├── raw/          # ignored, downloaded historical data
│   └── cache/        # ignored, intermediate caches
├── notebooks/
│   └── 01_research_parity.ipynb
├── src/
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   └── schemas.py
│   ├── data/
│   │   ├── base.py
│   │   ├── alpaca_provider.py
│   │   └── transforms.py
│   ├── strategy/
│   │   ├── baseline_intraday.py
│   │   └── adaptive_vol_regime.py
│   ├── backtest/
│   │   ├── engine.py
│   │   ├── metrics.py
│   │   └── plots.py
│   ├── execution/
│   │   ├── broker.py
│   │   ├── alpaca_broker.py
│   │   └── order_router.py
│   └── live/
│       ├── stream.py
│       └── runner.py
└── tests/
    ├── test_metrics.py
    ├── test_strategy_logic.py
    └── test_data_pipeline.py
```

- `src/strategy`: strategy logic (baseline + adaptive).
- `src/data`: data ingestion and feature engineering.
- `src/backtest`: backtesting, portfolio metrics, and plots.
- `src/execution`: order routing and broker integration.
- `src/live`: real‑time data streaming and live/paper trading runner.

***

## 3. Setup and installation

### 3.1. Clone repository

```bash
git clone <your-repo-url>.git
cd intraday-momentum-system
```

### 3.2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows
```

### 3.3. Install dependencies

```bash
pip install -r requirements.txt
```

***

## 4. Configuration and API keys

The project uses environment variables for broker/API configuration.

1. Create a free **Alpaca paper trading** account.
2. In the Alpaca web dashboard, generate an **API Key ID** and **Secret Key** for the paper account.
3. Copy `.env.example` to `.env` and fill in your values:

```env
ALPACA_API_KEY=your_api_key_id_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

`config/settings.yaml` contains non‑secret configuration such as:

- default symbol (e.g. SPY),
- historical data date range,
- bar timeframe,
- train/test split,
- strategy hyperparameters (base k, lambda, windows, max leverage).

***

## 5. How the system works

### 5.1. Data ingestion

- Historical minute bars are fetched from Alpaca’s Market Data API.
- Data is normalized into a standard schema: timestamp, open, high, low, close, volume.
- Intraday features are computed:
  - log returns,
  - minute‑of‑day index,
  - move from session open,
  - rolling intraday “noise” profile.

### 5.2. Strategy logic

There are two main strategies:

1. **Baseline intraday momentum**  
   - Fixed breakout band around open based on average historical intraday noise.  
   - Single first‑touch entry per day, flat at close.  

2. **Adaptive volatility‑regime strategy**  
   - Prior‑day realized volatility is standardized with a rolling z‑score.  
   - Breakout multiplier \(k\) and position size are functions of the current volatility regime.  
   - Higher volatility → wider band and smaller position.  
   - Lower volatility → narrower band and larger position.  

Both strategies:

- use only information available before the trading day to avoid look‑ahead bias,
- incorporate transaction costs and position size caps.

### 5.3. Backtesting

- A backtest engine runs the strategy over historical bars.
- Daily returns are aggregated for:
  - baseline strategy,
  - adaptive strategy,
  - buy‑and‑hold benchmark.
- Reported metrics include:
  - annualized return,
  - annualized volatility,
  - Sharpe ratio,
  - max drawdown,
  - hit rate, turnover, and others as needed.
- Plots (equity curves, drawdowns, rolling Sharpe, regime diagnostics) are generated into `output/`.

***

## 6. Running the project

### 6.1. End‑to‑end backtest (historical)

From the project root:

```bash
python -m src.main
```

`src/main.py` performs:

1. Load config and environment variables.
2. Download or load historical market data.
3. Run baseline and adaptive strategies.
4. Compute and print summary metrics.
5. Save plots and artifacts to `output/`.

### 6.2. Live/paper trading

The live runner uses Alpaca’s streaming and trading APIs in paper mode.

```bash
python -m src.live.runner
```

Typical live loop:

1. Subscribe to real‑time minute bars for the configured symbol.
2. Maintain intraday state and current position.
3. When a breakout condition is met, send a paper market order via the broker interface.
4. Close all positions by the defined session end time.

**Warning:** this is intended for paper trading / demo only; the code is not production‑hardened and does not handle all edge cases, failures, or regulatory constraints.

***

## 7. Docker and deployment

### 7.1. Build image

```bash
docker build -t intraday-momentum .
```

### 7.2. Run locally

```bash
docker run --env-file .env intraday-momentum
```

This launches the same backtest pipeline inside a container, demonstrating that the project is reproducible and portable.

### 7.3. Cloud deployment

The container can be deployed to any simple container hosting platform (e.g. Render, Railway, Azure App Service, a small VM). A minimal deployment only needs:

- the built image,
- environment variables for Alpaca,
- a command similar to `python -m src.main` or the live runner.

***

## 8. Testing

Basic tests are provided under `tests/`:

- `test_metrics.py`: sanity checks for performance metric calculations.
- `test_strategy_logic.py`: checks core signal logic for simple synthetic scenarios.
- `test_data_pipeline.py`: validates basic assumptions on data formatting and feature engineering.

Run all tests:

```bash
pytest
```

***

## 9. Assumptions, limitations, and future work

**Key assumptions**

- Strategy trades highly liquid US instruments (e.g. SPY) to minimize slippage and market impact.
- Transaction costs are modeled as fixed basis‑point charges per traded notional.
- All positions are closed at the end of the session (no overnight risk).

**Limitations**

- Slippage and partial fills are simplified.
- No portfolio‑level risk management (single‑asset focus).
- Live trading is designed for paper accounts; reliability and monitoring are minimal.

**Possible extensions**

- Multi‑asset portfolio with risk budgeting and cross‑sectional signals.
- More realistic execution modeling (limit orders, queue position, volume constraints).
- Higher‑frequency data and microstructure‑aware intraday models.
- Additional broker adapters (IBKR, Lynx) and pluggable data providers.
- Web UI or dashboard for monitoring live performance.

***

## 10. How to read this project

If you are reviewing this repository:

1. Start with `README.md` and `config/settings.yaml` to understand high‑level design.
2. Look at `src/strategy/baseline_intraday.py` and `adaptive_vol_regime.py` for the core trading logic.
3. Inspect `src/backtest/engine.py` and `metrics.py` to see how performance is evaluated.
4. Review `src/data/alpaca_provider.py` and `execution/alpaca_broker.py` to understand how the system connects to real APIs.
5. Open `notebooks/01_research_parity.ipynb` for a more exploratory explanation of how the Python implementation reproduces and extends the original R case study.

***

