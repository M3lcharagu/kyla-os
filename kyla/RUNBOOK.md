# 1-Hour Laptop Launch

This is the beginner-proof Windows 11 setup. Use **PowerShell** (the blue or black terminal that comes with Windows).

## 1. Install Node.js LTS and Git if they are missing

Copy and paste these commands into PowerShell. Each command installs the program only when it is not already available:

```powershell
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements }
```

Close PowerShell and open a **new** PowerShell window so the new PATH entries are loaded. Confirm both tools work:

```powershell
node --version
git --version
```

Node.js should be version 18 or newer. If `winget` is not available, install Node.js LTS from <https://nodejs.org/en/download> and Git for Windows from <https://git-scm.com/download/win>, then open a new PowerShell window and run the two version checks again.

## 2. Clone KYLA

Copy and paste these commands exactly:

```powershell
cd $HOME
git clone https://github.com/M3lcharagu/kyla-os
cd kyla-os
cd kyla
```

If you already cloned the repository, do not clone it a second time. Instead, run:

```powershell
cd $HOME\kyla-os\kyla
```

## 3. Install the KYLA dependencies

You are now inside the repository's `kyla` folder. Run:

```powershell
npm install
```

## 4. Create your Gemini API key file

Create your local `.env` file from the repository template:

```powershell
Copy-Item .env.example .env -Force
notepad .env
```

Notepad will open. Replace the placeholder line with your real Gemini API key, keeping this exact variable name and format:

```text
GEMINI_API_KEY=PASTE_YOUR_GEMINI_API_KEY_HERE
```

Save the file and close Notepad. Do not share this file or commit it; `.env` is ignored by Git. If you need a key, create one at <https://aistudio.google.com/apikey>.

## 5. Test the KYLA brain

Stay in the `kyla` folder and run:

```powershell
node kyla-brain.js
```

When you see `Ask KYLA:`, type a short question, then press **Enter**. A Gemini answer means the brain test worked. Press `Ctrl+C` when you are finished.

## 6. Test the daily news brief

Still in the `kyla` folder, run:

```powershell
node kyla-news.js
```

This fetches the configured market-news feeds and prints the brief in the terminal. A network error means the computer could not reach one of the external feeds; check your internet connection and try again.

## 7. Push the setup to GitHub

Return to the repository root, save the runbook/workflow changes, and push them to `main`:

```powershell
cd ..
git add .
git commit -m "Set up KYLA daily brief"
git push origin main
```

After you push, **GitHub Actions handles the daily brief automatically**. The workflow runs once per day at **07:00 UTC**, runs `node kyla-news.js` from `kyla`, and commits the generated output to `kyla/briefs/YYYY-MM-DD.md`. You can also start it manually from the repository's **Actions** tab using **KYLA Daily News Brief**.
