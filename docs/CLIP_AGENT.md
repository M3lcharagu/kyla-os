# CapCut-style clip agent (local)

Turn YouTube or TikTok URLs into vertical **9:16** shorts on your machine — no CapCut cloud, no Whisper API, no LLM credits for ranking.

## Pipeline

```text
URL / file
  → yt-dlp ingest
  → faster-whisper (local, model base/small)
  → heuristic highlight rank (hooks, punchlines, numbers, silence)
  → ffmpeg trim + 9:16 crop + burned captions
  → outputs/clips/clip-001.mp4 … + manifest.json
```

When the sibling repo `kyla-clip` is installed (`pip install -e ../kyla-clip`), KYLA prefers that full pipeline (scene-detect, ASS captions, loudnorm, music policy). Otherwise `tools/clip_agent.py` uses its built-in lightweight path.

## Commands

```bash
# Help / dry-run (no download)
python tools/clip_agent.py --help
python tools/clip_agent.py --dry-run "https://www.youtube.com/watch?v=jNQXAC9IVRw"

# Render shorts
python tools/clip_agent.py "https://www.youtube.com/watch?v=jNQXAC9IVRw"
python tools/clip_agent.py --clips 5 --model base "clip https://www.tiktok.com/@.../video/..."

# Via KYLA room R6 (GULA Editing Suite)
python main.py --room R6 --execute "clip https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

Outputs land in `outputs/clips/` (gitignored media; manifests are fine to inspect).

## Dependencies

Base KYLA stays light. Install the video stack only when needed:

```bash
pip install -r requirements-clip.txt
# needs system ffmpeg + ffprobe
# Linux Mint: sudo apt install ffmpeg
# Windows:    winget install Gyan.FFmpeg
```

Optional: `auto-editor` (installed by setup scripts) for silence trimming before ranking:

```bash
auto-editor input.mp4 --edit audio:threshold=0.04 -o work/tight.mp4
python tools/clip_agent.py --source work/tight.mp4
```

## Editorial rules (from kyla-clip)

- Confirm you have permission to use the source.
- Review every clip before posting (captions, crop, context, music).
- Music modes in kyla-clip: `none` | `licensed_file` | `add_in_tiktok` — never invent a license.
- Mel remains the final publisher.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Missing ffmpeg | Install ffmpeg; reopen terminal |
| Out of memory on whisper | Use `--model tiny` or `base` (not `small`/`medium` on 8GB) |
| yt-dlp fails TikTok | Update yt-dlp; try cookies if needed (your responsibility) |
| ASS/subtitles fail | Built-in path falls back to SRT burn-in; check font |
| Want full CapCut feature set | Use `../kyla-clip` CLI: `python -m kyla_clip.cli run --source URL` |
