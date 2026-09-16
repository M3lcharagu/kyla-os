# KYLA starter kit

A small, beginner-friendly Node.js 18+ kit for asking Gemini questions and printing a quick CoinDesk + Hyperliquid brief. It uses free/public endpoints where possible; the Gemini call requires your own API key.

## Windows 11 quick start

1. If Node.js is not installed, download the current **LTS** release (version 18 or newer) from [nodejs.org](https://nodejs.org/en/download). Accept the default installer options.
2. Open PowerShell and run these commands from your local `kyla-os` repository folder:

   ```powershell
   cd kyla
   npm install
   Copy-Item .env.example .env
   notepad .env
   ```

3. In Notepad, replace `your_gemini_api_key_here` with your Gemini API key, save the file, and close Notepad. Never commit `.env` or share the key.
4. Run the Gemini brain with a command-line prompt:

   ```powershell
   node kyla-brain.js "Give me three beginner tips for reading crypto market news."
   ```

   Or run it without an argument and type a prompt when asked:

   ```powershell
   node kyla-brain.js
   ```

5. Print the news and HYPE metadata brief:

   ```powershell
   node kyla-news.js
   ```

You can also use `npm run brain` and `npm run news` after installation. The news script does not need a Gemini key.

## Files

- `kyla-brain.js` — calls Gemini 2.5 Flash using `GEMINI_API_KEY