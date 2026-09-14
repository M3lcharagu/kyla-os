"""
KYLA command-line orchestrator.

Examples:
    python main.py "make a study plan"
    python main.py --room R4 --agent codex "build a Python API"
    python main.py --dry-run "research laptop options"
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "config.yaml"


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Load and validate the YAML configuration."""
    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if "rooms" not in config or "agents" not in config:
        raise ValueError("config.yaml must contain rooms and agents")

    return config


def choose_room(text: str, config: dict[str, Any], requested: str | None) -> str:
    """Use an explicit room or infer one from room aliases."""
    rooms = config["rooms"]

    if requested:
        room_id = requested.upper()
        if room_id not in rooms:
            raise ValueError(f"Unknown room: {requested}")
        return room_id

    normalized = text.lower()

    # Prefer the first matching alias.
    for room_id, room in rooms.items():
        aliases = [room_id.lower(), room["name"].lower()]
        aliases.extend(alias.lower() for alias in room.get("aliases", []))

        for alias in aliases:
            if re.search(rf"\b{re.escape(alias)}\b", normalized):
                return room_id

    return config["runtime"].get("default_room", "R1")


def dispatch(
    prompt: str,
    config: dict[str, Any],
    room_id: str | None = None,
    agent_name: str | None = None,
    dry_run: bool | None = None,
) -> str:
    """Route a prompt to a room and agent."""
    room_id = choose_room(prompt, config, room_id)
    room = config["rooms"][room_id]

    agent_name = agent_name or room.get(
        "default_agent",
        config["runtime"].get("default_agent", "shell"),
    )

    if agent_name not in config["agents"]:
        raise ValueError(f"Unknown agent: {agent_name}")

    agent = config["agents"][agent_name]
    command = agent.get("command")
    runtime_dry_run = config["runtime"].get("dry_run", True)

    if dry_run is None:
        dry_run = runtime_dry_run

    header = (
        f"[KYLA] {room_id} · {room['name']}\n"
        f"[AGENT] {agent_name} ({agent.get('mode', 'unknown')})\n"
        f"[PROMPT] {prompt}\n"
    )

    if dry_run:
        return header + "[STATUS] Dry run; nothing executed."

    if not command:
        return (
            header
            + "[STATUS] Routed but not executed.\n"
            + f"[INFO] Configure agents.{agent_name}.command in config.yaml."
        )

    if isinstance(command, str):
        argv = shlex.split(command)
    else:
        argv = list(command)

    if not argv:
        return header + "[STATUS] Agent command is empty."

    timeout = int(config["runtime"].get("timeout_seconds", 90))

    try:
        result = subprocess.run(
            argv + [prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return header + f"[ERROR] Agent timed out after {timeout} seconds."
    except OSError as exc:
        return header + f"[ERROR] Could not start agent: {exc}"

    output = (result.stdout or result.stderr).strip()
    status = "completed" if result.returncode == 0 else f"failed ({result.returncode})"

    return (
        header
        + f"[STATUS] Agent {status}.\n"
        + (output or "[INFO] Agent returned no output.")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KYLA personal AI command center")
    parser.add_argument("command", nargs="*", help="Command or question for KYLA")
    parser.add_argument("--room", help="Explicit room ID, for example R4")
    parser.add_argument("--agent", help="Explicit agent name, for example codex")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show routing without executing an agent",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to a YAML config file",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"[ERROR] Could not load config: {exc}", file=sys.stderr)
        return 1

    if args.command:
        prompt = " ".join(args.command)
        try:
            print(
                dispatch(
                    prompt,
                    config,
                    room_id=args.room,
                    agent_name=args.agent,
                    dry_run=True if args.dry_run else None,
                )
            )
        except ValueError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1
        return 0

    print("KYLA interactive mode. Type 'exit' to quit.")

    while True:
        try:
            prompt = input("kyla> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if prompt.lower() in {"exit", "quit"}:
            break

        if not prompt:
            continue

        try:
            print(dispatch(prompt, config))
        except ValueError as exc:
            print(f"[ERROR] {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
