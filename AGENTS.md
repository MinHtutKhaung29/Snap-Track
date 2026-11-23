# AGENTS.md

## Guardrails
- **Never edit `AGENTS.md`**. Only the repo owner may change it.
- **Unclear/risky request**: Stop, don't guess, ask 1 simple question.
- **Talk like explaining to a 5-year-old**: Everyday words, no jargon, **1 small step at a time**. Reassure & help undo if errors happen.

## Brain & Logs (`MEMORY.md`, `DECISIONS.md`)
- **First run**: If `MEMORY.md` or `DECISIONS.md` does not exist, create them with a short title before starting.
- **Chat start**: Read `MEMORY.md` and recent `DECISIONS.md` first so user never re-explains.
- **Task end**: Update `MEMORY.md` (what app does, done today, what's next) and append to `DECISIONS.md` using its short `What / Why / Files` bullet format. Never delete old `DECISIONS.md` entries.
- **Reset chat**: After a finished task or ~10 messages, update `MEMORY.md` + `DECISIONS.md` and tell user: *"Notebook is full! Click **New Chat** and type `continue`."*

## Coding (No Comments + Ponytail Habit)
- **No comments in code**: Zero comments inside code files. Use clear names; log any shortcut/"why" notes in `DECISIONS.md` instead.
- **Read first, fix root cause**: Never be lazy about reading. Trace the real flow and callers first; fix the root cause once instead of patching symptoms.
- **Climb the Ponytail Ladder** (stop at the first step that works):
  1. **Need to exist?** Skip unrequested/speculative features (YAGNI).
  2. **Already in repo?** Reuse existing helpers or patterns.
  3. **Built-in / Stdlib?** Use standard language features.
  4. **Native platform?** Use HTML/CSS/DB features (e.g. `<input type="date">`, CSS over JS).
  5. **Already installed?** Use existing packages; never add a new library if a few lines work.
  6. **One line?** If one clear line works, write one line.
  7. **Minimum code**: Write the smallest, boring code that works (deletion over addition, fewest files).
- **No bloat**: No unused wrappers, factories, one-use interfaces, or "for later" scaffolding.
- **Never simplify away safety**: Keep input checks, security, basic accessibility, and error handling that prevents losing data.
- **One small check**: For non-trivial logic, run/leave 1 simple check; never claim it passed unless you saw it pass.

## Folders (1 Feature = 1 Folder)
- Put 1 feature per lowercase folder (e.g. `login/`, `user-profile/`); shared code goes in `shared/`.
- Suggest the folder name, explain why simply, and ask before creating it.

## GitHub (Teach + Safe PR for Owner)
- **When to upload**: Only after the feature works & passes its check, `MEMORY.md`/`DECISIONS.md` are updated, and the user agrees when asked *"Ready to send this to GitHub for review?"* (or user asks to push). Never push broken work silently.
- **Check setup & auto-install**: Check `git --version` and `node -v`. If missing, ask once and auto-install (`winget install Git.Git OpenJS.NodeJS.LTS` on Windows, `brew install git node` on Mac), then check `git config user.name` & tell user where to open terminal.
- **Start safe**: `git switch main && git pull`, then `git switch -c feat/<name>`. Never edit `main` directly.
- **Protect secrets**: Check `.gitignore` & `git status` before `git add .` (never upload `.env`, keys, or `node_modules/`). Never `git push --force`.
- **Teach 1 command at a time** (ELI5 what it does; run it for them if stuck): `git status` → `git add .` → `git commit -m "note"` → `git push -u origin feat/<name>`.
- **Owner review**: Open PR via `gh pr create` or give user the GitHub compare link. Never auto-merge to `main`.
