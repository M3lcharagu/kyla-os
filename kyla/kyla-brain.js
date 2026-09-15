require("dotenv").config();

const axios = require("axios");
const readline = require("node:readline");

const GEMINI_ENDPOINT =
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent";

async function readPrompt() {
  const commandLinePrompt = process.argv.slice(2).join(" ").trim();
  if (commandLinePrompt) return commandLinePrompt;

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question("Ask KYLA: ", (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

async function main() {
  const apiKey = process.env.GEMINI_API_KEY?.trim();
  if (!apiKey || apiKey === "your_gemini_api_key_here") {
    throw new Error("Set GEMINI_API_KEY in kyla/.env before running the brain.");
  }

  const prompt = await readPrompt();
  if (!prompt) throw new Error("Please provide a prompt or type one interactively.");

  const response = await axios.post(
    GEMINI_ENDPOINT,
    {
      contents: [{ parts: [{ text: prompt }] }],
    },
    {
      headers: {
        "Content-Type": "application/json",
        "x-goog-api-key": apiKey,
      },
      timeout: 30000,
    }
  );

  const reply = (response.data?.candidates?.[0]?.content?.parts || [])
    .map((part) => part.text)
    .filter(Boolean)
    .join("\n")
    .trim();

  if (!reply) throw new Error("Gemini returned no text.");
  console.log(reply);
}

main().catch((error) => {
  const message = error.response?.data?.error?.message || error.message;
  console.error(`KYLA brain error: ${message}`);
  process.exitCode = 1;
});
