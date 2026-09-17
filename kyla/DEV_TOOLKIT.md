# KYLA DEV TOOLKIT — GitHub Gold in the Mansion

**Operating principles:** legal-first; least storage, RAM, bandwidth, and energy; fast and budget-friendly; phone-first (iPhone 11); prefer open source, local/self-hosted where practical, and reversible choices; collect only what the workflow needs.

**Hardware boundary:** the Windows 11 laptop is **retired — not part of KYLA**. It is not an execution layer or heavy lifter. KYLA is now cloud-first, with the iPhone 11 and the planned **2012 MacBook Pro as R1 mobile unit** as lightweight clients.

## Room key

R1 HUMANITAS — Command Center · R2 PATIENTIA — Second Brain · R3 TEMPERANTIA — Trading Room · R4 INDUSTRIA — Dev Lab · R5 LUXAURIA — Creative Studio · R6 GULA — Editing Suite · R7 SUPERBIA — Broadcast Room · R8 INVIDIA — Photo Studio · R9 CARITAS — Client Lounge · R10 HUMILITAS — Study Room · R11 AVARITIA — Business Ops · R12 ACEDIA — Research & Intelligence · R13 IRA — QA & Security · R14 CASTITAS — Life OS.

**Manager’s Deck:** SOPHIA oversees the whole house.

## Ten tools, fourteen rooms, one lean system

1. **[starship/starship](https://github.com/starship/starship)** — customizable terminal prompt exposing the Git branch and language/runtime version. Powered room: R4 INDUSTRIA Dev Lab. A visible, low-cost command-line uniform keeps context and version drift obvious so work stays fast and repeatable. Keep the prompt to repo, branch, runtime, and exit status; avoid noisy telemetry.
2. **[imsniff/bandwhich](https://github.com/imsniff/bandwhich)** — real-time network-traffic monitor by process and host. Powered room: R13 IRA QA & Security. Use it to answer “what is talking to the internet?” with minimal overhead while supporting legal/privacy checks and energy discipline.
3. **[tstack/lnav](https://github.com/tstack/lnav)** — terminal log viewer that merges logs, highlights errors, and supports SQL queries. Powered room: R13 IRA QA & Security. A lightweight audit-log reader turns scattered evidence into searchable QA without a heavy dashboard. Use lnav as the R13 “black box” for auth, deployment, and Docker errors; redact secrets before sharing.
4. **[brave/brave-browser](https://github.com/brave/brave-browser)** — Chromium browser with ad/tracker blocking, private search, Leo AI, and optional VPN. Powered room: R12 ACEDIA Research & Intelligence. Keep a privacy-gated research profile, private search by default, tracker blocking on, and Leo only for low-risk synthesis—not confidential inputs.
5. **[awesome-selfhosted/awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted)** — curated catalog of self-hostable open-source applications. Powered room: R12 ACEDIA Research & Intelligence, feeding R11 AVARITIA Business Ops. Treat it as a legal, budget-aware shopping list: evaluate first, install only when value beats maintenance cost.
6. **[AxoRegex/awesome-free-apps](https://github.com/AxoRegex/awesome-free-apps)** — curated free apps for Windows, macOS, Linux, and mobile. Powered room: R10 HUMILITAS Study Room. Use it to equip the 8GB client devices and iPhone without subscription creep, bloat, or speculative downloads. Build a free, light, reversible kit and benchmark it on the actual device before it enters the workflow.
7. **[xbmc/xbmc (Kodi)](https://github.com/xbmc/xbmc)** — open-source media player with plugins and skins. Powered rooms: R7 SUPERBIA Broadcast Room / R5 LUXAURIA Creative Studio. Keep local playback polished, legal, and minimal; no unlicensed streams or unnecessary add-ons.
8. **[jtroo/kanata](https://github.com/jtroo/kanata)** — cross-platform keyboard remapper with layers and macros. Powered room: R6 GULA Editing Suite, with R4 INDUSTRIA support. A few deliberate shortcuts compress repetitive editing work and conserve time, energy, and wrist motion. Video editing belongs on iPhone CapCut.
9. **[timvisee/send](https://github.com/timvisee/send)** — self-hosted encrypted file transfer with automatic expiry. Powered room: R9 CARITAS Client Lounge. Deliver client packages privately and temporarily, using one expiring link per client, clear filenames/versions, checksum when needed, and deletion after receipt.
10. **[eythaann/Seelen-UI](https://github.com/eythaann/Seelen-UI)** — desktop replacement with toolbar, dock, window manager, widgets, and CSS themes. Powered room: Manager’s Deck (SOPHIA), supporting R1 HUMANITAS. Keep this as a reference for restrained shell ergonomics, not a reason to retain retired hardware or add background load.

## Hardware and execution layers

- **R1 mobile antenna:** the planned **2012 MacBook Pro as R1 mobile unit** is the lightweight human interface. It is a MacBook Pro 13-inch Mid 2012 (MacBookPro9,2, 2-core i5, 8GB RAM), upgrading to a 1TB SATA SSD and then 16GB RAM. macOS is delivered via OpenCore Legacy Patcher and is capped at Monterey/Ventura.
- The R1 Mac is for terminal work, writing, Substack drafts, light VS Code/Node work, MT5 WebTerminal **only**, and the RustDesk client. RustDesk is used to remote into **CLOUD VMs**, never to make the retired Windows laptop the execution layer.
- **Cloud-first execution:** GitHub Actions free tier runs backtests, scripts, and CI; Vercel Hobby/free handles deployments and the KYLA dashboard; GitHub Codespaces free hours provide the development environment; and a cheap VPS at approximately **$5–6/month** is the eventual Docker Sandbox host when budget allows.
- Docker Sandboxes run on the cloud VPS when budget allows. They are **not** the official local execution layer.
- The iPhone 11 remains the phone-first control, capture, communication, and CapCut video-editing device. Use clients and remote access rather than adding local heavy services.

## Install order — cloud-first, lightweight clients

1. **Starship** — immediate R4 leverage for a consistent terminal.
2. **Brave** — privacy-first browsing and research.
3. **Kanata** — lightweight editing/productivity gains where supported.
4. **lnav** — readable logs before heavier observability.
5. **bandwhich** — on-demand network visibility.
6. **Seelen UI** — only after testing resource use on the actual client.
7. **Kodi** — only for a real local-media need.
8. **RustDesk** — for secure remote access to cloud VMs.
9. **awesome-free-apps** — consult as a catalog, not an install command.
10. **awesome-selfhosted** — consult last, then stage one service at a time on an appropriate cloud host.

**Not needed by default:** Kodi, Send, and Seelen UI are optional. Skip them until media, client delivery, or desktop-shell pain justifies their storage, setup, and background cost. The two “awesome” repositories are references, not software to install.

**SOPHIA’s rule:** if a tool is not legal, lean, reversible, phone-friendly, and useful this week, it does not enter the mansion.

## ROUND 2 — THE REPLACEMENT CAROUSEL

Round 2 tools are deliberately selected for legal/free/open-source and budget-friendly growth:

1. **[Tolgee](https://github.com/tolgee/tolgee-platform)** — open-source localization platform with in-context editing, AI translations, and translation memory. Candidate for multilingual KYLA dashboards and client website templates; localize in Swahili, Sheng, and English and keep translations editable.
2. **[Dify](https://github.com/langgenius/dify)** — production-ready agentic workflows, RAG pipelines, agents, and self-hosted/cloud/VPC deployment options. Candidate backend for KYLA agent orchestration, evaluated against the planned Kimi K3 brain; use self-hosted RAG over Substack pieces and the trading journal when appropriate.
3. **[RustDesk](https://github.com/rustdesk/rustdesk)** — open-source Rust remote-desktop tool and self-hosted alternative to TeamViewer/AnyDesk. Use official RustDesk sources, verify downloads, never trust unsolicited support requests, and use it from the R1 Mac/iPhone to access cloud VMs.
4. **[Listmonk](https://github.com/knadh/listmonk)** — self-hosted newsletter and mailing-list manager with a single binary and fast dashboard. Candidate for lean client outreach without recurring SaaS costs; use consent-based lists and clear unsubscribe handling.

### Round 2 install priority

1. **RustDesk first** — free remote access to the cloud execution layer.
2. **Listmonk second** — single binary and low overhead when outreach is needed.
3. **Dify third** — only if the planned Kimi K3 evaluation justifies the heavier service.
4. **Tolgee fourth** — when multilingual sites or dashboards start.

All four fit KYLA’s legal/free/open-source plus budget-friendly principles. Stage services one at a time, prefer free tiers, and move persistent workloads to the VPS only when the approximately $5–6/month budget is available.

## TRADE-OFFS ACCEPTED

- No local Docker sandboxes; Docker Sandboxes run on a cloud VPS when budget allows.
- No MetaTrader 5 desktop backtesting; use the MT5 WebTerminal only.
- No local AI models; use suitable cloud/free-tier or remote services with privacy and cost controls.
- Video editing moved to iPhone CapCut.

These are intentional constraints: legal, free/open-source first; minimal resources; reversible choices; and a budget-friendly, cloud-first KYLA execution architecture.
