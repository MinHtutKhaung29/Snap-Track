# AI-native speed options (no hardcoded parsing)

Date: 2026-11-26
Owner: "I want the AI brain, its understanding and reasoning, without programming hardcoded rules. So I need another solution. Make research on web and gh."

Status of the rejected approach: `app/chat/quick.py`, its test and the `handle_turn` hook were removed (tests re-run after removal: `test_ask` 38/38, `test_gate` 15/15). `settle_record()` stays, because the normal AI path uses it too.

## What the evidence says about where the seconds go

- A bare Gemini call measured here: 3.8–6.4s; with the real system prompt + tool schemas: 0.9–3.7s across runs (variance dominates, not "thinking"). Files: `tools/bench_ai.py`, `tools/bench_thinking.py`.
- End-to-end `/chat/send`: 4.4s headless, 10.0s headed (`tests/ui_perf.py`), so the model round trip is the whole cost.
- Google documents implicit and explicit **context caching** to avoid re-processing a stable prompt, and explicitly says to judge it by end-to-end TTFT p50/p95, not cache lookup time — https://aistudio.google.com/docs/caching , https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/context-cache/context-cache-overview
- Agent-latency guidance: serial model+tool steps compound; batching independent calls took a cited workload to ~2s median where serial calls were projected at 6s→51s; stream early, but note buffered tool calls and non-incremental structured output problems — https://developers.openai.com/api/docs/guides/latency-optimization
- Semantic caching (GPTCache, Vercel's write-up) can skip generation for similar requests, but similarity does not guarantee correctness, and it is unsafe for money records — https://github.com/zilliztech/gptcache , https://vercel.com/i/semantic-caching-llm-apps
- On-device small-model tool calling: one 2026 study reports 44.97% task accuracy for its best edge configuration, while project posts claim 76–149ms tool-call latency on a Raspberry Pi — fast but not trustworthy for financial records — https://arxiv.org/html/2504.19277 , https://pinoutfeed.com/article/needle-2-function-calling-model-raspberry-pi-5-tests-october-2026

## Options that keep the AI in charge

| option | what it does | expected effect | risk | verdict |
|---|---|---|---|---|
| **A. Stream the reply (SSE)** | text deltas arrive as generated, UI renders them | first words ~0.4–1.9s (measured TTFT for flash-lite by third parties) | tool-call turns still emit nothing until the call is decided; streaming + JSON needs care | **do first** |
| **B. Cache + slim the prompt** | implicit/explicit context cache; shorter system prompt, tighter tool schemas | cuts prefill on every turn, helps p95 | cache config per model; small maintenance | **do with A** |
| **C. Model + thinking tuning, measured** | keep flash-lite, set explicit thinking budget, compare p50/p95 against one stronger model for hard turns | removes long-tail spikes | needs a real benchmark harness | **do, cheap** |
| D. Parallel/compact tool results | fewer round trips when several lookups are needed | 2s median vs 6–51s serial in cited workload | only matters once there are multi-tool turns | later |
| E. Semantic cache | answer from a similar past request | very fast on hits | wrong/stale money answers | **reject** |
| F. On-device model | local reasoning + tool calls | 76–149ms claimed | 45% accuracy study; financial risk | **reject** |
| G. Draft-then-verify | fast model drafts the tool call, stronger model verifies before saving | ~1–2s to a visible draft, safe commit | two calls, queueing | optional after A/B |
| H. Two-phase UI | show the model's own intent as soon as the first tokens arrive ("記録します…") then the card | hides the tool-decision gap without faking data | must never show unverified amounts as final | **do with A** |

## GitHub survey (researcher-flash, 2026-11-26)

Metadata from the GitHub API, primary docs checked the same day.

| project | stars | last commit | license | what it gives | fit | main risk |
|---|---|---|---|---|---|---|
| `googleapis/python-genai` | 4,090 | 2026-11-25 | Apache-2.0 | official Gemini SDK; `stream_function_call_arguments=True` on Gemini 3+ (SDK ≥1.51) streams partial tool arguments | good: FastAPI `StreamingResponse` → vanilla `EventSource` | preview feature; only commit after final validated args |
| `pydantic/jiter` | 577 | 2026-11-20 | MIT | Rust-backed partial JSON parsing in Python | good: server-side previews, no JS build | truncated numbers (`12` before `1200`) mislead if shown unflagged |
| `pydantic/pydantic-ai` | 21,403 | 2026-11-26 | MIT | typed agent framework with `run_stream_events()` + Gemini | works, but adds a framework over raw calls | extra layer for one feature |
| `567-labs/instructor` | 14,145 | 2026-11-19 | MIT | streams partial Pydantic models | works | retry latency on a single worker |
| `lemony-ai/cascadeflow` | 3,921 | 2026-09-25 | MIT | draft-then-verify cascade with a FastAPI SSE guide | good for read-only Q&A | heuristic checks can miss financial errors |
| `aurelio-labs/semantic-router` | 4,049 | 2026-11-25 | MIT | millisecond embedding router fast vs strong model | good pre-call gate | misrouting money writes unless hard-overridden |

Rejected: `lm-sys/RouteLLM` (unmaintained since 2024-08), `BoundaryML/baml` (requires a DSL codegen build), `ag-ui-protocol/ag-ui` (React/TS client SDK, unneeded for plain SSE).

## Frontier consult (2026-11-26)

Two independent frontier lanes (advisor on gpt-6.2-sol, researcher-sonnet on claude-sonnet-5-5) got the same brief with the regex path marked as rejected. They converged:

- **Measure per stage before choosing a fix.** The 4.4s headless vs 10.0s headed gap suggests the model is not the only cost; instrument client → server → model call → DB → render, and keep one model call per turn (we already dispatch only the first tool call).
- **Cheapest first lever: turn thinking down explicitly.** Gemini 3 thinks dynamically by default and `thinking_level` caps it (https://ai.google.dev/gemini-api/docs/thinking); whether `gemini-3.1-flash-lite` accepts `minimal` is unconfirmed, so test it.
- **Best provider bet: fast hosted inference with tool support** — Groq lists `openai/gpt-oss-20b` at ~1000 tok/s, $0.075/$0.30 per 1M tokens, tool use, no parallel tool use (https://console.groq.com/docs/model/openai/gpt-oss-20b); Cerebras and Fireworks document tool calling too. Japanese accuracy of these small models is unverified (published MMMLU 75.7% is a warning sign).
- **Distillation is the real "AI-native but fast" endgame** — fine-tune a compact model on the owner's own labelled turns, constrained to action/arguments/abstain. High upfront work, high risk until tested on ambiguity.
- **Both refuse self-hosted GPU for a single user**, and both refuse committing money from partial or unvalidated output. Confirmation + schema validation is not "hardcoded parsing", so it stays within the owner's constraint.

## Recommendation (revised after both lanes)

1. **Instrument the turn first**: per-stage timestamps for one real message (client, server, Gemini call, DB, render), 10 runs, p50/p95. No promise until this exists.
2. **Set thinking explicitly** (`thinking_level: minimal` where supported, `thinking_budget: 0` on 2.5 models) and measure the delta on the same harness.
3. **Bake off Gemini vs Groq `gpt-oss-20b`** on 20 real Japanese money messages, scoring latency and tool-call correctness; keep money on the strong side, route read-only Q&A to the fast one only if it wins.
4. **Slim the prompt and tool schemas + implicit caching**, since those help every turn including tool calls.
5. **Stream progress, never numbers** (`python-genai` partial tool args), and only after 1–3 show it is worth it.
6. **Distillation** is a later project, not this week: it needs a labelled set of the owner's real turns.

## What must still be true after any change

- Amounts and categories still come only from the model's tool call or the user's typed answer.
- No answer is ever shown as saved before the server stores it.
- `tests/test_ask.py`, `test_gate.py`, `test_confirm.py`, `test_commitments.py`, `test_extract.py` stay green.
