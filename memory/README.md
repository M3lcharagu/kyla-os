# KYLA shared memory

Local long-term personal model used by Jarvis, HeyClicky, Kyla health, and Quant Mind.

## Rules

- **Do not commit real PHI, lab values, or account balances.** Only `profile.example.json` belongs in git.
- Copy the example to `profile.json` (gitignored via root `.gitignore` patterns you should keep).
- Kyla health agent may read/update a local profile when `--execute` is used; it never uploads data.
- Quant Mind may append paper-journal notes only.
- Retention, export, and delete-on-request are operator responsibilities.

## Layout

```text
memory/
  README.md
  profile.example.json
  profile.json          # local only
  health/               # optional lab extracts (local)
  quant/                # optional paper journal (local)
```

## Schema (profile)

See `profile.example.json`: goals, preferences, health_flags (non-clinical labels), quant_prefs, last_brief.
