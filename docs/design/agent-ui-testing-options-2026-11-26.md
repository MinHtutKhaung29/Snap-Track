# Agent UI-testing options — what is worth installing (2026-11-26)

Owner question: "make research on web first, and suggest me which skills is good. worth to take."

Context: headless screenshots and video already work (`verify-web-app` + `.verify/` journeys, 19/19 last run). What is missing is the thing the X clips show: a **browser window that stays open while the agent drives it**, so the owner watches clicks in real time. Two attempts to fake that with `tests/ui_send.py --headed` produced a window that opened, ran ~30s, then died (`TargetClosedError`) — a one-shot script cannot be watched across turns.

## The real distinction

- A **skill** (SKILL.md) is a procedure: it tells the agent how to test. It cannot show a window.
- An **MCP server or CLI** is the actual browser session. It can stay open, stay logged in, and be driven step by step across turns.

So the gap is tooling, not skills. Skills worth having are the ones that then *use* that tool.

## Candidates

| option | what it is | live window for owner | fit here | cost |
|---|---|---|---|---|
| **Playwright MCP** (`microsoft/playwright-mcp`) | official MCP server; agent gets navigate/click/type/snapshot over a persistent browser | **yes — headed by default**, `--headless` opt-in | best: Pi supports MCP (`pi mcp add`), Node 24 present, Playwright already installed | free |
| Vercel **agent-browser** | CLI tool; persistent browser between commands, `--headed` | yes | good fallback if MCP misbehaves; one more global npm package | free |
| **browser-use** (Python) | autonomous agent that decides its own clicks from screenshot + DOM | yes, plus live view | good for exploratory "find bugs yourself" runs; non-deterministic, model tokens per step | token cost |
| **Skyvern** | vision-first browser workflow engine | yes | overkill: built for scraping/automation farms, heavy infra | self-host |
| **obra/superpowers** | procedure pack (TDD, verification discipline) | no | already installed and in use | free |
| **`verify-web-app` + `.verify/`** | local skill + journeys + evidence page | no (records instead) | already working; keep as the reproducible regression layer | free |

Evidence: playwright.dev MCP docs (`https://playwright.dev/docs/getting-started-mcp`) and repo (`https://github.com/microsoft/playwright-mcp/`) confirm headed-by-default; `https://github.com/vercel-labs/agent-browser/` and `https://agent-browser.dev/installation` confirm persistent session plus `--headed`; a 2026 comparison article covers browser-use / stagehand / skyvern. Confidence: high for Playwright MCP (official docs), medium for the others (third-party).

## Recommendation

1. **Install Playwright MCP** — smallest change that gives a window to watch: `pi mcp add playwright -- npx -y @playwright/mcp@latest`. Headed is the default, and one browser session survives across turns instead of dying when a script exits.
2. **Keep `.verify/`** as the deterministic regression layer that runs headless and produces the evidence page.
3. **Skip browser-use and Skyvern for now** — they are autonomous bug hunters with an unpredictable bill. Revisit browser-use only if the owner wants the agent to explore on its own.
4. **Write one local skill** (`ui-watch`) *after* the MCP exists, encoding: start headed session → drive the changed surface → screenshot 390x844 and 1280x800 → leave the window open → tell the owner what to watch. Writing it first would repeat this session's mistake (procedure without a tool).

## Skills researched on the web (skills.sh registry, 2026-11-26)

The registry (skills.sh) and the official repos were checked, not just local skills:

| skill | source | what it actually gives | verdict |
|---|---|---|---|
| **playwright-cli** | official Playwright (`playwright-cli install --skills`; npm `playwright-cli` 0.262.0) | command surface for `open` (headed session), attach, snapshots/refs, storage state, tracing, video recording | **take it** — live window plus procedure in one vendor-owned install |
| **agent-browser** | `vercel-labs/skills` (1.7M installs, #3 on skills.sh) | shell CLI, persistent browser, `--headed`, ref-based snapshots | fallback; second choice |
| **webapp-testing** | `anthropics/skills` (official) | Playwright procedure + `with_server.py`, recon-then-act — but its own guidance says always launch **headless** | procedure yes, visibility no |
| **emil-design-eng** / **web-design-guidelines** (vercel-labs/agent-skills) | skills.sh, ~480–900K installs | front-end craft and review checklists | would have caught a text label in a circle; cheap, optional |
| **design-mobile-apps** | `designed-by-ai/skills` (1.6M installs) | mobile layout/pattern review | optional, overlaps the above |

Honest correction: the first research pass covered tools/MCP only, not the skills registry — this table is the web research she asked for. Install counts are discovery signals, not quality proof; a third-party skill runs code, so review its SKILL.md before installing.

## Provenance check — who made these, and is it worth saving (2026-11-26)

| skill | author / org | repo | stars | installs | audits (skills.sh) | SKILL.md read? |
|---|---|---|---|---|---|---|
| playwright-cli | Microsoft; npm author `Microsoft Corporation`, maintainers Pavel Feldman, Dmitry Gozman, Yury Semikhatsky (Playwright leads) | `microsoft/playwright-cli` | 15.5K | 228K | Gen Pass · Socket Pass · **Snyk Warn** | yes — 40+ commands, sessions, profiles, tracing, video; markdown instructions only, no bundled scripts |
| emil-design-eng | Emil Kowalski (Sonner/Vaul author) | `emilkowalski/skills` | 59.5K | 482K | Gen Pass · Socket Pass · **Snyk Warn** | yes — design-engineering philosophy, taste/craft rules |
| agent-browser | Vercel Labs (npm maintainers incl. `vercel-release-bot`) | `vercel-labs/agent-browser` | — | 1.7M | not checked | no |
| webapp-testing | Anthropic | `anthropics/skills` | — | — | not checked | yes — headless-only by its own rule |
| pstack (poteto) | poteto — Meta, Netflix, Cursor; React core team | `cursor/plugins` | — | — | not checked | yes — includes `/create-verification-skill`, the ancestor of our `verify-snaptrack` |

The Snyk `Warn` on two of them is not a pass. In practice these two skills are Markdown that tells the agent to run a CLI, so the risk sits in the CLI it drives, not in the skill text — but the warning is recorded here rather than hidden.

## Exact install (not executed)

```bash
pi mcp add playwright -- npx -y @playwright/mcp@latest
pi mcp list
```

Then `/mcp` inside a session to confirm connection; tools appear as `browser_navigate`, `browser_click`, `browser_type`, `browser_take_screenshot`, `browser_snapshot`.
