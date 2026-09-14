"""
Provider-neutral WhatsApp and Docker stubs.

This file does not connect to WhatsApp or Docker automatically.

Future WhatsApp webhook code can call:

    handle_whatsapp_payload({
        "sender": "+254...",
        "text": "make a study plan"
    })

The WhatsApp provider should perform authentication, webhook verification,
and outbound message sending outside this starter module.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from typing import Any

from main import dispatch, load_config


def handle_whatsapp_payload(payload: dict[str, Any]) -> str:
    """
    Route an inbound WhatsApp-like payload into KYLA.

    Expected payload:
        {
            "sender": "+254700000000",
            "text": "help me study Python"
        }
    """
    text = str(payload.get("text", "")).strip()

    if not text:
        return "No text message received."

    config = load_config()

    # Keep external execution disabled until deliberately enabled.
    execute = os.getenv("KYLA_EXECUTE", "0") == "1"

    return dispatch(
        prompt=text,
        config=config,
        dry_run=not execute,
    )


def run_docker_sandbox(
    image: str,
    command: list[str] | str,
    config_path: str = "config.yaml",
) -> str:
    """
    Run an explicitly allowed command in a restricted Docker container.

    This is a local stub for the future docker-agent. It does not use a shell.
    """
    if os.getenv("KYLA_ENABLE_DOCKER", "0") != "1":
        return "[DOCKER] Disabled. Set KYLA_ENABLE_DOCKER=1 to enable."

    config = load_config()
    allowed_images = config["runtime"].get("allowed_docker_images", [])

    if image not in allowed_images:
        return f"[DOCKER] Image is not allow-listed: {image}"

    argv = shlex.split(command) if isinstance(command, str) else list(command)

    if not argv:
        return "[DOCKER] No command supplied."

    docker_args = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--cpus=1",
        "--memory=512m",
        "--pids-limit=128",
        "--tmpfs=/tmp",
        image,
        *argv,
    ]

    timeout = int(config["runtime"].get("timeout_seconds", 90))

    try:
        result = subprocess.run(
            docker_args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return f"[DOCKER] Timed out after {timeout} seconds."
    except OSError as exc:
        return f"[DOCKER] Could not start Docker: {exc}"

    output = (result.stdout or result.stderr).strip()
    status = "completed" if result.returncode == 0 else f"failed ({result.returncode})"

    return f"[DOCKER] {status}\n{output or '[No output]'}"


if __name__ == "__main__":
    # Local smoke test:
    print(
        handle_whatsapp_payload(
            {
                "sender": "local-test",
                "text": "create a study plan for Python",
            }
        )
    )
