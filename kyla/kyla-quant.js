'use strict';

const SIMPLE_PRICE_URL =
  'https://api.coingecko.com/api/v3/simple/price?ids=solana,bitcoin&vs_currencies=usd';
const SOL_RANGE_URL = () => {
  const now = Math.floor(Date.now() / 1000);
  const from = now - 200 * 60;
  return `https://api.coingecko.com/api/v3/coins/solana/market_chart/range?vs_currency=usd&from=${from}&to=${now}`;
};
const HYPERLIQUID_URL = 'https://api.hyperliquid.xyz/info';
const HYPERLIQUID_BODY = '{"type":"meta"}';

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { accept: 'application/json', ...(options.headers || {}) },
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText} from ${url}`);
  }
  return response.json();
}

function averageLast200Minutes(prices) {
  const cutoff = Date.now() - 200 * 60 * 1000;
  const recent = prices
    .filter(([timestamp, price]) => timestamp >= cutoff && Number.isFinite(price))
    .map(([, price]) => price);
  const values = recent.length ? recent : prices.map(([, price]) => price).filter(Number.isFinite);
  if (!values.length) throw new Error('CoinGecko returned no SOL history');
  return values.reduce((sum, price) => sum + price, 0) / values.length;
}

function formatUsd(value) {
  return `$${Number(value).toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
}

async function main() {
  const [spot, history, meta] = await Promise.all([
    fetchJson(SIMPLE_PRICE_URL),
    fetchJson(SOL_RANGE_URL()),
    fetchJson(HYPERLIQUID_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: HYPERLIQUID_BODY,
    }),
  ]);

  const sol = spot?.solana?.usd;
  const btc = spot?.bitcoin?.usd;
  if (!Number.isFinite(sol) || !Number.isFinite(btc)) {
    throw new Error('CoinGecko did not return SOL/USD and BTC/USD prices');
  }

  const solHistory = Array.isArray(history?.prices) ? history.prices : [];
  const average = averageLast200Minutes(solHistory);
  const bias = sol > average ? 'bullish' : sol < average ? 'bearish' : 'neutral';
  const universe = Array.isArray(meta?.universe) ? meta.universe.slice(0, 3) : [];

  console.log(`Prices: SOL/USD ${formatUsd(sol)} | BTC/USD ${formatUsd(btc)}`);
  console.log(`Bias: SOL ${bias} (200m avg ${formatUsd(average)}) | Hyperliquid top 3: ${JSON.stringify(universe)}`);
  console.log('no auto-trades — review rules first');
}

main().catch((error) => {
  console.error(`quant starter failed: ${error.message}`);
  process.exitCode = 1;
});
