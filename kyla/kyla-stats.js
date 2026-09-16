'use strict';

const fs = require('fs');

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const character = text[i];

    if (inQuotes) {
      if (character === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 1;
        } else {
          inQuotes = false;
        }
      } else {
        field += character;
      }
    } else if (character === '"' && field.length === 0) {
      inQuotes = true;
    } else if (character === ',') {
      row.push(field);
      field = '';
    } else if (character === '\n') {
      row.push(field);
      if (row.some((value) => value.trim() !== '')) rows.push(row);
      row = [];
      field = '';
    } else if (character !== '\r') {
      field += character;
    }
  }

  if (field.length > 0 || row.length > 0) {
    row.push(field);
    if (row.some((value) => value.trim() !== '')) rows.push(row);
  }

  return rows;
}

function finiteNumber(value) {
  if (typeof value !== 'string' || value.trim() === '') return null;
  const number = Number(value.trim());
  return Number.isFinite(number) ? number : null;
}

function formatMoney(value) {
  return Number.isFinite(value) ? `${value.toFixed(2)} KSh` : 'n/a';
}

function report(strategy, trades) {
  const wins = trades.filter((trade) => trade.pnl > 0);
  const losses = trades.filter((trade) => trade.pnl < 0);
  const grossWins = wins.reduce((total, trade) => total + trade.pnl, 0);
  const grossLosses = losses.reduce((total, trade) => total + Math.abs(trade.pnl), 0);
  const total = trades.reduce((sum, trade) => sum + trade.pnl, 0);
  const best = trades.length ? Math.max(...trades.map((trade) => trade.pnl)) : null;
  const worst = trades.length ? Math.min(...trades.map((trade) => trade.pnl)) : null;
  const profitFactor = grossLosses > 0 ? (grossWins / grossLosses).toFixed(2) : (grossWins > 0 ? 'Infinity' : 'n/a');
  const winRate = trades.length ? `${((wins.length / trades.length) * 100).toFixed(1)}%` : '0.0%';

  console.log(`\n${strategy}`);
  console.log(`  Trades: ${trades.length}`);
  console.log(`  Win rate: ${winRate}`);
  console.log(`  Total P/L: ${formatMoney(total)}`);
  console.log(`  Average win: ${formatMoney(wins.length ? grossWins / wins.length : null)}`);
  console.log(`  Average loss: ${formatMoney(losses.length ? -grossLosses / losses.length : null)}`);
  console.log(`  Profit factor: ${profitFactor}`);
  console.log(`  Best trade: ${formatMoney(best)}`);
  console.log(`  Worst trade: ${formatMoney(worst)}`);
}

function main() {
  const candidates = [
    `${process.cwd()}/kyla/journal.csv`,
    `${__dirname}/journal.csv`,
  ];
  const journalPath = candidates.find((candidate) => {
    try {
      return fs.statSync(candidate).isFile();
    } catch {
      return false;
    }
  });

  if (!journalPath) {
    console.error('Could not find kyla/journal.csv. Run this script from the repository root or keep it beside the journal.');
    process.exitCode = 1;
    return;
  }

  let text;
  try {
    text = fs.readFileSync(journalPath, 'utf8');
  } catch (error) {
    console.error(`Could not read ${journalPath}: ${error.message}`);
    process.exitCode = 1;
    return;
  }

  const rows = parseCsv(text);
  if (rows.length === 0) {
    console.log('No actual trades found: the journal is empty.');
    return;
  }

  const headers = rows[0].map((header) => header.trim());
  const index = Object.fromEntries(headers.map((header, position) => [header, position]));
  const requiredHeaders = ['strategy', 'entry', 'sl', 'tp', 'exit', 'pnl_ksh', 'notes'];
  const missingHeaders = requiredHeaders.filter((header) => index[header] === undefined);
  if (missingHeaders.length) {
    console.error(`Missing required journal headers: ${missingHeaders.join(', ')}`);
    process.exitCode = 1;
    return;
  }

  const strategyNames = ['Range Scalp', 'Breakout', 'Pullback Trend'];
  const grouped = new Map(strategyNames.map((strategy) => [strategy, []]));
  let exampleRows = 0;
  let invalidRows = 0;

  for (const row of rows.slice(1)) {
    const notes = row[index.notes] || '';
    if (/example/i.test(notes)) {
      exampleRows += 1;
      continue;
    }

    const numericFields = ['entry', 'sl', 'tp', 'exit', 'pnl_ksh'];
    const values = Object.fromEntries(numericFields.map((field) => [field, finiteNumber(row[index[field]])]));
    if (numericFields.some((field) => values[field] === null)) {
      invalidRows += 1;
      continue;
    }

    const strategy = (row[index.strategy] || '').trim() || 'Unspecified';
    if (!grouped.has(strategy)) grouped.set(strategy, []);
    grouped.get(strategy).push({ pnl: values.pnl_ksh });
  }

  const actualTrades = [...grouped.values()].reduce((total, trades) => total + trades.length, 0);
  console.log(`Journal: ${journalPath}`);
  console.log(`Example rows ignored: ${exampleRows}`);
  console.log(`Invalid rows ignored: ${invalidRows}`);
  if (actualTrades === 0) {
    console.log('No actual trades found: example rows and rows with missing/invalid numeric fields are excluded.');
  }

  for (const [strategy, trades] of grouped) report(strategy, trades);
}

main();
