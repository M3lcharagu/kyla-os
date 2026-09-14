# R3 TEMPERANTIA trading module

## Paper-only
This is **paper-only**. It reads MT5 data and simulates trades; no live orders are sent and the code never calls `mt5.order_send()`.

## Files
- `mt5_connector.py`: MT5 initialize/login, symbol selection/info, ticks, and timezone-converted OHLCV rates.
- `signals.py`: causal ATR/EMA/candle/FVG features and closed-candle signals.
- `risk.py`: risk-based sizing, sessions, daily/weekly guards, realized PnL and status.
- `backtest.py`: CSV loader and bar-by-bar, next-open, one-position backtest with JSON results.
- `paper_trader.py`: read-only polling loop, simulated entries/exits, status and interrupt summary.
- `config.yaml`: complete JSON-compatible YAML settings.

## ICT-ish signal logic
A long needs a sweep of the prior `sweep_lookback` lows and a close back above them, a bullish three-candle FVG (`current low > high two candles back`), close above EMA, minimum body ratio, and a close in the upper `min_close_location` of the candle. A short reverses these conditions with prior highs, bearish FVG, close below EMA, and a lower close location. The stop is beyond the signal candle by `stop_buffer_points` (scaled by the instrument point). ATR/EMA and all filters use only the evaluated closed candle and history. Entry is the following bar open, so no future data is used.

## Install and prepare MT5
```bash
pip install MetaTrader5 pandas
```
Install/login to the desktop MT5 terminal, enable the broker's symbols, and keep it running. Broker suffixes (for example `XAUUSDm`) may require adapting the symbol/config. Optional environment variables are `MT5_PATH`, `MT5_LOGIN`, `MT5_PASSWORD`, and `MT5_SERVER`.

## Backtest
Export/save MT5 OHLC data as CSV with `time,open,high,low,close` (a `datetime` or `date` column is also accepted), then run:
```bash
python trading/backtest.py --csv data/XAUUSD_M5.csv --symbol XAUUSD --config trading/config.yaml --output result.json
```
The CSV timezone is treated as configured (or converted to it); the output includes trades, win rate, profit factor, max drawdown, equity curve and related statistics.

## Paper trader
```bash
python trading/paper_trader.py --symbol XAUUSD --config trading/config.yaml
```
The loop polls the latest closed candle and simulates the next-bar-open entry. It tracks one paper trade, exits at stop/target/session end, prints status, and on Ctrl+C exits at current bid for a long or ask for a short, prints a summary, and disconnects. It never sends a live order.

## Risk and caveats
The session is Mon-Thu, 08:00-18:00 in `Africa/Nairobi`, with at most 3 trades/day, a $100 realized daily-loss guard, a $150 weekly target lock, and $50 weekly trailing-drawdown protection. Sizing uses MT5 `trade_tick_size`/`trade_tick_value` when available; backtests use the configured cash-per-price-unit-per-lot fallback. Confirm broker tick values, point sizes, volume min/max/step, symbol names, timezone, and cash fallback before relying on any result. Configuration is JSON-compatible YAML so the scripts need only Python standard library plus pandas and MetaTrader5.
