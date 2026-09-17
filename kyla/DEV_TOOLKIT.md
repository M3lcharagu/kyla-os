# KYLA DEV TOOLKIT — GitHub Gold in the Mansion

**Operating principles:** legal-first; least storage, RAM, bandwidth, and energy; fast and budget-friendly; phone-first (iPhone 11) with a Windows 11 laptop limited to 8GB RAM and no GPU. Prefer open source, local/self-hosted, reversible choices; collect only what the workflow needs.

**Room key:** R1 HUMANITAS — Command Center · R2 PATIENTIA — Second Brain · R3 TEMPERANTIA — Trading Room · R4 INDUSTRIA — Dev Lab · R5 LUXURIA — Creative Studio · R6 GULA — Editing Suite · R7 SUPERBIA — Broadcast Room · R8 INVIDIA — Photo Studio · R9 CARITAS — Client Lounge · R10 HUMILITAS — Study Room · R11 AVARITIA — Business Ops · R12 ACEDIA — Research & Intelligence · R13 IRA — QA & Security · R14 CASTITAS — Life OS. **Manager’s Deck:** SOPHIA oversees the whole house.

## Ten tools, fourteen rooms, one lean system

1. **starship/starship** · **Function:** A customizable terminal prompt that exposes the Git branch and language/runtime version. 
 **Powered room — R4 INDUSTRIA Dev Lab:** A visible, low-cost command-line uniform makes context and version drift obvious, so work stays fast and repeatable. 
 **Creative integration:** Make Starship the R4 “uniform”: a two-line, high-contrast prompt with only repo, branch, runtime, and exit status—no noisy telemetry.

2. **imsnif/bandwhich** · **Function:** Real-time network-traffic monitor by process and host. 
 **Powered room — R13 IRA QA & Security:** It answers “what is talking to the internet?” with minimal overhead, supporting legal/privacy checks and energy discipline. 
 **Creative integration:** Keep it as the **Docker Sandbox network watch**: open it before tests, spot unexpected hosts, then stop the container or remove the dependency.

3. **tstack/lnav** · **Function:** Terminal log viewer that merges logs, highlights errors, and supports SQL queries. 
 **Powered room — R13 IRA QA & Security:** One lightweight audit-log reader turns scattered evidence into fast, searchable QA without a heavy dashboard. 
 **Creative integration:** Use lnav as the R13 “black box”: a saved format/query set for auth, deployment, and Docker errors; redact secrets before sharing.

4. **brave/brave-browser** · **Function:** Chromium browser with ad/tracker blocking, private search, Leo AI, and optional VPN. 
 **Powered room — R12 ACEDIA Research & Intelligence:** A privacy-gated research browser reduces tracking, page weight, and distraction while keeping familiar web compatibility. 
 **Creative integration:** Make a R12 “research gate”: separate profile, private search by default, tracker blocking on, and Leo only for low-risk synthesis—not confidential inputs.

5. **awesome-selfhosted/awesome-selfhosted** · **Function:** Curated catalog of self-hostable open-source applications. 
 **Powered room — R12 ACEDIA Research & Intelligence (feeding R11 AVARITIA Business Ops):** It is a legal, budget-aware shopping list for KYLA services—evaluate first, install only when value beats maintenance cost. 
 **Creative integration:** Turn its entries into a one-page KYLA backlog tagged **need / nice / never**; shortlist phone-friendly, low-RAM services before buying hardware.

6. **Axorax/awesome-free-apps** · **Function:** Curated free apps for Windows, macOS, Linux, and mobile. 
 **Powered room — R10 HUMILITAS Study Room:** It equips the 8GB laptop and iPhone without subscription creep, bloat, or speculative downloads. 
 **Creative integration:** Build a “free, light, reversible” kit: one app per job, portable where possible, benchmarked on the actual laptop before it enters the house.

7. **xbmc/xbmc (Kodi)** · **Function:** Open-source media player with plugins and skins. 
 **Powered room — R7 SUPERBIA Broadcast Room / R5 LUXURIA Creative Studio:** Local playback gives the media pipeline a polished front end without a cloud bill; keep plugins legal and minimal. 
 **Creative integration:** Make Kodi the **penthouse media lounge**: a local library, one dark skin, hardware-friendly playback, and no unlicensed streams or unnecessary add-ons.

8. **jtroo/kanata** · **Function:** Cross-platform keyboard remapper with layers and macros. 
 **Powered room — R6 GULA Editing Suite (with R4 INDUSTRIA):** A few deliberate shortcuts compress repetitive editing work and conserve time, energy, and wrist motion. 
 **Creative integration:** Add a “CapCut layer” for content-edit shortcuts—cut, split, ripple/delete, marker, export—while preserving a safe base layer and an instant emergency toggle.

9. **timvisee/send** · **Function:** Self-hosted encrypted file transfer with automatic expiry. 
 **Powered room — R9 CARITAS Client Lounge:** It delivers client packages directly, privately, and temporarily, reducing attachment limits, cloud sprawl, and retained copies. 
 **Creative integration:** Use Send for website handoffs from R9: one expiring link per client, clear filename/version, checksum when needed, and deletion after receipt.

10. **eythaann/Seelen-UI** · **Function:** Windows desktop replacement with toolbar, dock, window manager, widgets, and CSS themes. 
 **Powered room — Manager’s Deck (SOPHIA), supporting R1 HUMANITAS:** A restrained shell makes the laptop phone-like, navigable, and focused without buying a new machine; keep widgets sparse for 8GB RAM. 
 **Creative integration:** Theme it as a **dark penthouse Manager’s Deck** on the Windows laptop: dock = rooms, one status strip = SOPHIA, no animated wallpaper, and a low-power profile.

## Install order — Windows 11, 8GB RAM, no GPU

1. **Starship** — tiny, immediate R4 leverage; 2. **Brave** — daily privacy and lighter browsing; 3. **Kanata** — instant editing/productivity gain; 4. **lnav** — lightweight logs before heavier observability; 5. **bandwhich** — on-demand network visibility; 6. **Seelen UI** — install only after testing RAM use; 7. **Kodi** — only for a real local-media need; 8. **Send** — deploy when a client handoff requires it; 9. **awesome-free-apps** — consult as a catalog, not an install; 10. **awesome-selfhosted** — consult last, then stage one service at a time.

**Not needed by default:** Kodi, Send, and Seelen UI are optional—skip them until media, client delivery, or desktop-shell pain justifies their storage, setup, and background cost; the two “awesome” repositories are references, not software to install.

**SOPHIA’s rule:** if a tool is not legal, lean, reversible, phone-friendly, and useful this week, it does not enter the mansion.

## ROUND 2 — THE REPLACESO CAROUSEL

1. **Tolgee** ([github.com/tolgee/tolgee-platform](https://github.com/tolgee/tolgee-platform), ~4.1k stars) · **Description:** An open-source localization platform with in-context editing, AI translations, and translation memory. **Powered room — R5 LUXURIA Creative Studio:** It powers multilingual dashboard and website-template work because polished, editable translations make client sites more useful and sellable. **Creative integration:** Localize KYLA dashboard and website templates in Swahili/Sheng/English; sell 3-language sites as a client upgrade; edit translations directly in the site preview.

2. **Dify** ([github.com/langgenius/dify](https://github.com/langgenius/dify)) · **Description:** Production-ready agentic workflows, RAG pipelines, agents, and self-hosted/cloud/VPC deployment options. **Powered room — R2 PATIENTIA Second Brain:** It powers durable agent orchestration and retrieval because KYLA can evaluate it against the planned Kimi K3 brain while keeping knowledge local when needed. **Creative integration:** Make Dify a candidate backend for KYLA agent orchestration, evaluated against the planned Kimi K3 brain; self-host RAG over Substack pieces and the trading journal for R2 PATIENTIA.

3. **RustDesk** ([github.com/rustdesk/rustdesk](https://github.com/rustdesk/rustdesk), ~124k stars) · **Description:** An open-source Rust remote-desktop tool and self-hosted alternative to TeamViewer/AnyDesk. **Powered rooms — R13 IRA QA & Security + R4 INDUSTRIA Dev Lab:** It powers secure remote access and troubleshooting across the QA/security and development rooms. **Scam warning:** Use only official RustDesk sources/site and verify downloads; never trust unsolicited support requests or share access codes. **Creative integration:** Make KYLA phone-first: control the Windows 11 laptop from an iPhone 11, demo client websites from the phone during pitches, and access Docker sandboxes remotely.

4. **Listmonk** ([github.com/knadh/listmonk](https://github.com/knadh/listmonk), ~23k stars) · **Description:** A self-hosted newsletter and mailing-list manager with a single binary and fast dashboard. **Powered room — R11 AVARITIA Business Ops:** It powers lean client outreach because a self-hosted, low-overhead list can manage leads without recurring SaaS costs. **Creative integration:** Build an email list for past and potential website clients and run the campaign “3-day website special KSh 9,000,” with follow-ups to leads Stylush, Leijona, KROSSFIT, Carspa, Vogue, Geco, and Zuri's.

### Install priority — Windows 11 laptop, 8GB RAM, budget

1. **RustDesk first** — free remote access, immediate value.
2. **Listmonk second** — single binary, low RAM.
3. **Dify third** — only if Kimi K3 evaluation fails, heavier.
4. **Tolgee fourth** — only when multilingual sites start.

All four fit KYLA’s legal/free/open-source + budget-friendly principle.
