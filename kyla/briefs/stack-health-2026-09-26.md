# Kyla Stack Health — 2026-09-26T08:13:39Z

## Dry-run routes (no cloud LLM)
```
[KYLA] R6 · GULA Editing Suite
[AGENT] clip (local)
[PROMPT] clip a youtube short in gula
[SUITE] video
[STACK] clip · KYLA clip agent (CapCut-style) (wired, local/$0, R6,R7)
  https://github.com/M3lcharagu/kyla-clip
  python tools/integrations_cli.py run clip
[STATUS] Dry run; nothing executed.
[KYLA] R10 · HUMILITAS Study Room
[AGENT] stack (local)
[PROMPT] summarize my study plan
[SUITE] study
[SUITE] study — python tools/stack_agent.py --suite study
[STATUS] Dry run; nothing executed.
[KYLA] R1 · HUMANITAS Command Center
[AGENT] ruflo (local)
[PROMPT] plan my week
[SUITE] command
[ORCHESTRATOR] ruflo always-on — python tools/ruflo_agent.py
[STACK] ruflo · Ruflo (agent meta-harness) (wired, orchestrator — uses Claude/Codex when present; prefer Ollama/local bridge ($0), R1,R4,R2,R5,R10,R12,R11,R13)
  https://github.com/ruvnet/ruflo
  python tools/integrations_cli.py run ruflo
[STATUS] Dry run; nothing executed.
```

## Integrations catalog
```
KYLA stack (26)  dir=/home/runner/kyla-stack

ID                     STATUS   ON   ROOMS            CREDITS                REPO
--------------------------------------------------------------------------------------------------------------
ruflo                  wired    no   R1,R4,R2,R5,R10,R12,R11,R13 orchestrator — uses Claude/Codex when present; prefer Ollama/local bridge ($0) https://github.com/ruvnet/ruflo
ollama                 wired    yes  R1,R2,R4,R5,R10,R12 local/$0               https://github.com/ollama/ollama
clip                   wired    yes  R6,R7            local/$0               https://github.com/M3lcharagu/kyla-clip
gitingest              wired    no   R4,R12           local/$0               https://github.com/coderamp-labs/gitingest
voicebox               wired    no   R6,R7            local/$0-but-RAM-heavy https://github.com/jamiepine/voicebox
remotion               wired    no   R6,R7            local/$0               https://github.com/remotion-dev/remotion
openhands              wired    no   R4               cloud-unless-Ollama    https://github.com/All-Hands-AI/OpenHands
personalive            wired    no   R6,R8            local-GPU-or-skip      https://github.com/GVCLab/PersonaLive
mumuainovel            wired    no   R5               cloud-unless-Ollama    https://github.com/xiamuceer-j/MuMuAINovel
marketingskills        wired    no   R11,R7           local/$0               https://github.com/coreyhaines31/marketingskills
build-your-own-x       wired    no   R10,R4           local/$0               https://github.com/codecrafters-io/build-your-own-x
cli-anything           wired    no   R4               local/$0-unless-cloud-agents https://github.com/HKUDS/CLI-Anything
freedomain             wired    no   R11              local/$0               https://github.com/DigitalPlatDev/FreeDomain
agency-agents          wired    no   R1,R9,R11        local/$0               https://github.com/msitarzewski/agency-agents
graft                  wired    no   R4               local/$0               https://github.com/trailhq/Graft
codebase-memory        wired    no   R4,R2            local/$0               https://github.com/DeusData/codebase-memory-mcp
openmontage            wired    no   R6,R7            local/$0-if-no-keys    https://github.com/calesthio/OpenMontage
context7               wired    no   R4,R12           local/$0-docs          https://github.com/upstash/context7
prompts                wired    no   R2,R5            local/$0               https://github.com/f/prompts.chat
awesome-design-md      wired    no   R5,R8,R4         local/$0               https://github.com/VoltAgent/awesome-design-md
public-apis            wired    no   R12,R1,R11,R4    local/$0               https://github.com/public-apis/public-apis
agent-reach            wired    no   R12,R1,R3,R11,R4 local/$0 (free platform read) https://github.com/Panniantong/Agent-Reach
awesome-llm-apps       wired    no   R4,R1,R10,R12    local/$0               https://github.com/Shubhamsaboo/awesome-llm-apps
openviking             wired    no   R4,R12,R1        local/$0-unless-cloud  https://github.com/volcengine/OpenViking
awesome-harness-engineering wired    no   R1,R4,R2,R13     local/$0               https://github.com/ai-boost/awesome-harness-engineering
anthropic-cybersecurity-skills wired    no   R13,R4,R1        local/$0 (skills pack) https://github.com/mukul975/Anthropic-Cybersecurity-Skills
```

## 24/7 notes
- Scheduled = GitHub Actions (no Melvin laptop).
- Interactive room bots = online_bridge host + tunnel (see docs/ONLINE.md).
- This Action uses dry-run + catalog only; no paid API keys.
