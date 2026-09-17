# KYLA Hardware and Execution Architecture

## Principles

KYLA is legal-first, free/open-source first, minimal-resource, reversible, and budget-friendly. Hardware is used as a lightweight interface; persistent or heavy execution belongs in cloud services that can be paused, inspected, and kept within budget.

## R1 mobile antenna

The planned **2012 MacBook Pro as R1 mobile unit** is the R1 mobile antenna and human-facing terminal:

- **Model:** MacBook Pro 13-inch Mid 2012
- **Identifier:** MacBookPro9,2
- **CPU:** 2-core Intel i5
- **Current memory:** 8GB RAM
- **Upgrade path:** 1TB SATA SSD first, then 16GB RAM
- **Operating system:** macOS via OpenCore Legacy Patcher, capped at Monterey/Ventura
- **Role:** terminal, writing, Substack drafts, light VS Code/Node, MT5 WebTerminal only, and RustDesk client

RustDesk on the R1 Mac is a client for remoting into **CLOUD VMs**. It is not a local heavy-execution workaround and does not revive the retired Windows machine.

## Phone-first companion

The iPhone 11 remains the phone-first control and creative device. It handles mobile communication, capture, approvals, and video editing in CapCut. It should not be burdened with persistent services or speculative downloads.

## Retired hardware boundary

The Windows 11 laptop is **retired — not part of KYLA**. It is not the KYLA execution layer, not a heavy lifter, not a Docker host, and not a fallback for local backtests or AI workloads.

## Cloud-first execution layer

1. **GitHub Actions free tier** — run backtests, scripts, and CI in reproducible workflows.
2. **Vercel Hobby/free** — deploy KYLA surfaces and the KYLA dashboard within the free tier.
3. **GitHub Codespaces free hours** — provide an on-demand development environment without requiring a local heavy toolchain.
4. **Cheap VPS (~$5–6/month)** — eventual host for Docker Sandboxes when the budget allows. Keep the VPS paused, secured, and scoped to workloads that justify the recurring cost.

Docker Sandboxes run on the cloud VPS when budget allows; they are **not the official local execution layer**. The R1 Mac and iPhone are clients, not production hosts.

## Accepted trade-offs

- No local Docker sandboxes.
- No MetaTrader 5 desktop backtesting; web version only via MT5 WebTerminal.
- No local AI models.
- Video editing moved to iPhone CapCut.

This architecture keeps KYLA useful on minimal hardware while preserving a clear path to more capacity only when free tiers or the small VPS budget support it.
