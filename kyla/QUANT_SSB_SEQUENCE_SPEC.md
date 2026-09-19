# S/B Sequence Scalping Specification

> **Status: HYPOTHESIS / RESEARCH SPECIFICATION.** This document makes the S/B sequence idea deterministic and backtestable; it is not evidence of profitability, financial advice, or a live-trading instruction. There is no guaranteed 2:1 outcome.
>
> **Repository fit:** this is a research specification for the existing `kyla/` quant work. It does not modify the existing notes, journal, or strategy examples.

## 1. Scope and configuration

The system operates on closed **1-minute or 5-minute candles** and uses only closed **15-minute and 1-hour candles** for bias. The same rules must be run separately for `XAUUSD` and `SOL` with venue-specific data and costs.

```yaml
base_timeframe: [1m, 5m]
bias_timeframes: [15m, 1h]
ema_fast: 21
ema_slow: 55
atr_period: 14
volume_period: 20
volume_confirmation: optional
volume_multiplier: 1.20
body_to_range_min: 0.35
wick_to_body_min: 1.25
close_location_long_min: 0.65
close_location_short_max: 0.35
bias_slope_lookback: 3
trend_separation_atr: 0.25
flat_slope_atr: 0.10
stop_buffer_atr: 0.10
full_trade_risk: 1.00R
probe_trade_risk: 0.25R       # sensitivity: 0.30R
full_target: +1.00R
auto_stop: -1.00R
probe_target: +0.25R
hard_time_exit_minutes: 43    # sensitivity run: 45; never exceed configured cap
cooldown_bars_after_exit: 1
cycle_signal_window_minutes: 90
cycle_max_duration_minutes: 120
```

`R` is the initial monetary risk of a full-size trade, including the stop distance but before transaction costs. The stop price is fixed at entry; a stop may not be widened. Any parameter change is a separate, pre-registered research run, not a live adjustment.

## 2. Deterministic candle features and S/B signals

For every completed base candle `t`, calculate:

- `range = high_t - low_t`; reject a zero-range candle.
- `body = abs(close_t - open_t)`.
- `upper_wick = high_t - max(open_t, close_t)`.
- `lower_wick = min(open_t, close_t) - low_t`.
- `close_location = (close_t - low_t) / range`.
- `momentum_up = close_t > close_(t-1) and close_(t-1) >= close_(t-2)`.
- `momentum_down = close_t < close_(t-1) and close_(t-1) <= close_(t-2)`.
- `EMA21` and `EMA55` are calculated causally from base candles. The EMA at `t` uses data through `t` only.
- If volume is available and `volume_confirmation=true`, require `volume_t >= 1.20 * SMA(volume, 20)`; if unavailable, the observation is invalid for the volume-gated run, not silently substituted.

A candle is an **S (sell/bearish) signal** when all core conditions hold:

1. `close_t < open_t`.
2. `body / range >= 0.35`.
3. `upper_wick / body >= 1.25` (bearish rejection of higher prices).
4. `momentum_down=true`.
5. `close_t < EMA21_t < EMA55_t`.
6. `close_location <= 0.35`.
7. If the optional volume gate is enabled, the volume condition also holds.

A candle is a **B (buy/bullish) signal** when the exact mirror holds:

1. `close_t > open_t`.
2. `body / range >= 0.35`.
3. `lower_wick / body >= 1.25` (bullish rejection of lower prices).
4. `momentum_up=true`.
5. `close_t > EMA21_t > EMA55_t`.
6. `close_location >= 0.65`.
7. If the optional volume gate is enabled, the volume condition also holds.

A signal is evaluated only once, at the close of `t`. The entry is the next eligible base-bar open after modeled latency; never enter on the still-forming signal candle.

### USEFUL / SKIP contract

| Item | Flag | Rule in this specification |
|---|---|---|
| Close versus open | **USEFUL** | Required direction test for S/B. |
| Wick rejection | **USEFUL** | Required 1.25x body rejection test. |
| Momentum direction | **USEFUL** | Required two-step monotonic close test. |
| EMA alignment | **USEFUL** | Required EMA21/EMA55 order and price side. |
| Volume confirmation | **USEFUL (optional)** | Run as a declared gated variant; never mix gated and ungated results. |
| Closed 15m/1h bias | **USEFUL** | Required directional and regime filter. |
| Discretionary chart reading | **SKIP** | No visual override, subjective pattern label, or hindsight exception. |
| Unclosed candle values | **SKIP** | They are lookahead and cannot enter a backtest. |
| News/manual override | **SKIP** | It is a different, separately specified strategy. |

## 3. Higher-timeframe bias and regime

Resample from the venue's base candles using exchange/session timestamps. A 15m or 1h candle becomes available only after its close. At a base-bar decision time, use the most recently completed bias candle; never use its open, high, low, close, EMA, or ATR before completion.

For each bias timeframe `q` (`15m`, `1h`), calculate EMA20, EMA50, ATR14 and the three-candle EMA20 slope in price units:

- `UP_q` if `close_q > EMA20_q > EMA50_q` **and** `EMA20_q - EMA20_(q-3) >= 0.10 * ATR14_q`.
- `DOWN_q` if `close_q < EMA20_q < EMA50_q` **and** `EMA20_(q-3) - EMA20_q >= 0.10 * ATR14_q`.
- `FLAT_q` if `abs(EMA20_q - EMA20_(q-3)) <= 0.10 * ATR14_q` **and** `abs(EMA20_q - EMA50_q) <= 0.25 * ATR14_q`.
- Otherwise `TRANSITION_q`.

Combine the two timeframes deterministically:

- `TREND_UP` / long bias: `UP_15m` and `UP_1h`.
- `TREND_DOWN` / short bias: `DOWN_15m` and `DOWN_1h`.
- `RANGE`: `FLAT_15m` and `FLAT_1h`.
- `UNKNOWN`: every other combination, including disagreement, transition, missing history, or a not-yet-closed candle.

`UNKNOWN` is a no-trade state. Trending and ranging results must be reported separately; do not fold UNKNOWN into a profitable-looking regime.

## 4. Three-candle sequences and deterministic reading

A sequence is exactly three consecutive **eligible** signal candles with no non-signal candle between them. `SSS`, `BBB`, `BBS`, and `SSB` are recognized at the close of the third candle. A missing/invalid candle resets the sequence. The four sequence labels are retained even when a regime rule marks the setup SKIP.

| Sequence | Continuation reading (USEFUL only when exact rule holds) | Reversal/exhaustion reading (USEFUL only when exact rule holds) | Else |
|---|---|---|---|
| `SSS` | Short continuation only in `TREND_DOWN`; enter short next eligible bar. | **SKIP**; no discretionary reversal interpretation for three S signals. | **SKIP**. |
| `BBB` | Long continuation only in `TREND_UP`; enter long next eligible bar. | **SKIP**; no discretionary reversal interpretation for three B signals. | **SKIP**. |
| `BBS` | Long continuation only in `TREND_UP` when the third S is a pullback: `close_3 >= EMA21_3`, `lower_wick_3/body_3 >= 1.25`, and `close_location_3 >= 0.50`; enter long next eligible bar. | Short exhaustion/reversal only in `RANGE` when `close_3 < EMA21_3` and `close_3 < close_2`; enter short next eligible bar. | **SKIP**. |
| `SSB` | Short continuation only in `TREND_DOWN` when the third B is a pullback: `close_3 <= EMA21_3`, `upper_wick_3/body_3 >= 1.25`, and `close_location_3 <= 0.50`; enter short next eligible bar. | Long exhaustion/reversal only in `RANGE` when `close_3 > EMA21_3` and `close_3 > close_2`; enter long next eligible bar. | **SKIP**. |

The regime/bias chooses the reading: `TREND_UP` can select only the stated long continuation, `TREND_DOWN` only the stated short continuation, and `RANGE` can select only the stated reversal reading for `BBS` or `SSB`. `UNKNOWN`, `TRANSITION`, or a failed row condition is always **SKIP**. There is no operator choice between continuation and reversal. A sequence is not a signal merely because its letters appear; all three candles must pass the S/B definitions, and the row's regime rule must pass.

## 5. Risk-tiered cycle and the 2:1 outcome model

A cycle is a non-overlapping ordered group of up to three accepted trades from one sequence/regime hypothesis:

1. **Trade 1:** full size, risk `1.00R`.
2. **Trade 2:** full size, risk `1.00R`.
3. **Trade 3:** minimal probe, risk `0.25R` by default; run `0.30R` as a separately labeled sensitivity. It is never silently promoted to full size.

A full-size winner is `+1.00R gross` and a full-size stop is `-1.00R gross`. A probe winner is `+0.25R gross` and its stop is `-0.25R gross`, before costs. The phrase “2:1 model” means the intended two full-risk winning outcomes versus one small-risk probe loss; it is not a guarantee and is not a 2R target promise.

The canonical illustration is exact: `+1R +1R -0.25R = +1.75R before costs`. With two full-size winners and one probe loss, net cycle result is `1.75R - entry costs - exit costs - applicable fees/funding - slippage`. If all three trades have equal risk, two wins and one loss at `1R` gives only `+1R before costs`, not the tiered `+1.75R`.

For any sample, report expectancy in R as:

`E[R/trade] = P(win) * average_win_R - P(loss) * average_loss_R - average_all_costs_R`,

where costs include every entry and exit cost and time exits are their observed realized R. For a cycle, sum the three realized, cost-adjusted trade results and divide by completed cycles. A 66% win rate at 1R targets is profitable only if average losses and all spread, slippage, fee, funding, and other entry/exit costs leave positive expectancy. **66% is not a guarantee.**

Cycle boundaries are deterministic:

- A new cycle starts only when flat, not in cooldown, daily loss is below its cap, and an accepted sequence signal is entered.
- Trade 2 may be taken only after trade 1 is fully closed and a new qualifying signal of the same sequence type and regime appears within `cycle_signal_window_minutes` (90). Trade 3 follows the same rule after trade 2.
- No position overlap, pyramiding, hedging, or simultaneous cycle is allowed.
- A cycle ends when trade 3 closes, when the 120-minute maximum cycle duration from trade 1 entry is reached, when no next qualifying signal arrives within 90 minutes, or when a daily limit/kill switch halts trading. Unused slots are not losses.
- After a cycle ends, wait `cooldown_bars_after_exit=1` complete base bar and require a newly completed qualifying sequence; the old sequence cannot start a new cycle.

## 6. Exit, latency, and re-entry rules

At entry, place a normal fixed stop at `1.00R` from the actual fill and a target at `+1.00R` for full-size trades. For a probe, use the same direction and stop geometry but size the monetary risk to `0.25R` (or the declared `0.30R` sensitivity) and target `+0.25R`. Stop/target precedence within a candle must be conservative: when both are touched and tick order is unavailable, record the stop first; do not choose the favorable order.

Every position has a hard time cap of **43 minutes** from actual entry timestamp. At the cap, flatten at the next available executable price regardless of P&L, label the exit `time_exit`, and include its costs/slippage. A sensitivity run may use a **45-minute** cap, but no trade may exceed the cap configured for that run. If the cap fires during momentum, still flatten; do not reinterpret the signal or hold longer. Do not re-enter on the same bar as a time exit. The next eligible entry is the open of the next base candle after one complete cooldown bar, and only if a newly qualifying sequence is present.

Model order latency as next-bar execution: signal at close `t`, order submitted after that close, fill at the next bar open plus modeled latency/slippage. Stops, targets, and time exits also receive venue-specific exit slippage. If exact intrabar ordering is unavailable, use the declared conservative assumption consistently across all variants.

## 7. Data and backtest protocol

**XAUUSD:** use OANDA practice candles and document the instrument/account configuration. API documentation: https://developer.oanda.com/rest-live-v20/introduction/ . Practice base endpoint: https://api-fxpractice.oanda.com . A typical candle request is the practice v20 instruments/candles resource under that base, with `granularity=M1` or `M5`; record the returned timestamps, completeness flags, bid/ask or mid choice, and volume.

**SOL:** use Binance public klines, normally `SOLUSDT`, and record the market type and symbol. Public REST market-data documentation: https://developers.binance.com/en/docs/binance-spot-api-docs/rest-api/market-data-endpoints . Public data base: https://data-api.binance.vision . Use the kline interval `1m` or `5m`; discard the currently open kline and record UTC timestamps. Spot fees are modeled when applicable; funding is modeled for a derivatives run when applicable, never assumed zero.

Required protocol:

- Use at least **200 completed cycles per sequence and regime where feasible**, preferably 300+. If a cell has fewer, report `INSUFFICIENT_SAMPLE` with its actual count; never pad or merge it silently.
- Split chronologically into train, validation, and untouched test data. Parameter selection is train-only; validation is for the pre-registered choice; test is run once for the frozen specification.
- Use walk-forward evaluation with a written window scheme. No random shuffling, leakage, future-bar features, future bias candles, or post-trade knowledge in entry rules.
- Build 15m/1h bias from closed candles only, and use only information available at the signal timestamp.
- Test `TREND_UP`, `TREND_DOWN`, `RANGE`, and `UNKNOWN` separately. `UNKNOWN` must produce no trades but must have a count and percentage report.
- Model spread and slippage on **each entry and each exit**, plus commissions/fees, funding where applicable, and next-bar execution/latency. Use venue-specific OANDA and Binance assumptions and publish the assumptions with the result.
- Keep 1m and 5m, XAUUSD and SOL, volume-gated and ungated, and 43-minute and 45-minute sensitivity results as distinct runs. Do not cherry-pick the best run.

## 8. Required report fields

Every run and every Friday report must include:

- venue, instrument, timeframe, date range, timezone, data URL/source, and candle completeness policy;
- parameter version, bias construction, execution latency, spread model, slippage model, fees, funding, and currency;
- cycle count and completed/aborted cycle count; trades per cycle and unused slots;
- win rate by `SSS`, `BBB`, `BBS`, `SSB`, and by continuation/reversal reading;
- probe win rate, probe loss rate, standalone probe expectancy, and probe contribution;
- average net R/trade and average net R/cycle, expectancy, profit factor;
- maximum drawdown in R and account currency, longest losing streak, time-exit count/rate;
- total and average spread, slippage, fees, funding, and other costs;
- sequence-by-regime breakdown, `UNKNOWN`/transition count, train/validation/test and walk-forward breakdown;
- which sequence is best under the frozen cost-adjusted test result, with sample size and uncertainty context;
- a direct comparison of the full system **with versus without the probe**.

The probe must prove incremental value. Retain it only if its standalone expectancy and its information/selection benefit improve the cost-adjusted system enough to offset its risk and execution cost. Otherwise remove it from the production hypothesis. A favorable aggregate result without this ablation is insufficient.

## 9. Friday-only review and change control

Once per week, on **Friday only after the week's data is closed**, generate a sequence breakdown for `SSS`, `BBB`, `BBS`, and `SSB`. Show the best sequence type, performance by `TREND_UP`, `TREND_DOWN`, `RANGE`, and `UNKNOWN`, probe contribution, sample counts/insufficient-sample flags, and cost-adjusted test/walk-forward results.

Apply this deterministic decision rule:

- **RETAIN:** the frozen sequence/risk rule has positive net expectancy in the untouched test and walk-forward cells with adequate sample, and the probe passes the incremental-value comparison.
- **REVISE ONLY IN RESEARCH:** a rule fails a pre-registered threshold or has unstable regime/venue results, but the hypothesis is worth a new versioned train/validation experiment. No live parameter change.
- **CUT:** no adequate positive evidence after costs, the probe is not incrementally useful, or risk limits are breached in the predefined stress tests.

No live parameter tweaking, sequence deletion, stop widening, target moving, or regime relabeling is allowed in response to one week or one losing streak. Any change creates a new version and repeats the chronological protocol.

## 10. Risk and operational guardrails

This is a hypothesis, not a proven profitable system. Do not infer independent profitability evidence from this repository, and do not claim a guaranteed 2:1 result. Funded-account rules, daily loss limits, trailing drawdown, news restrictions, and symbol restrictions can make a backtest inapplicable.

Before any paper or live consideration, set a fixed small per-trade risk, an explicit maximum daily loss, and a kill switch. The kill switch must halt new entries and flatten positions when the daily loss cap, connection/data-integrity failure, repeated rejected orders, or an unmodeled spread/slippage threshold is hit. Never martingale, average down, revenge trade, or increase size after a loss. A skipped/invalid setup is a no-trade outcome, not an instruction to force the next trade. Review venue and funded-account terms independently before risking capital.
