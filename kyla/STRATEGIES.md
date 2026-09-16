# XAUUSD Demo Scalping Strategies

These three rule-based strategies are for Mel's HFM demo account only. They are testing templates, not financial advice. Use small demo size, risk no more than 0.5% of demo equity per trade, never widen a stop, and skip trades when spreads or news make the planned risk unclear. Use a 15-minute chart unless the rule says otherwise; every position must be closed after 45 minutes if neither target nor stop has been reached.

## A. Range Scalp

Trade a clearly bounded, sideways range only.

- **Entry trigger:** Mark support and resistance from at least two recent touches. Buy only when a 15-minute candle tests support and closes back above it; enter at the next candle open. Sell only when a 15-minute candle tests resistance and closes back below it; enter at the next candle open.
- **Stop loss:** For a buy, place the stop 0.20% below support (or just beyond the rejection wick, whichever is farther). For a sell, place it 0.20% above resistance (or just beyond the rejection wick, whichever is farther). Do not enter if the stop would be wider than 0.35% of entry.
- **Take profit:** Target the range midpoint first; set the final take profit just before the opposite boundary, with a minimum planned reward-to-risk of 1.5:1. Do not chase a target beyond the range.
- **Trade limit and hold time:** Maximum 3 trades per day across all strategies. Hold 15–45 minutes; close at 45 minutes if still open.
- **Invalidation:** The setup is invalid if a 15-minute candle closes outside the range, support/resistance has fewer than two clear touches, the rejection candle closes through the level, or the spread makes the planned risk exceed the limit. Cancel an unfilled order when invalidated.

## B. Breakout

Trade a confirmed break from a clearly marked support or resistance level.

- **Entry trigger:** Mark the most recent clear support and resistance. For a long, enter at the next candle open only after a 15-minute candle closes above resistance by at least 0.05% of price. For a short, enter at the next candle open only after a 15-minute candle closes below support by at least 0.05% of price. Do not enter on a wick-only break.
- **Stop loss:** Put the stop on the inside of the broken level, 0.20% beyond that level against the trade (below resistance for a long, above support for a short). If the required stop is wider than 0.35% of entry, skip the trade.
- **Take profit:** Set take profit at 2 times the initial risk, or at the next major level if it is closer; take the closer target. Do not move the stop farther away.
- **Trade limit and hold time:** Maximum 3 trades per day across all strategies. Hold 15–45 minutes; close at 45 minutes if still open.
- **Invalidation:** The setup is invalid if the breakout candle closes back inside the level before entry, the breakout is only a wick, the next major level leaves less than 1.5:1 reward-to-risk, or the spread/news makes execution uncertain. Cancel an unfilled order when invalidated.

## C. Pullback Trend

Trade a pullback in the direction of a confirmed short-term trend.

- **Entry trigger:** On the 15-minute chart, an uptrend requires price above a rising 20 EMA and two higher swing highs/lows. Buy only when price pulls back to the 20 EMA or a prior broken resistance level, then a candle closes bullish above that level; enter at the next candle open. For a downtrend, reverse the rules: price must be below a falling 20 EMA with two lower swing highs/lows, and enter short after a bearish close below the 20 EMA or retested level.
- **Stop loss:** For a buy, place the stop 0.20% below the pullback swing low; for a sell, place it 0.20% above the pullback swing high. Skip the trade if the stop would be wider than 0.35% of entry.
- **Take profit:** Target the prior trend extreme or 2 times initial risk, whichever comes first, and take the trade only when the planned reward-to-risk is at least 1.5:1.
- **Trade limit and hold time:** Maximum 3 trades per day across all strategies. Hold 15–45 minutes; close at 45 minutes if still open.
- **Invalidation:** The setup is invalid if the EMA flattens or price closes through it against the trend, the pullback breaks the swing point, the confirmation candle is missing, the minimum reward-to-risk is unavailable, or the spread/news makes risk unclear. Cancel an unfilled order when invalidated.

## Demo-testing checklist

Record every attempted trade in `journal.csv`, including skipped or invalidated ideas in the notes when useful. Stop for the day after three trades or after two consecutive losses, review the journal, and test these rules on demo data before considering any change.