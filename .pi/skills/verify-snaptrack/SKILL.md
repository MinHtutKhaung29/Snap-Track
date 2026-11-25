---
name: verify-snaptrack
description: Pointer for Snap & Track verification. Use the global verify-web-app skill with this project's .verify/ config, journeys and feature map.
---

# Snap & Track verification lives in `.verify/`

The driver is generic now. Read the global skill first: `~/.agents/skills/verify-web-app/SKILL.md`.

| what | where |
|---|---|
| contract (base_url, readiness assertions, launch, evidence) | `.verify/config.json` |
| journeys: `chat`, `receipts`, `login` | `.verify/journeys/` |
| feature map, one file per surface | `.verify/features/` (start at `README.md`) |
| app-specific scratch cleanup | `.verify/cleanup.py` |
| evidence of every run | `documents/_extract/verify/<stamp>-<journey>/` |

```bash
python ~/.agents/skills/verify-web-app/scripts/verify.py doctor --project .
python ~/.agents/skills/verify-web-app/scripts/verify.py chat   --project .
python ~/.agents/skills/verify-web-app/scripts/verify.py all    --project .
python ~/.agents/skills/verify-web-app/scripts/verify.py serve  --project .
```

Journeys run under the project venv (`.verify/config.json` → `python`), so Playwright and app imports work.

Do not add app knowledge to the global skill; put it in the config, a journey, or the feature map.
