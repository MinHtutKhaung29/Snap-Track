# DECISIONS.md

> Simple log for the repo owner. Never edit or delete old entries.

---

### 2026-11-23 — Initial Rules & Safety Setup
- **What:** Added `AGENTS.md`, safety hooks, memory, and `.gitignore`
- **Why:** Keep code simple, protect `main`, remember past work, and teach GitHub step by step
- **Files:**
  - `AGENTS.md` — main rules
  - `.agents/hooks.json` — hook config
  - `.agents/guard.js` — blocks bad edits/pushes & reminds long chats
  - `MEMORY.md` — agent memory across days
  - `DECISIONS.md` — this log
  - `.gitignore` — blocks uploading secrets & junk

### 2026-11-23 — Branch Protection & Auto-Install Tools
- **What:** Protected `main` on GitHub and added auto-install rule for Git + Node.js
- **Why:** Block collaborators from pushing directly to `main`, and let the agent install missing tools for beginners
- **Files:**
  - `AGENTS.md` — added Git + Node.js check/auto-install step
  - `DECISIONS.md` — logged this update
