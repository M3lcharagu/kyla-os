#!/usr/bin/env python3
"""CapCut-style local clip agent for YouTube / TikTok → 9:16 shorts.

Zero cloud credits: yt-dlp + faster-whisper + ffmpeg (all local).

Usage (standalone):
  python tools/clip_agent.py "https://www.youtube.com/watch?v=..."
  python tools/clip_agent.py --dry-run "clip https://tiktok.com/..."
  python tools/clip_agent.py --help

Via KYLA (R6 GULA Editing Suite):
  python main.py --room R6 --execute "clip https://youtube.com/..."

Prefers the sibling kyla-clip package when installed; otherwise runs a
built-in lightweight pipeline (heuristic highlights + ffmpeg 9:16).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "outputs" / "clips"
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)

DEFAULT_WHISPER = os.environ.get("KYLA_WHISPER_MODEL", "base")
DEFAULT_CLIPS = int(os.environ.get("KYLA_TARGET_CLIPS", "3"))
DEFAULT_MAX_SEC = float(os.environ.get("KYLA_MAX_CLIP_SECONDS", "45"))
DEFAULT_MIN_SEC = float(os.environ.get("KYLA_MIN_CLIP_SECONDS", "12"))


def extract_source(text: str) -> str | None:
    text = text.strip()
    cleaned = re.sub(
        r"^(?:clip|edit|cut|capcut|shorts?|make\s+clips?)\s+",
        "",
        text,
        flags=re.I,
    ).strip()
    m = URL_RE.search(cleaned) or URL_RE.search(text)
    if m:
        return m.group(0).rstrip(").,;]")
    candidate = Path(cleaned).expanduser()
    if candidate.exists():
        return str(candidate.resolve())
    if cleaned and not cleaned.lower().startswith(("http://", "https://")):
        if "/" in cleaned or cleaned.endswith((".mp4", ".mkv", ".mov", ".webm")):
            return cleaned
    return None


def which_or_none(name: str) -> str | None:
    return shutil.which(name)


def check_deps(need_whisper: bool = True) -> list[str]:
    missing = []
    if not which_or_none("ffmpeg"):
        missing.append("ffmpeg")
    if not which_or_none("ffprobe"):
        missing.append("ffprobe")
    if not which_or_none("yt-dlp"):
        try:
            import yt_dlp  # noqa: F401
        except ImportError:
            missing.append("yt-dlp")
    if need_whisper:
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            missing.append("faster-whisper (pip install -r requirements-clip.txt)")
    return missing


def try_kyla_clip(source: str, out_dir: Path, target: int, model: str, dry_run: bool) -> bool:
    sibling = ROOT.parent / "kyla-clip"
    src_path = sibling / "src"
    if not (src_path / "kyla_clip").is_dir():
        return False
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    try:
        from kyla_clip.config import AppConfig, TranscriptionConfig, ScoreConfig, VideoConfig, MusicConfig
        from kyla_clip.pipeline import run as clip_run
    except ImportError:
        return False
    if dry_run:
        print(f"[DRY-RUN] Would run kyla-clip pipeline on: {source}")
        print(f"[DRY-RUN] output_dir={out_dir} model={model} target_clips={target}")
        return True
    cfg = AppConfig(
        work_dir=out_dir / "_work",
        output_dir=out_dir,
        transcription=TranscriptionConfig(model=model, device="cpu", compute_type="int8"),
        scoring=ScoreConfig(
            min_clip_seconds=DEFAULT_MIN_SEC,
            max_clip_seconds=DEFAULT_MAX_SEC,
            target_clips=target,
        ),
        video=VideoConfig(width=1080, height=1920),
        music=MusicConfig(mode="none"),
    )
    cfg.work_dir.mkdir(parents=True, exist_ok=True)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = clip_run(source, cfg)
    ok = sum(1 for j in manifest.jobs if j.status == "rendered")
    fail = sum(1 for j in manifest.jobs if j.status == "failed")
    print(f"[OK] kyla-clip wrote {ok} clip(s), {fail} failed → {out_dir}")
    for job in manifest.jobs:
        reasons = ",".join(job.candidate.reasons) or "heuristic"
        print(f"  - {job.id}: {job.status} ({job.candidate.start:.1f}-{job.candidate.end:.1f}s, {reasons}) → {job.output_path}")
        if job.error:
            print(f"    error: {job.error}")
    return True


def _download(source: str, work: Path) -> Path:
    if source.startswith(("http://", "https://")):
        out_tmpl = str(work / "source.%(ext)s")
        if which_or_none("yt-dlp"):
            cmd = ["yt-dlp", "--no-playlist", "-o", out_tmpl, "--write-info-json", source]
        else:
            cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist", "-o", out_tmpl, "--write-info-json", source]
        subprocess.run(cmd, check=True)
        media = next(
            (p for p in sorted(work.glob("source.*")) if p.suffix.lower() not in {".json", ".part", ".ytdl"}),
            None,
        )
        if media is None:
            raise FileNotFoundError("yt-dlp produced no media file")
        return media
    path = Path(source).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def _probe_duration(media: Path) -> float:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(media)],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(probe.stdout)["format"]["duration"])


def _transcribe(media: Path, model: str) -> list[dict]:
    from faster_whisper import WhisperModel
    wm = WhisperModel(model, device="cpu", compute_type="int8")
    segments, _ = wm.transcribe(str(media), word_timestamps=False)
    return [
        {"start": s.start, "end": s.end, "text": (s.text or "").strip()}
        for s in segments if (s.text or "").strip()
    ]


HOOKS = ("listen", "here's why", "the truth", "you need to", "did you know", "stop", "how to", "wait")
PUNCH = ("but", "so", "that's the", "the point is", "until", "because")


def _rank(segments: list[dict], duration: float, target: int) -> list[dict]:
    scored = []
    for seg in segments:
        text = seg["text"].lower()
        score = 0.0
        reasons = []
        if any(h in text for h in HOOKS):
            score += 2.0; reasons.append("hook")
        if any(p in text for p in PUNCH):
            score += 1.5; reasons.append("punchline")
        if re.search(r"\b\d+(?:[.,]\d+)?%?\b", text):
            score += 0.8; reasons.append("number")
        if text.rstrip().endswith((".", "?", "!")):
            score += 1.0; reasons.append("complete")
        dur = seg["end"] - seg["start"]
        if 3 <= dur <= 20:
            score += 0.5
        start = max(0.0, seg["start"] - 2.0)
        end = min(duration, max(seg["end"] + 2.0, start + DEFAULT_MIN_SEC))
        end = min(end, start + DEFAULT_MAX_SEC)
        scored.append({"start": start, "end": end, "score": round(score, 3), "reasons": reasons, "text": seg["text"]})
    scored.sort(key=lambda c: c["score"], reverse=True)
    picked: list[dict] = []
    for c in scored:
        if any(abs(c["start"] - p["start"]) < DEFAULT_MIN_SEC for p in picked):
            continue
        picked.append(c)
        if len(picked) >= target:
            break
    if not picked and duration > 0:
        n = max(1, target)
        step = duration / (n + 1)
        for i in range(n):
            start = max(0.0, step * (i + 1) - DEFAULT_MIN_SEC / 2)
            end = min(duration, start + min(DEFAULT_MAX_SEC, max(DEFAULT_MIN_SEC, duration / n)))
            picked.append({"start": start, "end": end, "score": 0.0, "reasons": ["even_split"], "text": ""})
    return picked


def _burn_srt(segments: list[dict], start: float, end: float, path: Path) -> Path | None:
    lines = []; idx = 1
    for seg in segments:
        if seg["end"] < start or seg["start"] > end:
            continue
        def ts(sec: float) -> str:
            sec = max(0.0, sec - start)
            h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60); ms = int((sec - int(sec)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        lines += [str(idx), f"{ts(max(seg['start'], start))} --> {ts(min(seg['end'], end))}", seg["text"], ""]
        idx += 1
    if not lines:
        return None
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _render(media: Path, out: Path, start: float, end: float, srt: Path | None) -> None:
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    if srt is not None:
        srt_esc = str(srt).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        vf += f",subtitles='{srt_esc}':force_style='Fontsize=28,Outline=2,Alignment=2'"
    cmd = ["ffmpeg", "-y", "-ss", str(start), "-t", str(end - start), "-i", str(media),
           "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)


def run_builtin(source: str, out_dir: Path, target: int, model: str, dry_run: bool) -> int:
    missing = check_deps(need_whisper=not dry_run)
    if missing and not dry_run:
        print("[ERROR] Missing dependencies:", ", ".join(missing), file=sys.stderr)
        print("  Run: bash scripts/setup_local.sh   (or scripts/setup_local.ps1 on Windows)", file=sys.stderr)
        print("  Then: pip install -r requirements-clip.txt", file=sys.stderr)
        return 1
    if dry_run:
        print(f"[DRY-RUN] Built-in clip pipeline")
        print(f"  source={source}\n  out={out_dir}\n  whisper={model} target_clips={target}")
        print(f"  deps_ok={not check_deps(need_whisper=True)}")
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kyla-clip-") as tmp:
        work = Path(tmp)
        print(f"[1/4] Ingest {source}")
        media = _download(source, work)
        duration = _probe_duration(media)
        print(f"[2/4] Transcribe locally (faster-whisper {model}, {duration:.1f}s)")
        segments = _transcribe(media, model)
        (out_dir / "transcript.json").write_text(json.dumps(segments, indent=2), encoding="utf-8")
        print(f"[3/4] Rank highlights ({len(segments)} segments)")
        picks = _rank(segments, duration, target)
        print(f"[4/4] Render {len(picks)} vertical 9:16 clip(s)")
        jobs = []
        for i, pick in enumerate(picks, 1):
            clip_id = f"clip-{i:03d}"
            out = out_dir / f"{clip_id}.mp4"
            srt = _burn_srt(segments, pick["start"], pick["end"], work / f"{clip_id}.srt")
            try:
                _render(media, out, pick["start"], pick["end"], srt)
                status, err = "rendered", None
                print(f"  ✓ {clip_id} {pick['start']:.1f}-{pick['end']:.1f}s → {out}")
            except subprocess.CalledProcessError as exc:
                status = "failed"
                err = exc.stderr.decode("utf-8", errors="replace")[-400:] if exc.stderr else str(exc)
                print(f"  ✗ {clip_id} failed: {err}", file=sys.stderr)
            jobs.append({"id": clip_id, "start": pick["start"], "end": pick["end"], "score": pick["score"],
                         "reasons": pick["reasons"], "status": status, "output": str(out), "error": err})
        (out_dir / "manifest.json").write_text(json.dumps({"source": source, "duration": duration, "model": model, "jobs": jobs}, indent=2), encoding="utf-8")
        ok = sum(1 for j in jobs if j["status"] == "rendered")
        print(f"[DONE] {ok}/{len(jobs)} clips in {out_dir}")
        return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="clip_agent", description="Local CapCut-style clipper (YouTube/TikTok → 9:16 shorts, no cloud credits)")
    p.add_argument("prompt", nargs="*", help="URL or 'clip <url>' prompt from KYLA")
    p.add_argument("--source", help="Explicit source URL or local file path")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory (default outputs/clips)")
    p.add_argument("--clips", type=int, default=DEFAULT_CLIPS, help="Target number of shorts")
    p.add_argument("--model", default=DEFAULT_WHISPER, help="faster-whisper model (base|small|tiny)")
    p.add_argument("--dry-run", action="store_true", help="Show plan without downloading/rendering")
    p.add_argument("--builtin", action="store_true", help="Force built-in pipeline (skip kyla-clip)")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    prompt = " ".join(args.prompt).strip()
    source = args.source or (extract_source(prompt) if prompt else None)
    if not source:
        parser.print_help()
        print("\n[ERROR] Provide a YouTube/TikTok URL or local video path.", file=sys.stderr)
        return 2
    out_dir = args.out
    if not args.builtin:
        try:
            if try_kyla_clip(source, out_dir, args.clips, args.model, args.dry_run):
                return 0
        except Exception as exc:
            print(f"[WARN] kyla-clip path failed ({exc}); falling back to built-in.", file=sys.stderr)
    return run_builtin(source, out_dir, args.clips, args.model, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
