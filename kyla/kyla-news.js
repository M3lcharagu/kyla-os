const axios = require("axios");
const { XMLParser } = require("fast-xml-parser");

const RSS_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml";
const HYPERLIQUID_URL = "https://api.hyperliquid.xyz/info";

function textValue(value) {
  if (typeof value === "string") return value.trim();
  return value?.["#text"]?.trim() || "";
}

async function main() {
  const [rssResponse, metaResponse] = await Promise.all([
    axios.get(RSS_URL, { timeout: 20000 }),
    axios.post(
      HYPERLIQUID_URL,
      { type: "meta" },
      {
        headers: { "Content-Type": "application/json" },
        timeout: 20000,
      }
    ),
  ]);

  const parser = new XMLParser({ trimValues: true });
  const feed = parser.parse(rssResponse.data);
  const rawItems = feed?.rss?.channel?.item || [];
  const items = (Array.isArray(rawItems) ? rawItems : [rawItems]).filter(Boolean);
  const universe = Array.isArray(metaResponse.data?.universe)
    ? metaResponse.data.universe
    : [];
  const hype = universe.find(
    (asset) => String(asset?.name || "").toUpperCase() === "HYPE"
  );

  console.log("KYLA quant brief");
  console.log(`Generated: ${new Date().toISOString()}`);
  console.log("\nTop 3 CoinDesk headlines:");

  if (items.length === 0) {
    console.log("No headlines were returned.");
  } else {
    items.slice(0, 3).forEach((item, index) => {
      const title = textValue(item.title) || "Untitled";
      const link = textValue(item.link);
      console.log(`${index + 1}. ${title}${link ? ` — ${link}` : ""}`);
    });
  }

  console.log("\nHYPE metadata (Hyperliquid meta endpoint):");
  if (!hype) {
    console.log("HYPE was not present in the returned universe.");
  } else {
    const summary = {
      name: hype.name,
      szDecimals: hype.szDecimals,
      maxLeverage: hype.maxLeverage,
      onlyIsolated: hype.onlyIsolated,
      marginMode: hype.marginMode,
    };
    console.log(JSON.stringify(summary, null, 2));
  }
}

main().catch((error) => {
  const detail = error.response?.data?.error || error.message;
  console.error(`KYLA news error: ${detail}`);
  process.exitCode = 1;
});
