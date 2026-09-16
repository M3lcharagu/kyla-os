# QUANT_NOTES

Beginner-to-intermediate research notes for Mel. These are study notes, not financial advice, not a live trade call, and not a promise that demo results transfer to live trading. The examples are framed around XAUUSD scalps held for roughly 15–45 minutes on an HFM demo account and SOL on Hyperliquid; they are not instructions to place a trade.

## 1. Markov-signal gold system from creator David K

### What it is
A Markov or hidden-Markov-style model treats the market as moving among unobserved regimes—such as bullish trend, bearish trend, and range/quiet conditions—where the next regime depends mostly on the current regime. A signal system can use those inferred regimes to decide whether a setup is eligible. The creator's TikTok description is a particular system, not proof that a Markov model can predict the next gold move.

The stated signal workflow uses **CLOSED daily candles and CLOSED 4H candles only**. Execution is a **live market order** when the rules say to act, with configurable risk per trade. If the system says today was skipped, that is a **no-trade day**, not a missing signal to be filled in by guesswork. I have not independently verified any live signal from the TikTok, so this note makes no claim about what today's signal is.

### Key formula / idea
For a simple regime model, let \(S_t\) be the hidden state and \(X_t\) the observed return or feature:

\[
P(S_t=j\mid S_{t-1}=i)=P_{ij},\qquad P(S_t\mid X_{1:t})\propto P(X_t\mid S_t)P(S_t\mid X_{1:t-1}).
\]

The transition matrix \(P\) describes regime persistence and the emission model \(P(X_t\mid S_t)\) describes what returns/volatility may look like in each state. The operational rule is more important than the label: only completed bars may update the state used for a decision, then a live order is executed under a pre-set risk cap.

### Why it matters for Mel's actual trading
For an XAUUSD scalp held 15–45 minutes, using an unclosed daily or 4H candle can let future information leak into the apparent regime. That can turn a backtest into hindsight. Closed higher-timeframe context may help decide whether a short-term setup is even eligible, but it does not remove spread, slippage, news, execution, or model risk. SOL on Hyperliquid can have different liquidity, volatility, funding, and liquidation mechanics, so a gold regime rule cannot simply be copied to SOL.

The displayed **50% risk-per-trade setting is reckless and must NOT be copied**. A risk percentage is not a confidence score. A 50% loss on one trade can make recovery mathematically and psychologically difficult; Mel should use a much smaller, pre-committed demo risk cap and treat any live account separately.

### Concrete how-to-use note
1. Timestamp every daily and 4H candle in one timezone and mark it closed before it can enter a feature set.
2. Record the regime/signal, the exact close time, the intended stop distance, and the configurable risk cap before any order.
3. If the published workflow says “skipped,” record **no-trade day**; do not invent a market order.
4. If testing on XAUUSD, model the real 15–45 minute holding window, HFM demo spread, slippage, and news exclusions. If testing SOL, separately model Hyperliquid fees, funding, leverage, and liquidation risk.
5. Never treat this note as a live signal and never copy the 50% setting.

## 2. Bailey & Lopez de Prado (2014) Deflated Sharpe Ratio

### What it is
The Deflated Sharpe Ratio (DSR) adjusts a reported Sharpe ratio for two common sources of optimism: selection bias from trying many strategies/parameters and non-normal return distributions. A high Sharpe found after many trials is less impressive than the same Sharpe specified in advance and evaluated once.

### Key formula / idea
A common presentation is:

\[
\mathrm{DSR}=\Phi\!\left(\frac{\widehat{SR}-SR^*}{\sqrt{\frac{1-\hat\gamma_3\widehat{SR}+\frac{\hat\gamma_4-1}{4}\widehat{SR}^{2}}{T-1}}}\right),
\]

where \(\Phi\) is the standard normal CDF, \(\widehat{SR}\) is the observed Sharpe, \(T\) is the number of return observations, \(\hat\gamma_3\) is skewness, \(\hat\gamma_4\) is kurtosis, and \(SR^*\) is the benchmark Sharpe expected from the best result among the number of trials considered. Equivalent algebraic forms put the square-root term in the numerator. The meaning is the same: ask whether the observed Sharpe clears a multiple-testing and distribution-shape hurdle, rather than asking only whether it is positive.

### Why it matters for Mel's actual trading
Mel can easily test several XAUUSD entry rules, stop widths, sessions, indicators, and holding times, then remember the winner. That is a multiple-comparisons problem. SOL adds more knobs: market, leverage, funding, time window, and execution venue. Short samples of 15–45 minute trades can also have skew, fat tails, and clustered losses, making a normal-return Sharpe misleading.

DSR does not make a strategy safe or prove causality. It is a guardrail against promoting a lucky backtest.

### Concrete how-to-use note
Keep a trial ledger: every materially tested rule, parameter set, market, date range, and out-of-sample result—even the losers. Estimate skewness and kurtosis from the same return definition, use a consistent observation frequency, and set the multiple-trial benchmark before celebrating the best result. Compare DSR-style evidence with drawdown, costs, trade count, and a genuinely untouched period. Do not use a favorable DSR as permission to raise risk.

## 3. Prediction-market mispricing/arbitrage engine: Polymarket vs Kalshi

### What it is
A prediction-market engine compares executable prices for equivalent outcomes across venues or within a venue. An apparent two-outcome arbitrage exists when the prices needed to buy mutually exclusive, collectively exhaustive outcomes sum to less than the payout after all costs. The engine must distinguish a screen-level discrepancy from an executable, settleable opportunity.

The supplied 2026 UCLA study reports more than **75 million order-book snapshots** across **173 NBA games**, but only **7 executable in-game arbitrage episodes**, with an approximately **3.6-second median duration**. That is a useful warning: many apparent discrepancies disappear once execution and timing are tested.

### Key formula / idea
For a two-outcome buy, a first-pass gross condition is:

\[
p_{YES}+p_{NO}<1.
\]

The practical condition is net edge after every leg and every cost:

\[
\text{net edge}=\text{guaranteed settlement value}-\text{capital committed}-\text{fees}-\text{spread/slippage}-\text{funding, transfer, and operational costs}.
\]

For a binary bet with net profit odds \(b\), estimated win probability \(p\), and \(q=1-p\), the basic Kelly fraction is:

\[
f^*=\frac{bp-q}{b}.
\]

That is a theoretical sizing fraction, not a recommendation. Probability/model error, correlated positions, venue limits, and a short-lived edge argue for a strongly fractional cap—or no trade.

### Why it matters for Mel's actual trading
The research lesson transfers to SOL and XAUUSD execution: a quote is not a fill, and a gross edge is not a net edge. Polymarket and Kalshi can differ in contract wording, resolution source, trading hours, fees, collateral, and settlement timing. Cross-platform arbitrage carries **legging risk**: one leg can fill while the other moves or fails. It also carries cross-platform settlement risk: “equivalent” outcomes may resolve differently or at different times.

This is not a claim that KYLA currently has a prediction-market engine. It is a research pattern for measuring whether a theoretical edge survives the order book and the operational path.

### Concrete how-to-use note
For every candidate, snapshot both order books with synchronized timestamps; record available size at each price, fees, spread, latency, partial-fill behavior, collateral/transfer time, contract wording, and resolution rules. Calculate the net edge at the quantity actually executable, not at the top-of-book headline price. Log apparent opportunities separately from fully executable, simultaneously hedged opportunities. If sizing is studied, start with a tiny fractional-Kelly simulation and hard portfolio caps; never let a Kelly formula override a loss limit.

## 4. Information diffusion: Hawkes process for news to price

### What it is
A Hawkes process models event arrivals whose intensity can rise after a news event or after prior market events. It separates **exogenous** moves, driven by outside information such as a release, from **self-excited** moves, where one market event increases the chance of more events shortly afterward. It is a useful timing model, not a guarantee that news direction is predictable.

### Key formula / idea
A basic univariate Hawkes intensity is:

\[
\lambda(t)=\mu+\sum_{t_i<t}\alpha e^{-\beta(t-t_i)}.
\]

Here \(\mu\) is baseline intensity, \(\alpha\) is the jump in intensity after an event, and \(\beta\) is the exponential decay rate. The response half-life is:

\[
t_{1/2}=\frac{\log 2}{\beta}.
\]

A multivariate version can let news, trades, volatility, and order-book events excite one another. The kernel should be estimated with event timestamps and tested out of sample.

### Why it matters for Mel's actual trading
XAUUSD can react sharply to scheduled macro news; a 15–45 minute scalp can spend its entire intended holding period inside the diffusion burst. SOL can show self-exciting cascades during liquidations or fast crypto news. If timestamps are coarse or sourced from different clocks, the model can confuse cause and reaction and make the half-life look more precise than it is.

### Concrete how-to-use note
Build an event table with UTC timestamps, source type, asset, price move, spread, and whether the event was scheduled news or a market event. Estimate separate baseline and excitation behavior for XAUUSD and SOL. Use the estimated half-life as a research window for “avoid, wait, or study” rules, then include spread and slippage. Do not infer trade direction from intensity alone; validate direction and execution separately.

## 5. Alpha decay: Falck, Rej & Thesmar (2021)

### What it is
Alpha decay is the reduction in a strategy's excess performance after discovery, publication, adoption, crowding, or changing market conditions. A backtest can remain mathematically correct while its live opportunity shrinks because other participants trade the same signal or because the original market structure changes.

### Key formula / idea
A simple way to monitor it is a rolling post-discovery Sharpe or information ratio relative to the pre-discovery estimate:

\[
\text{decay ratio}_t=\frac{SR_{\text{post},t}}{SR_{\text{pre}}},\qquad
\text{drop}=1-\text{decay ratio}_t.
\]

The 2021 study discussed **72 strategies** and reported a roughly **50% post-publication Sharpe drop**. That is an empirical finding from that study, not a universal constant or a forecast for Mel's strategies.

### Why it matters for Mel's actual trading
A strategy copied from a creator, paper, or public code may be most crowded precisely when it becomes visible. XAUUSD scalps are especially sensitive to spread, session liquidity, news, and execution timing; SOL can experience rapid crowding and regime shifts. A good demo period can therefore be a discovery period rather than proof of durable alpha.

### Concrete how-to-use note
Stamp the date a rule was designed, changed, or made public. Keep a pre-publication/in-sample segment separate from a later forward segment, and monitor rolling net performance after fees, slippage, and funding. Record whether deterioration comes from signal accuracy, payoff asymmetry, latency, or costs. Retire or revise a rule based on a pre-written test—not because of one losing streak and not because a recent win tempts more leverage.

## 6. Monte Carlo reshuffling of equity curves

### What it is
Monte Carlo reshuffling repeatedly reorders observed trade returns to show how the same wins and losses could produce different paths. It helps estimate path risk: likely and bad drawdowns, losing streaks, time to recovery, and the chance that a strategy's observed order was unusually favorable.

### Key formula / idea
Given trade returns \(r_1,\ldots,r_n\), sample a permutation \(\pi\) and construct:

\[
E_t=E_{t-1}(1+r_{\pi(t)}),\qquad
DD_{\max}=\max_t\left(1-\frac{E_t}{\max_{u\le t}E_u}\right).
\]

Repeat many times and inspect the distribution of maximum drawdown, terminal equity, and longest losing streak. A “worst drawdown path” can mean a high percentile such as the 95th/99th drawdown, or the worst simulated path under a declared simulation count—not an impossible certainty.

### Why it matters for Mel's actual trading
Two systems with the same average return can feel very different when one clusters losses. This matters when XAUUSD trades are held for 15–45 minutes and when SOL positions face fast moves, funding, or liquidation. A demo equity curve with a convenient win order may understate the cash and discipline needed for a less favorable order.

### Concrete how-to-use note
Use net per-trade returns, preserve the actual position-sizing rule, and report the number of simulations and percentile chosen. Run a simple reshuffle first, then stress tests that retain or model dependence, regime changes, costs, skipped trades, and gap/slippage effects. Reshuffling cannot create information: it does not repair look-ahead bias, a small or selected sample, changing strategy rules, or an iid assumption that is false. Use the results to set conservative drawdown and risk caps, not to justify a larger bet.

## 7. Time-series dependency and the X1 → X2 → X3 arrows

### What it is
The arrows \(X_1\rightarrow X_2\rightarrow X_3\) represent ordered observations: past data may contain information about the future, while future data must not be allowed to influence a past decision. Time-series dependency means observations are not automatically independent, so random shuffling can leak regime and label information across train and test sets.

### Key formula / idea
A starter autoregressive model is:

\[
X_t=c+\phi X_{t-1}+\varepsilon_t,
\]

or with several lags, \(X_t=c+\sum_{k=1}^{p}\phi_kX_{t-k}+\varepsilon_t\). Features for a decision at time \(t\) must be computed from information available at or before \(t\), and a forward label such as the return from \(t\) to \(t+h\) must not be used as a feature.

### Why it matters for Mel's actual trading
For XAUUSD, an unclosed 15-minute, 4H, or daily candle can silently turn into future knowledge. For SOL, exchange timestamps, funding snapshots, liquidation data, and order-book updates can arrive at different times. Look-ahead leakage can make a 15–45 minute strategy look precise in a notebook while being impossible to execute.

### Concrete how-to-use note
Draw the data timeline before coding: feature cutoff, signal decision, order timestamp, fill, exit, and label horizon. Use chronological train/validation/test splits or walk-forward testing; fit scalers and thresholds on training data only; and lag any aggregate that would not have been known at decision time. Keep a final untouched period. A dependency arrow is a reminder to ask “what was known then?” before trusting any result.

## How this maps to KYLA

KYLA's actual trading-room mapping is in the repository root file `config.yaml`: `R3` is named **TEMPERANTIA Trading Room**, with the purpose **Trading research and journaling**, aliases `temperantia`, `trading`, `markets`, and `investing`. The relevant existing files are all under `kyla/`; no invented alternative path is needed.

- **R3 TEMPERANTIA Trading Room — `config.yaml`**: Treat R3 as the research-and-journaling home for hypotheses, timestamp rules, skipped/no-trade decisions, cost assumptions, and post-trade review. Concepts 1, 4, 5, 6, and 7 belong here as research questions and audit notes before they become code. R3 does not turn a note into a live signal.
- **`kyla/kyla-quant.js`**: The existing script fetches SOL/USD and BTC/USD data from CoinGecko, calculates a roughly 200-minute SOL average and a simple bullish/bearish/neutral bias, and reads a small Hyperliquid metadata response. It logs prices and says there are no auto-trades. It is therefore a natural place to study SOL time ordering (7), news/event timing as a future extension (4), costs and slippage before interpreting a bias (3), and regime ideas (1)—but it currently does **not** implement the David K gold Markov system, XAUUSD candles, a Polymarket/Kalshi arbitrage engine, Hawkes estimation, or real execution.
- **`kyla/kyla-stats.js`**: The existing statistics script reads a journal CSV, validates `strategy`, `entry`, `sl`, `tp`, `exit`, `pnl_ksh`, and `notes`, ignores example rows, groups actual rows by `Range Scalp`, `Breakout`, and `Pullback Trend`, and reports count, win rate, total P/L, averages, profit factor, and best/worst trade. It is a useful base for concepts 2, 5, and 6: maintain a complete trial ledger, calculate net rather than headline results, and add walk-forward/Monte Carlo analysis without changing the raw journal.
- **`kyla/journal.csv`**: This is the existing journal path consumed by `kyla/kyla-stats.js`. It currently contains a header plus two rows marked in their notes as example rows (a Range Scalp long on 2026-09-15 and a Breakout short on 2026-09-16), not a verified live-performance history. Add timestamps, venue/instrument, candle-closed status, fees/slippage, intended risk, regime/features, skipped reason, and out-of-sample/test-set label before using it for research. Do not treat the sample rows as evidence that a strategy works.

A practical KYLA workflow is: R3 records the hypothesis and data contract; `kyla/kyla-quant.js` provides a transparent market-data starting point for SOL research; `kyla/journal.csv` records attempted, skipped, and invalid ideas; and `kyla/kyla-stats.js` checks descriptive results. A future implementation should keep signal generation, execution, and evaluation separate so that closed-candle rules, latency, and costs cannot be hidden inside a favorable backtest.

## Operational checklist

- **Data timestamps:** store timezone/UTC, source, event time, arrival time, candle open/close, and order/fill time; reconcile clocks.
- **Closed candles:** use only closed daily/4H/15-minute candles for features that claim to be known at the decision; never fill a missing live signal from hindsight.
- **Fees and slippage:** include spread, commissions, funding, market-impact/partial fills, transfers, and venue-specific costs; compare apparent with executable edge.
- **Risk caps:** pre-commit a small per-trade and portfolio cap, maximum daily loss, leverage/liquidation guard, and stop-trading rule; the 50% TikTok setting is reckless and must not be copied.
- **Out-of-sample testing:** preserve chronological, untouched data; track every trial; use walk-forward evaluation and check selection bias, non-normality, alpha decay, and dependency.
- **Journaling:** record trades and no-trade decisions, hypothesis/version, instrument/venue, regime/features, entry/exit, costs, risk, reason for invalidation, and what was known at the time.

## Sources

https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2465675

https://davidhbailey.com/dhbpapers/deflated-sharpe.pdf

https://arxiv.org/abs/2105.01380

https://arxiv.org/html/2105.01380v1

https://arxiv.org/pdf/2105.01380

https://www.tandfonline.com/doi/full/10.1080/14697688.2022.2098810

https://arxiv.org/abs/1405.6047

https://link.aps.org/doi/10.1103/PhysRevE.91.012819

https://pubmed.ncbi.nlm.nih.gov/25679668/

https://arxiv.org/html/2605.00864v1

https://people.stat.ucla.edu/guangcheng/Arbitrage%20Analysis%20Cheng.pdf

https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6624718

https://www.tiktok.com/@david_k_g/video/7590001563125484856

https://medium.com/@Kryptera/i-built-a-hidden-markov-model-to-detect-gold-market-regimes-heres-what-the-data-revealed-46c84f2ca83d

https://www.youtube.com/watch?v=3U2AoySocRc
