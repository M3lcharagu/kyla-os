#!/usr/bin/env python3
"""Always-on Ruflo orchestrator wrapper for KYLA.

Policy: Ruflo is the intended default agent path (not optional).
Bootstrap via `npx ruflo@latest` when Node/npx exist. If Node is completely
unavailable, print a clear error and fall through to stack_agent / ollama.

No paid API calls are made by this wrapper. Ruflo itself may use Claude/Codex
when those CLIs/keys exist on the machine; prefer local/Ollama when configured.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _stack_dir() -> Path:
    env = os.environ.get("KYLA_STACK_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    if Path("/workspace").is_dir():
        return Path("/workspace/kyla-stack")
    return (Path.home() / "kyla-stack").resolve()


def _which(name: str) -> str | None:
    return shutil.which(name)


def node_available() -> bool:
    return bool(_which("node") and _which("npx"))


def node_major() -> int | None:
    node = _which("node")
    if not node:
        return None
    try:
        out = subprocess.check_output([node, "-v"], text=True, timeout=10).strip()
    except (subprocess.SubprocessError, OSError):
        return None
    # v20.19.2 → 20
    if out.startswith("v"):
        out = out[1:]
    try:
        return int(out.split(".", 1)[0])
    except ValueError:
        return None


def ensure_ruflo(non_interactive: bool = True) -> list[str]:
    """Return argv prefix to invoke Ruflo CLI. Auto-bootstrap via npx.

    Prefer `npx ruflo@latest`. If that fails to resolve, shallow-clone into
    KYLA_STACK_DIR/ruflo and run via npx from that tree when possible.
    """
    if not node_available():
        raise RuntimeError("Node/npx unavailable")

    major = node_major()
    if major is not None and major < 20:
        print(
            f"[RUFLO] WARN: Node {major} detected; Ruflo prefers Node 20+. "
            "On Catalina use nvm to install Node 20 if possible.",
            file=sys.stderr,
        )

    # Marker so we only run init once per stack dir (idempotent enough).
    dest = _stack_dir() / "ruflo"
    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / ".kyla_ruflo_inited"

    npx = _which("npx")
    assert npx
    base = [npx, "--yes", "ruflo@latest"]

    # Smoke: version (also warms npx cache). Soft-fail — still try hive-mind.
    try:
        subprocess.run(
            base + ["--version"],
            check=False,
            timeout=120,
            capture_output=True,
            text=True,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"[RUFLO] WARN: npx ruflo@latest --version failed: {exc}", file=sys.stderr)

    if not marker.is_file():
        init_cmd = base + ["init"]
        # Prefer non-interactive; wizard is documented for Mac handoff.
        if non_interactive:
            # Ruflo accepts plain `init` without wizard for non-interactive.
            pass
        else:
            init_cmd = base + ["init", "wizard"]
        print(f"[RUFLO] bootstrap: {' '.join(init_cmd)}", flush=True)
        try:
            # Run init in stack/ruflo so project files land there, not polluting KYLA root.
            subprocess.run(
                init_cmd,
                check=False,
                timeout=300,
                cwd=str(dest),
                env={**os.environ, "CI": "1", "npm_config_yes": "true"},
            )
            marker.write_text("ok\n", encoding="utf-8")
        except (subprocess.SubprocessError, OSError) as exc:
            print(f"[RUFLO] WARN: init soft-failed: {exc}", file=sys.stderr)
            # Still mark so we do not loop forever on flaky networks.
            try:
                marker.write_text(f"soft-fail:{exc}\n", encoding="utf-8")
            except OSError:
                pass

    # Optional clone for offline/local reference (lazy; not required for npx path).
    if os.environ.get("KYLA_CLONE_RUFLO") == "1" and not (dest / ".git").is_dir():
        print(f"[RUFLO] cloning ruvnet/ruflo into {dest}", flush=True)
        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "https://github.com/ruvnet/ruflo.git",
                    str(dest),
                ],
                check=False,
                timeout=600,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            print(f"[RUFLO] WARN: clone failed: {exc}", file=sys.stderr)

    return base


def run_ruflo(prompt: str, mode: str = "hive") -> int:
    base = ensure_ruflo(non_interactive=True)
    prompt = (prompt or "").strip() or "Reply with KYLA_RUFLO_OK"
    mode = (mode or "hive").lower()

    if mode in {"version", "doctor", "health"}:
        cmd = base + (["doctor"] if mode in {"doctor", "health"} else ["--version"])
        print(f"[RUFLO] {' '.join(cmd)}", flush=True)
        return subprocess.run(cmd, check=False).returncode

    if mode in {"swarm", "agent"}:
        # Swarm path: init topology then orchestrate task (no paid keys required for CLI scaffold).
        print("[RUFLO] swarm path (topology + task orchestrate)", flush=True)
        subprocess.run(
            base
            + [
                "swarm",
                "init",
                "--topology",
                "hierarchical",
                "--max-agents",
                "4",
                "--strategy",
                "specialized",
            ],
            check=False,
            timeout=180,
        )
        cmd = base + ["task", "orchestrate", "--task", prompt, "--strategy", "adaptive"]
        print(f"[RUFLO] {' '.join(cmd)}", flush=True)
        return subprocess.run(cmd, check=False).returncode

    # Default ALWAYS path: hive-mind spawn with the user objective.
    cmd = base + ["hive-mind", "spawn", prompt]
    print(f"[RUFLO] {' '.join(cmd)}", flush=True)
    print(
        "[RUFLO] note: Ruflo may call Claude/Codex if those exist locally; "
        "for $0 prefer Ollama + ruflo-ruvllm / provider config. See docs/RUFLO.md.",
        flush=True,
    )
    return subprocess.run(cmd, check=False).returncode


def fallthrough(prompt: str, suite: str, room: str) -> int:
    print(
        "[RUFLO] ERROR: Node.js / npx not available — cannot run always-on Ruflo.\n"
        "  Install Node 20+ (Catalina: use nvm — see docs/RUFLO.md),\n"
        "  then re-run. Falling through to stack_agent / ollama.",
        file=sys.stderr,
    )
    stack = ROOT / "tools" / "stack_agent.py"
    ollama = ROOT / "tools" / "ollama_agent.py"
    if stack.is_file():
        argv = [sys.executable, str(stack)]
        if suite:
            argv += ["--suite", suite]
        if room:
            argv += ["--room", room]
        argv.append(prompt)
        print(f"[FALLBACK] {' '.join(argv)}", flush=True)
        return subprocess.run(argv, check=False).returncode
    if ollama.is_file():
        return subprocess.run(
            [sys.executable, str(ollama), prompt], check=False
        ).returncode
    print("[FALLBACK] no stack_agent or ollama_agent found", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="KYLA always-on Ruflo agent")
    parser.add_argument("--suite", default="")
    parser.add_argument("--room", default="")
    parser.add_argument(
        "--mode",
        default=os.environ.get("KYLA_RUFLO_MODE", "hive"),
        choices=["hive", "swarm", "agent", "version", "doctor", "health"],
        help="Ruflo invocation mode (default: hive-mind spawn)",
    )
    parser.add_argument(
        "--fallback-only",
        action="store_true",
        help="Skip Ruflo and go straight to stack (debug)",
    )
    parser.add_argument("prompt", nargs="*")
    args = parser.parse_args()
    prompt = " ".join(args.prompt).strip()

    print(
        f"[KYLA/ruflo] ALWAYS-ON orchestrator  suite={args.suite or '-'} "
        f"room={args.room or '-'} mode={args.mode}",
        flush=True,
    )
    print("  https://github.com/ruvnet/ruflo  (aliases: ruflow, claude-flow)", flush=True)

    if args.fallback_only or not node_available():
        return fallthrough(prompt or "KYLA_STACK_OK", args.suite, args.room)

    try:
        return run_ruflo(prompt, mode=args.mode)
    except RuntimeError as exc:
        print(f"[RUFLO] {exc}", file=sys.stderr)
        return fallthrough(prompt or "KYLA_STACK_OK", args.suite, args.room)
    except Exception as exc:  # noqa: BLE001 — last-resort fallthrough
        print(f"[RUFLO] unexpected error: {exc}", file=sys.stderr)
        return fallthrough(prompt or "KYLA_STACK_OK", args.suite, args.room)


if __name__ == "__main__":
    raise SystemExit(main())
