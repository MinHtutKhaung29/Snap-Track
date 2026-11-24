# Snap & Track — P0–P2 Implementation Plan

Persisted from an independent planning pass (2026-11-24) that read `docs/base-plan.md` in full. Task level: files, routes, interfaces, Gemini contracts, indexed SQL, and named tests. `DECISION NEEDED` marks anything the base plan left open.

Status: **draft pending v3 reconciliation** — the independent review of the base plan found schema and safety defects that this document may still reflect. Read `docs/base-plan.md` v3 for the corrected contracts before building from this.

---

# Snap & Track — P0–P2 Implementation Plan (as delivered)

**Goal:** Boot the app on Windows, file typed expenses and income in one private chat thread, and turn receipt photos into a swipe queue without putting unconfirmed money in the ledger.

**Architecture:** FastAPI serves Jinja2 pages and uses `mysql-connector-python` against MySQL 8.4. The server owns validation, confirmation, and SQL writes; Gemini proposes actions and reads receipt images. Each user has one durable thread, with pending text confirmations in `chat_message.payload` and the receipt queue derived from `receipts` and `transactions`.

**Stack:** Python 3.13 via `py -3.13`, FastAPI, Jinja2, Starlette `SessionMiddleware`, `hashlib.scrypt`, MySQL 8.4, `mysql-connector-python`, `google-genai` pinned to model ID `gemini-3.1-flash-lite`, and plain JavaScript pointer events.

**Spec:** `docs/base-plan.md`. Receipt evidence: `docs/p005-technical-validation.md` and `documents/_extract/p005/run_real.py`.

## Scope and decisions

- **P0, 11/24–11/27:** clean install, seven-table schema, nine categories, green DB-backed health check.
- **P1, 11/30–12/06:** register, sign in/out, private thread, typed expense/income, inferred-date confirmation, 24-hour undo.
- **P2, 12/07–12/13:** image upload and read, stacked receipt cards, save/correct/discard/re-read, receipt undo.
- **Not in P0–P2:** commitment UI or writes, AI aggregates, fact writes or history summarization, standalone money list/edit/filter pages, app-install packaging, or later hardening work. `app/money/` supplies ledger persistence in P1; `app/commitments/` gets no files or router until P3. The seven tables still ship in P0.
- Use whole yen, parameterized SQL, and a server-derived `user_id` on every user-data operation. Global categories and credential lookup by email are the exceptions. Photos and inferred dates never cause an unsolicited ledger write. Never default an amount or category.
- No comments in proposed or implemented code, including SQL and JS. Record reasons and approved deviations in `DECISIONS.md`; do not edit the base plan as part of these tasks.

| Decision | Recommended contract used below | If not accepted |
|---|---|---|
| **DECISION NEEDED D1 — Dates, evidence, and retries** | Use `Asia/Tokyo` for “today” and UTC for DB timestamps. Require independent proof of the amount and explicit date for an immediate save. For safely resolved inferred dates, including omitted date → today, always show a confirmation. Refuse unresolved or future transaction dates. Never auto-resubmit a typed message after a lost response. | Freeze the parser cases and phone test expectations before P1. Trusting model evidence or auto-replaying a send can file wrong or duplicate money. |
| **DECISION NEEDED D2 — HTTP, account, and P0 health defaults** | Use the form routes below, redirects after successful POSTs, a 30-character-minimum session secret, CSRF tokens, 8–128-character passwords, lowercased email, and a DB-backed health check. Register redirects to sign-in. Secure cookies except for explicit trusted-local development. | Change route and test contracts together before building. Do not silently weaken ownership or CSRF checks. |
| **DECISION NEEDED D3 — Receipt queue and correction** | Discard by setting `pending` with `extracted=NULL`; preserve the image and require an explicit re-read. A valid but incomplete receipt is `done`, asks for the first missing field, and can only be saved via completed correction. Require an extraction ID on save/discard. Number cards against the current queue after each reload, not a historical batch. | Resolve before P2. Leaving a discarded receipt `done` and unlinked puts it straight back on the queue. |
| **DECISION NEEDED D4 — Image and failure limits** | Accept decoded JPEG/PNG/WebP, at most 12 MiB and 24 million pixels, with a 15-second provider timeout and a 60-second stale processing lease. Verify native phone capture; do not add HEIC conversion or client resizing unless the real-phone gate shows it is needed. | Approve supported formats and recovery behavior before P2. Without a stale-state rule, a process crash can strand a receipt. |
| **DECISION NEEDED D5 — Gates and cost control** | Time P2 from the first camera-open tap through display of the fifth saved card; demonstrate misread correction separately. Before live P2 acceptance, run the owner’s 10-receipt proof. Keep the model pin unless the owner approves the documented fallback after a result below 8/10. Record usage during the proofs and set daily-cap size/enforcement separately before shared deployment; the base plan gives no cap value or enforcement contract. | Record the approved timing/proof/cap contract. Do not report a timed or live gate as passed from mocked tests. |
| **DECISION NEEDED D6 — Deferred product questions** | Keep fixed seed categories and manual-only bill posting; no schedule change based on unconfirmed school dates or team paperwork. P3 must resolve commitment start dates versus §5’s “no date beyond today”; recommend future commitments be allowed while future *transactions* are forbidden. P4 must approve the query scope and fact rules below before exposing those tools. | No P0–P2 code depends on the deferred decision. Flag any changed requirement before that later phase. |

## Current-state delta

| Area | State before P0 |
|---|---|
| App, schema, test harness | **Missing** in the inspected workspace; architectural definitions exist in the base plan. |
| Receipt Gemini proof | **Partial**: Commons dataset amount 4/5, date 5/5, zero guesses on unknown fields; owner’s 10 receipts still outstanding. |
| Chat Gemini proof | **Missing**: ten sentences with expected tool and arguments have not been run. |
| Receipt discard and pending predicate | **Conflicting unless resolved**: `done` + no linked ledger row means queued; discard therefore must change status or the predicate. This plan changes status only. |
| Application secrets and MySQL service availability | **Unknown now**. The base plan recorded MySQL absent on 2026-11-24. The validation report requires revoking the key used in the earlier proof. |

## Ordered implementation tasks

### P0-01 — Bootstrap, schema, seed, and health

**Objective and boundary:** Deliver a clean Windows install and a single DB-backed health endpoint. No login, model calls, ledger writes, or upload mount. One writer owns all P0 files.

| Create | Purpose / owned symbols |
|---|---|
| `.gitignore` | Exclude `.venv/`, `.env`, `uploads/`, and Python/test caches. |
| `.env.example` | Document non-secret P0 DB settings and placeholders. |
| `requirements.txt` | Runtime dependencies: FastAPI, Uvicorn, Jinja2, `mysql-connector-python`, and `python-dotenv`. |
| `requirements-dev.txt` | Include runtime requirements plus `pytest` and `httpx`. |
| `README.md` | Windows setup, DB provision, boot, health check, and test commands. |
| `DECISIONS.md` | Record approved choices and deviations without code comments. |
| `app/__init__.py`, `app/shared/__init__.py` | Package markers. |
| `app/main.py` | `create_app`, health route, and application wiring. |
| `app/shared/config.py` | `Settings`, `load_settings`, `ConfigError`. |
| `app/shared/db.py` | `db_connection`, `DatabaseError`, `CommitOutcomeUnknown`. |
| `app/shared/templates/base.html` | Shared HTML shell, viewport and stylesheet link. |
| `app/shared/static/base.css` | Mobile-first base layout and readable forms. |
| `db/schema.sql` | The seven tables, keys and indexes from base plan §4. |
| `db/seed.sql` | Idempotent insertion/update of the nine fixed categories. |
| `tests/conftest.py` | Application fixtures and isolated MySQL settings. |
| `tests/test_p0.py` | Schema, seed, config, and health tests. |

**Shared contracts**

- `load_settings() -> Settings`: read `.env` and environment, with real environment variables taking precedence. P0 keys: `SNAPTRACK_DB_HOST`, `SNAPTRACK_DB_PORT`, `SNAPTRACK_DB_USER`, `SNAPTRACK_DB_PASSWORD`, `SNAPTRACK_DB_NAME`. Default host/port `127.0.0.1`/`3306`; missing required values or invalid typed values raise `ConfigError`. Never include secret values in errors.
- `create_app(settings: Settings | None = None) -> FastAPI`: supplied settings are the test seam; otherwise call `load_settings()`. Raise `ConfigError` if configuration is invalid. Do not open MySQL or Gemini during creation.
- `db_connection(settings: Settings) -> AbstractContextManager[MySQLConnectionAbstract]`: one connector connection per use, `utf8mb4`, autocommit off, UTC session timezone, `READ COMMITTED`. Commit once on normal exit; roll back on body failure and close on every exit. Translate connector failures to `DatabaseError` with the connector `errno` available to the caller; preserve non-connector exceptions. If a lost connection leaves commit outcome indeterminate, raise `CommitOutcomeUnknown`, a `DatabaseError` subtype. Never replay a write automatically. Routes use regular synchronous handlers for blocking connector/provider operations.

**HTTP and SQL**

| Method/path | Request | Response and template | SQL/index |
|---|---|---|---|
| `GET /health` | None | `200 {"status":"ok"}`; DB failure `503 {"status":"unavailable"}`. No template. | `SELECT 1 AS ok;` No table or index. |
| `GET /docs` | None | FastAPI-generated Swagger UI HTML; no Jinja2. | None. |
| `GET /openapi.json` | None | FastAPI-generated OpenAPI JSON. | None. |
| `GET`, `HEAD /static/{path:path}` | Asset path | Static file or `404`; no Jinja2. | None. |

Disable ReDoc and the unused Swagger OAuth redirect. Mount **only** `app/shared/static/`, never `uploads/`. Health checks connectivity, not whether the schema and seed were applied; acceptance verifies those independently.

**DB contract:** Copy the §4 definitions verbatim in dependency order: `users`, `categories`, `receipts`, `transactions`, `commitments`, `chat_message`, `memory_fact`. Use InnoDB and an `utf8mb4` database. Do not add an unapproved `fk_txn_commit`, queue table, or session identifier. Seed category labels and codes exactly as specified. Assign `sort_order` 1–6 for expense and 1–3 for income in base-plan order. Seed upserts by `uq_category(kind,code)`; a second run changes neither IDs nor count. `schema.sql` is a first-install script for an empty DB, not a destructive migration or an upgrade script.

**Build order**
1. [ ] Add configuration/dependencies, test DB guard, and tests. Integration fixtures use explicit `SNAPTRACK_TEST_DB_*` settings and refuse a DB name not ending in `_test`; fixtures must never reset or delete from the demo DB.
2. [ ] Provision MySQL and apply the schema then seed to the isolated DB. Add `db_connection`; verify its transaction and exception behavior.
3. [ ] Add app factory, static mount, template shell, and health. Run the P0 tests.
4. [ ] Run the README in a fresh PowerShell terminal against a fresh demo database. Record MySQL version, seed count, and health response before checkpointing P0.

**Tests**
- `test_config_rejects_missing_db_name` — missing DB name raises `ConfigError` before any connector call.
- `test_schema_has_seven_tables` — `SHOW TABLES` on the clean test DB returns exactly `users`, `categories`, `receipts`, `transactions`, `commitments`, `chat_message`, `memory_fact`.
- `test_seed_is_repeatable` — after applying `seed.sql` twice, the same nine category IDs, codes, kinds, labels, and sort orders remain.
- `test_db_rolls_back_body_failure` — insert in a DB context and raise `RuntimeError`; caller observes that error and a fresh connection finds zero matching rows.
- `test_health_green` — configured MySQL returns HTTP 200 with exactly `{"status":"ok"}`.
- `test_health_db_unavailable` — connector failure returns HTTP 503 with exactly `{"status":"unavailable"}` and never discloses a host, username, or password.

**Validation and handoff:** Bootstrap using the commands in “Validation and rollback,” then run `.\.venv\Scripts\python.exe -m pytest -q tests/test_p0.py`; all tests pass. Artifacts: fresh-install README, schema/seed, test output, health response. Reviewer checks schema parity, connection cleanup and non-disclosure. If P0 fails, discard only the newly created test database or clean demo database after confirming it contains no user data; do not reset a populated DB. Residual risk: Windows PATH/service setup varies; MariaDB is mentioned as a fallback in the spec, not accepted as a substitute for the MySQL 8.4 phase gate.

### P1-01 — Accounts and one private thread

**Objective and boundary:** Deliver register, sign-in/out and private read-only thread rendering before attempting AI writes. No public user IDs or client-supplied `user_id`; no model dependency for viewing the thread.

| Create or modify | Purpose / owned symbols |
|---|---|
| `app/login/__init__.py` | Package marker. |
| `app/login/routes.py` | `router`, register/sign-in/sign-out handlers and account SQL. |
| `app/login/templates/login/register.html`, `app/login/templates/login/login.html` | CSRF-protected account forms. |
| `app/shared/auth.py` | `require_user`, `require_csrf`, `csrf_token`, `hash_password`, `verify_password`, auth exceptions. |
| `app/shared/templates/error.html` | Generic HTML error page; no upstream error or secrets. |
| `app/chat/__init__.py` | Package marker. |
| `app/chat/routes.py` | `router`, root and `GET /chat`; write handlers come in P1-02. |
| `app/chat/templates/chat/thread.html` | Permanent thread, escaped bodies, and a slot for the composer/cards in P1-02. |
| Modify `app/main.py`, `app/shared/config.py`, `app/shared/templates/base.html` | Session/template wiring, error handlers, navigation. |
| Modify `.env.example`, `requirements.txt`, `README.md`, `tests/conftest.py` | Session settings, `itsdangerous` and `python-multipart`, fixture users, local settings. |
| `tests/test_p1_auth.py` | Account, CSRF, and thread isolation tests. |

**Shared auth contracts**

- `require_user(request: Request) -> int`: FastAPI dependency. Accept only a positive integer `user_id` from the verified Starlette session. Raise `LoginRequired` otherwise; app handler responds `303 Location: /login`, including for private POST routes. No DB call. No auth decorator is needed.
- `csrf_token(request: Request) -> str`: return the current session token or create one with `secrets.token_urlsafe(32)`. `require_csrf(request: Request, submitted_token: str | None) -> None`: constant-time comparison with the existing token; missing/mismatch raises `CsrfRejected`, mapped to `403 error.html`. Private POSTs authenticate before checking CSRF, then check CSRF before parsing business fields or touching the DB.
- `hash_password(password: str) -> str` and `verify_password(password: str, encoded_hash: str) -> bool`: UTF-8, fresh random 16-byte salt, scrypt `n=16384, r=8, p=1, dklen=64`; persist `scrypt$` followed by hex salt and digest separated by `$`. Return `False` for wrong password or malformed stored hash. Scrypt runtime failure raises `PasswordHashError`, mapped to generic 500 HTML. Never log password/form bodies.
- Add `SNAPTRACK_SESSION_SECRET` (at least 30 characters) and `SNAPTRACK_COOKIE_SECURE` (default true). Use signed `HttpOnly`, `SameSite=Lax` session cookies; store only `user_id` and CSRF token. Clear and issue a fresh CSRF token on login; clear session on logout. Use an explicit `false` only for local HTTP on a trusted network.

**HTTP contracts**

All POSTs below are `application/x-www-form-urlencoded`. Required missing/invalid form fields return 422 in the indicated form template; login credential failure returns that same login template at 401 with one generic error. Database outage returns `503 error.html`.

| Method/path | Fields | Response/template | SQL |
|---|---|---|---|
| `GET /` | None | `303 /chat` with valid session; otherwise `303 /login`. No template. | None. |
| `GET /register` | None | `200 login/register.html`. | None. |
| `POST /register` | `name`, `email`, `password`, `csrf_token` | `303 /login`; duplicate email `409 login/register.html`; invalid fields `422 login/register.html`. | A1 |
| `GET /login` | None | `200 login/login.html`. | None. |
| `POST /login` | `email`, `password`, `csrf_token` | `303 /chat` after session rotation; `401 login/login.html` for bad credentials. | A2 |
| `POST /logout` | `csrf_token` | `303 /login`; clears session. | None. |
| `GET /chat` | None | `200 chat/thread.html`, one owned thread in message-ID order; private, `Cache-Control: no-store`. | A3; P1-02 adds card joins. |

Trim `name`, 1–80 characters. Trim/lowercase `email`, at most 255 characters, one `@`, nonempty sides, no whitespace. Keep password characters unchanged; accept 8–128 characters. Map duplicate email using connector duplicate-entry error, not a racy preflight check. CSRF failure is 403 even on public form POSTs.

```sql
INSERT INTO users (name, email, password_hash)
VALUES (%(name)s, %(email)s, %(password_hash)s);

SELECT user_id, password_hash FROM users WHERE email = %(email)s;

SELECT message_id, role, body, payload, created_at
FROM chat_message
WHERE user_id = %(user_id)s
ORDER BY message_id;
```

A1 writes `PRIMARY` and enforces unique `users.email`; A2 uses that unique index. A3 uses `idx_chat_user(user_id,message_id)`. Jinja escapes names and message bodies; no HTML from Gemini is trusted.

**Build order**
1. [ ] Add account fixtures/tests first, including two users and a missing-CSRF case.
2. [ ] Implement auth helpers/settings and wire session middleware and exception handlers.
3. [ ] Implement registration, login and logout; only then add the protected thread read.
4. [ ] Run auth tests; give P1-02 the passing app and stable auth contracts.

**Tests**
- `test_register_seeds_no_user_data` — valid registration returns 303 to `/login`, writes one user with normalized email and a non-plaintext hash, and writes no message or transaction.
- `test_duplicate_email_conflict` — registering `Demo@Example.test` then `demo@example.test` returns 409 for the second request and leaves exactly one account.
- `test_login_generic_failure` — nonexistent account and incorrect password both return 401 and the same credential error.
- `test_login_logout_session` — successful login redirects to `/chat`, rotates CSRF, sets `HttpOnly`/`SameSite=Lax` and configured `Secure`; logout clears access and the next `/chat` redirects to `/login`.
- `test_missing_csrf_does_not_register` — valid registration fields without token return 403 and write zero users.
- `test_thread_is_private_and_escaped` — user B sees none of user A’s messages; a body `<script>alert(1)</script>` appears escaped in A’s page; response is `no-store`.

**Validation and handoff:** `.\.venv\Scripts\python.exe -m pytest -q tests/test_p0.py tests/test_p1_auth.py` passes. Deliver the auth and thread checkpoint, test DB users, and route list. Reviewer checks session rotation, POST CSRF, escaping, and ownership. Roll back app files as one checkpoint; keep accounts and messages. Local HTTP is a demo configuration, not production security approval.

### P1-02 — Gemini chat, transaction cards, confirm, undo

**Objective and boundary:** Implement only `record_expense` and `record_income`. No photo ingress, no deferred tools, no model-supplied SQL or user IDs. Single writer after P1-01 because this task modifies the same thread and router.

| Create or modify | Purpose / owned symbols |
|---|---|
| `app/shared/ai.py` | `generate_chat`, `ChatReply`, `AIUnavailable`, `AIResponseError`, shared model pin. |
| `app/chat/tools.py` | `ToolCall`, fixed declarations, argument validation, input-evidence check, one-retry coordination. |
| `app/chat/templates/chat/transaction_card.html` | Pending, saved, undone and expired ledger cards. |
| `app/money/__init__.py`, `app/money/service.py` | Package marker and ledger SQL; `insert_transaction`, `undo_transaction`, category resolution. No money router. |
| Modify `app/chat/routes.py`, `app/chat/templates/chat/thread.html` | Composer, send, confirm, undo and card hydration. |
| Modify `app/shared/config.py`, `.env.example`, `requirements.txt`, `README.md`, `tests/conftest.py` | Gemini key/config, `google-genai` and Windows `tzdata`, fake client, live P0.5/P1 instructions. |
| `tests/test_p1_chat.py` | Tool, evidence, persistence, confirmation, undo and isolation tests. |

**Shared AI contract**

`generate_chat(settings: Settings, *, system_instruction: str, contents: Sequence[google.genai.types.Content], declarations: Sequence[google.genai.types.FunctionDeclaration]) -> ChatReply`

`ChatReply` exposes `content: google.genai.types.Content`, `text: str | None`, `calls: tuple[ToolCall, ...]`; `ToolCall` has `name: str` and `args: dict[str, object]`. Keep the SDK candidate content intact for the retry transcript. Pin model ID and disable automatic function execution. No HTTP retries that re-run app work. `AIUnavailable` covers missing/rejected credentials, quota, timeout or transport/service failure. `AIResponseError` covers unparseable responses or no usable candidate. Parsed unknown/multiple calls go through tool validation, not automatic execution. Missing `GEMINI_API_KEY` never stops P0 or account/thread reads. Revoke the exposed proof key before any live run.

**Gemini declarations**

Each row defines an object schema: exact property names below, all listed fields required except `memo` and `query_money.category_code`; reject extra fields server-side. Use JSON `integer`, `string`, or `null` as specified; descriptions carry semantic bounds, and the server enforces them even if the SDK/model does not. Integers reject booleans, floats and numeric strings. String lengths refer to trimmed values. Strict dates are actual calendar dates written `YYYY-MM-DD`.

| Name | Properties and validation | Exposed |
|---|---|---|
| `record_expense` | `amount`: integer `1..4294967295`; `date`: date string `≤ today`; `source`: string `1..120`; `category_code`: one of `food,transport,daily,social,utility,other`, must exist as `expense`; `memo`: omitted/null or string `0..255`, blank → null. | P1–P2 |
| `record_income` | Same names/types/bounds; `category_code`: `salary,support,other_income`, must exist as `income`. | P1–P2 |
| `create_bill` | `title`: string `1..120`; `amount`: integer `1..4294967295`; `due_day`: integer `1..31`; `start`: date string; D6 recommends allowing future starts. | P3 only, contract to approve |
| `create_installment` | `title`: string `1..120`; `total_amount`: integer `1..4294967295`; `months`: integer `1..24`; `due_day`: integer `1..31`; `start`: date string, same future-date decision. | P3 only, contract to approve |
| `mark_paid` | `commitment_id`: integer `1..4294967295`; must identify an owned active commitment. | P3 only, contract to approve |
| `query_money` | `from`, `to`: inclusive date strings `from ≤ to ≤ today`; `kind`: `expense` or `income`; `category_code`: omitted/null or seeded code of that kind. | P4 only, contract to approve |
| `save_fact` | `topic`: string `1..40`; `value`: string `1..255`; reject blank/control characters; topic unique within user. Eligible topics still need P4 approval. | P4 only, contract to approve |
| `read_facts` | Empty object; no parameters. | P4 only |

Do not register stubs for deferred tools. `source`, category and memo may be proposed from context; the server does not treat a seeded `other` category as permission to default an unclear entry.

**Input-evidence and write rules**

1. Load existing owned facts and the last 20 stored messages before appending the incoming text to the prompt. Fetch newest first, reverse in Python. History/facts may inform interpretation, but never count as amount/date evidence.
2. Use the current user message only for evidence. Normalize full-width characters for matching, not storage. Accept one unambiguous positive whole-yen amount: digits with optional valid thousands separators and `¥`/`￥`, `円`, or `JPY`; a lone bare integer also counts after removing recognized date spans. More than one candidate, ambiguous units/decimal/sign, or no match → ask, with no pending card. Never choose among conflicting candidates based on model preference. If the proposed amount does not match evidence, use the one invalid-argument retry.
3. An explicit `YYYY-MM-DD` or `YYYY/MM/DD`, or `今日`/`today`, is eligible for immediate save only when exactly one unambiguous date is present and it matches the proposal. Multiple conflicting date cues, invalid calendar dates, or future transaction dates cannot be saved. An omitted date resolves to today **for confirmation only**. Recognize JP/EN previous-week expressions including `先週の金曜`/`last Friday`; use the previous Monday–Sunday week, selecting the named weekday. Bare `先週`/`last week` has no day: ask instead of choosing. Ask for dates outside the supported grammar rather than accepting a model guess. Compare the proposed date with the server-resolved date; retry on mismatch.
4. On a malformed/unknown/multiple/mismatched call, re-send the original context plus the preserved candidate and one validation error; never execute the rejected call. On a second invalid call or a no-call answer, write no financial row and render one short question or plain reply. Provider failure writes no financial row and persists a plain retry-later message. Only the server generates saved/undo claims.
5. After Gemini returns, use one DB transaction for the user message and assistant message and, if eligible, one ledger insert. No DB transaction stays open during a provider call. Pending writes use `{"type":"pending_transaction","kind":"expense|income","amount":1,"date":"YYYY-MM-DD","source":"…","category_code":"…","memo":null}` in the assistant row; its real amount and kind replace the illustrative values. Saved payload is `{"type":"saved_transaction","txn_id":123}`; plain replies use SQL `NULL`. Confirm locks and revalidates the owned pending row and only then inserts with `source_kind='chat'`; repeated confirmation of a saved card redirects without inserting. Undo soft-deletes; it does not change the message payload.
6. Do not promise exactly-once behavior for two independent sends of the same typed text. Disable repeat submit while a request is pending; after an uncertain result, reload the thread, never automatically POST again.

**HTTP contracts**

Form POSTs use `application/x-www-form-urlencoded` and `csrf_token`. `message_id` and `txn_id` are positive unsigned-INT path values. Malformed requests return `422 error.html`; unauthenticated/CSRF/DB handling is as in P1-01. Valid write results redirect `303 /chat`.

| Method/path | Fields | Result/template | SQL |
|---|---|---|---|
| `GET /chat` | None | `200 chat/thread.html`; `chat/transaction_card.html` for pending and saved payloads. A saved card shows undo iff the linked row is live and younger than 24 hours. | C1 |
| `POST /chat/messages` | `text`, trimmed 1–2,000 characters; `csrf_token` | Redirect after recorded reply, clarification, pending card or saved card; result rendered on `chat/thread.html`. | C2, C3, C4, T1 when eligible |
| `POST /chat/messages/{message_id}/confirm` | `csrf_token` | Redirect after saving or if already saved; `404 error.html` for missing/foreign, `409 error.html` if owned message is not confirmable. | C5, C3, T1, C6 |
| `POST /chat/transactions/{txn_id}/undo` | `csrf_token` | Redirect after undo or if already undone; `404 error.html` for missing/foreign, `409 error.html` if live but expired. | T2, T3 |

**SQL in route order** — named connector placeholders below are bind parameters, not string interpolation. Use `lastrowid` from the successful ledger insert.

C1 — thread and owned saved-card hydration. Uses `idx_chat_user` and joined `transactions.PRIMARY`; a deleted row remains joinable to render “undone.”

```sql
SELECT m.message_id, m.role, m.body, m.payload, m.created_at,
       t.txn_id, t.kind, t.amount, t.txn_date, t.source, t.category_id,
       t.deleted_at, t.created_at > UTC_TIMESTAMP() - INTERVAL 24 HOUR AS can_undo,
       c.category_name
FROM chat_message AS m
LEFT JOIN transactions AS t
  ON t.txn_id = CAST(JSON_UNQUOTE(JSON_EXTRACT(m.payload, '$.txn_id')) AS UNSIGNED)
 AND t.user_id = m.user_id
LEFT JOIN categories AS c ON c.category_id = t.category_id
WHERE m.user_id = %(user_id)s
ORDER BY m.message_id;
```

C2 — model context. Uses `uq_fact(user_id,topic)` and reverse `idx_chat_user`.

```sql
SELECT topic, value FROM memory_fact WHERE user_id = %(user_id)s ORDER BY topic;

SELECT role, body FROM chat_message
WHERE user_id = %(user_id)s
ORDER BY message_id DESC
LIMIT 20;
```

C3 — category validation, `uq_category`. C4 — append chat messages, `PRIMARY` and `idx_chat_user` maintained; use twice within one transaction, once per role.

```sql
SELECT category_id, category_name FROM categories
WHERE kind = %(kind)s AND code = %(category_code)s;

INSERT INTO chat_message (user_id, role, body, payload)
VALUES (%(user_id)s, %(role)s, %(body)s, %(payload_json)s);
```

C5/C6 — confirmation lock and payload update, `chat_message.PRIMARY`, ownership predicate on both statements.

```sql
SELECT role, payload FROM chat_message
WHERE message_id = %(message_id)s AND user_id = %(user_id)s
FOR UPDATE;

UPDATE chat_message SET payload = %(payload_json)s
WHERE message_id = %(message_id)s AND user_id = %(user_id)s;
```

T1 — shared ledger insert. P1 binds `receipt_id=NULL`, `source_kind='chat'`; P2 binds the locked receipt ID and `source_kind='photo'`. Maintains PK, unique receipt key, and user date/category indexes. Commitments are not written here.

```sql
INSERT INTO transactions
  (user_id, kind, amount, txn_date, category_id, source, memo, receipt_id, source_kind)
VALUES
  (%(user_id)s, %(kind)s, %(amount)s, %(date)s, %(category_id)s, %(source)s,
   %(memo)s, %(receipt_id)s, %(source_kind)s);
```

T2/T3 — check and lock by `transactions.PRIMARY`; timestamp cutoff is exclusive. A live row at exactly 24 hours is expired. Re-check in update so crossing the cutoff between statements cannot undo the row.

```sql
SELECT deleted_at, created_at > UTC_TIMESTAMP() - INTERVAL 24 HOUR AS can_undo
FROM transactions
WHERE txn_id = %(txn_id)s AND user_id = %(user_id)s
FOR UPDATE;

UPDATE transactions SET deleted_at = UTC_TIMESTAMP()
WHERE txn_id = %(txn_id)s AND user_id = %(user_id)s
  AND deleted_at IS NULL
  AND created_at > UTC_TIMESTAMP() - INTERVAL 24 HOUR;
```

**Build order**
1. [ ] Freeze D1, write fake-Gemini/DB tests, and record the live P0.5 chat cases before running the live model.
2. [ ] Build model adapter and declarations, then validate tool arguments and evidence independently of route writes.
3. [ ] Implement append/direct save in one transaction, then payload rendering. Implement locked confirm using that payload contract, then undo.
4. [ ] Validate the test suite, run the ten live chat cases on the configured model, and repeat the ten filing cases through the phone UI. Record tool arguments and DB result without recording secrets.

**Tests**
- `test_only_p1_transaction_tools_exposed` — fake SDK receives exactly the declarations `record_expense`, `record_income`, and model ID `gemini-3.1-flash-lite`.
- `test_explicit_expense_and_income_save` — with Tokyo date `2026-11-24`, `今日 ランチ 850円` and `2026-11-23 salary ¥220000` create one owned food expense for 850 on Nov 24 and one salary income for 220000 on Nov 23, both `source_kind='chat'`.
- `test_inferred_date_survives_refresh_and_confirms_once` — under the same clock `先週の金曜 ランチ 1200円` shows `2026-11-20` after refresh, initially writes zero ledger rows, then two concurrent confirm POSTs produce exactly one ledger row.
- `test_omitted_date_never_auto_saves` — `ランチ 850円` renders a pending card dated `2026-11-24` and writes zero ledger rows.
- `test_invalid_tool_retries_once` — a boolean amount followed by an income category on an expense causes exactly two model calls, one plain clarification and zero ledger rows.
- `test_retry_cannot_bypass_input_evidence` — incoming `今日 ランチ 850円` with proposed amount 8500 on both attempts results in zero ledger rows; multiple text amounts or no amount also result in no pending financial card.
- `test_future_or_unresolved_date_not_filed` — under the same clock `2026-11-25 ランチ 850円` and `先週 ランチ 850円` yield no ledger rows and no confirmable card.
- `test_prompt_context_is_owned_and_bounded` — after 25 owned stored messages and one foreign message, prompt has the newest 20 owned bodies in ascending ID order, only owned facts, and the current input once.
- `test_ai_outage_writes_no_ledger` — provider timeout persists the user message plus retry-later reply and zero ledger rows.
- `test_confirm_and_undo_are_owner_scoped` — user B’s requests for A’s pending message and saved transaction return 404 without changing either row.
- `test_undo_window_and_idempotency` — a row at 23 hours 59 minutes is soft-deleted and repeated undo preserves that timestamp; a live row aged 24 hours or more returns 409 and remains live.

**Validation and handoff:** `.\.venv\Scripts\python.exe -m pytest -q tests/test_p0.py tests/test_p1_auth.py tests/test_p1_chat.py` passes. For the live proof, pre-label ten unambiguous cases covering today/explicit dates, expense/income, JP/EN/mixed text and one previous-week date; require 10/10 correct tool, arguments, and final rows after any required confirm. Verify one undo in MySQL by checking the same `txn_id` remains and `deleted_at` becomes non-null. Deliver case/expected/actual results, not just screenshots. Reviewer checks the two paths to a ledger insert and verifies no provider call happens inside a DB transaction. Roll back application code as a checkpoint, retaining messages and ledger rows. Residual risks: limited date grammar and legitimate repeated text; do not loosen proof rules to compensate.

### P2-01 — Upload, read, queue, swipe and recovery

**Objective and boundary:** Add receipt intake to the existing chat and reuse its ledger and undo path. No new table, public uploads directory, receipt auto-post, line-item splitting, or background job. One writer owns the P2 integration; it extends P1 routes/templates.

| Create or modify | Purpose / owned symbols |
|---|---|
| `app/receipts/__init__.py` | Package marker. |
| `app/receipts/routes.py` | `router`, upload, private image, save/correct, discard and re-read. |
| `app/receipts/service.py` | Receipt SQL, extraction-state transitions, queue query. |
| `app/receipts/templates/receipts/queue.html` | Stack, non-ready notices, re-read and upload forms. |
| `app/receipts/templates/receipts/card.html` | Photo, fields, index, correction panel, gesture-equivalent buttons. |
| `app/receipts/static/swipe.js` | Pointer events and dispatch to the same controls as buttons. |
| `app/shared/uploads.py` | `save_upload`, `StoredUpload` and upload exception types. |
| Modify `app/shared/ai.py`, `app/shared/config.py`, `app/main.py` | `extract_receipt`, upload settings, receipt router and scoped asset mount. |
| Modify `app/chat/routes.py`, `app/chat/templates/chat/thread.html` | Place the receipt uploader/queue in the same thread; keep existing message and ledger-card behavior. |
| Modify `.env.example`, `requirements.txt`, `README.md`, `tests/conftest.py` | Private upload directory, Pillow, fixture images/fake extraction, phone and failure instructions. |
| `tests/test_p2_receipts.py` | Upload, extraction, queue, ownership, state and replay checks. |

`uploads/` is created locally at runtime or setup, never committed or mounted. `GET`/`HEAD /assets/receipts/{path:path}` serves only `app/receipts/static/` or returns 404; no DB or Jinja2.

**Shared upload and extraction contracts**

- `save_upload(upload: UploadFile, *, upload_dir: Path, max_bytes: int, max_pixels: int) -> StoredUpload`. `StoredUpload` exposes `image_path: str` (generated basename only), `path: Path` (absolute), `mime_type: str`, `size_bytes: int`. Read `upload.file` with a size limit; ignore client filename and reported MIME for storage decisions. Verify/decode a single JPEG, PNG or WebP image and check dimensions before full decode. Store original bytes under an exclusive, generated UUID filename with trusted extension. Raise `UploadTooLarge` for byte/pixel limits (413), `UnsupportedImage` for invalid or unsupported image (415), or `UploadStorageError` for filesystem failure (503). Remove partial files. After a known DB insert rollback remove the saved file; after an uncertain commit do not delete a possibly referenced file. Document manual reconciliation; do not auto-rerun upload. Enforce the byte limit while reading the uploaded file, and note that public deployment still needs an ingress request-size limit.
- `extract_receipt(settings: Settings, *, image_path: Path, mime_type: str) -> ReceiptExtraction`. `ReceiptExtraction` has `is_receipt: bool`, `expense_date: date | None`, `shop_name: str | None`, `amount: int | None`, `category_code: str | None`. Raise `AIUnavailable`/`AIResponseError` as defined in P1; raise `UploadStorageError` if the stored file is missing or unreadable. Use pinned Gemini, `temperature=0`, `application/json`, a structured schema, and **no callable financial tools**. All five keys required in the response; use nullable ISO date string, shop string, whole-yen integer, and seeded expense category respectively. `is_receipt` is a non-null boolean. Keep P0.5’s total/era/collage rules. The evidence harness forced an expense category; allow `null` here so an unclear category is not guessed. Structurally malformed output → failed read. Treat unusable fields in an otherwise structurally valid receipt (e.g., future date or zero amount) as missing; retain valid fields. `is_receipt=false` → failed read, no card.

**Receipt state and browser behavior**

- Upload saves the file and commits a receipt in `processing`. Store `extracted={"read_id":"<uuid>","started_at":"<UTC timestamp>"}` for that attempt. Call Gemini without a DB transaction open. Finalize only if the row still belongs to the attempt: set `done` with `{"read_id":"<uuid>","is_receipt":true,"expense_date":null,"shop_name":null,"amount":null,"category_code":null}` using actual valid values, or set `failed` with `extracted=NULL`. Threshold for starting another attempt is 60 seconds; a late response from an earlier attempt cannot overwrite a newer attempt. A provider or file-read failure leaves the image row available for re-read.
- Queue predicate is owned `done` receipts with **no linked transaction, even a soft-deleted one**. Order by `(uploaded_at, receipt_id)` ascending and label cards `1/N` through `N/N` in that order. Queue remains in the same page as chat and does not block uploading another photo. Show failed/discarded/stale reads with a re-read form; fresh processing rows have no retry button.
- For an incomplete card, ask for the first missing value in this order: amount, category, date, shop. Prevent direct acceptance until all are valid. Left swipe or `← 修正` reveals editable fields prefilled from extraction; right swipe or `保存 →` invokes direct acceptance; `✕ 捨てる` submits discard. Buttons work without swipe; correction must be reachable with a keyboard and no JS. For the pointer path, recognize release with `|dx| ≥ 60 CSS px` and `|dx| > |dy|`; ignore canceled/vertical drags and pointer events originating on interactive controls. Dispatch to the same form/control as the button. Never synthesize save from left swipe or discard.
- Save/correct locks the owned receipt, matches the current `read_id`, checks for an existing link, validates category, then inserts exactly one expense and appends a saved assistant card in the same DB transaction. Use `source_kind='photo'` for corrected as well as unedited reads; final `source` is shop, `memo=NULL`. A replay for the same linked read returns the existing result without writing. Old-read requests return 409. Undo uses P1’s route, leaving the receipt linked and off the queue.
- Discard locks the receipt and sets `pending,NULL` only if it still matches the current read and is unlinked. No ledger or chat write. Re-read is permitted for unlinked `pending`, `failed`, or stale `processing`; reject a fresh in-flight read, a queued `done` read, or any linked receipt with 409. Discard, re-read and save must share the same receipt-lock boundary.

**HTTP contracts**

Private auth and CSRF rules are unchanged. Except upload, POSTs use form encoding. `receipt_id` is a positive unsigned-INT path parameter. `read_id` is the UUID issued by the current read. Missing or malformed fields give `422 error.html`; foreign or nonexistent IDs give `404 error.html`; stale or illegal states give `409 error.html`.

| Method/path | Fields | Result/template | SQL |
|---|---|---|---|
| `GET /chat` | None | Existing `200 chat/thread.html` with `receipts/queue.html` and `receipts/card.html`; source is receipt queue and retained-read notices, not chat payload. | C1, R1, R2, R3 |
| `POST /receipts` | Multipart `photo` (one file) and `csrf_token` | 303 to `/chat` with a card or a failed-read notice; 413/415/503 `error.html` for upload helper failures before DB insert. Camera form uses `accept="image/*"` and `capture="environment"`. | R4, R5 |
| `GET /receipts/{receipt_id}/image` | None | `200` owned image bytes, correct MIME, `Cache-Control: private, no-store`, `X-Content-Type-Options: nosniff`; `404` if row/file missing. No Jinja2 for image bytes. | R6 |
| `POST /receipts/{receipt_id}/save` | `csrf_token`, `read_id`, `mode=accept` or `correct`. Accept forbids override fields. Correct requires `date`, `shop`, `amount`, `category_code`. Date is strict ISO and not future; shop trimmed `1..120`; amount ASCII digits, integer `1..4294967295`; category a seeded expense code. | Redirect on commit or same-read replay. Invalid or incomplete candidate gives 422; never writes. Correction form/card rendered by `receipts/card.html` inside chat. | R7, R8, C3, T1, C4 |
| `POST /receipts/{receipt_id}/discard` | `csrf_token`, `read_id` | 303 to `/chat`; card removed, image retained and re-read offered. Replayed discard on non-`done` state is 409. | R7, R8, R9 |
| `POST /receipts/{receipt_id}/reread` | `csrf_token` | 303 to `/chat` with new card or failed-read notice. | R7, R8, R10, R5 |

**Receipt SQL**

R1–R3 — queue, retained-read notices, and category controls. `idx_receipt_user_time` supports the owner/time scan; the receipt join uses the unique `transactions.receipt_id` index. `categories.uq_category` serves the `kind` range; sorting the small seeded list is expected. Use the R2 processing timestamp to distinguish stale from fresh rows in the server view model.

```sql
SELECT r.receipt_id, r.uploaded_at, r.extracted
FROM receipts AS r
LEFT JOIN transactions AS t
  ON t.receipt_id = r.receipt_id AND t.user_id = r.user_id
WHERE r.user_id = %(user_id)s AND r.read_status = 'done' AND t.txn_id IS NULL
ORDER BY r.uploaded_at, r.receipt_id;

SELECT r.receipt_id, r.read_status, r.extracted
FROM receipts AS r
LEFT JOIN transactions AS t
  ON t.receipt_id = r.receipt_id AND t.user_id = r.user_id
WHERE r.user_id = %(user_id)s
  AND r.read_status IN ('pending','processing','failed') AND t.txn_id IS NULL
ORDER BY r.uploaded_at, r.receipt_id;

SELECT code, category_name FROM categories
WHERE kind = 'expense'
ORDER BY sort_order, category_id;
```

R4 persists the private image and starts an attempt; `PRIMARY` and `idx_receipt_user_time` maintained. R5 finalizes only the current attempt using `receipts.PRIMARY`; zero rows changed means an obsolete result, not grounds to retry.

```sql
INSERT INTO receipts (user_id, image_path, read_status, extracted)
VALUES (%(user_id)s, %(image_path)s, 'processing', %(attempt_json)s);

UPDATE receipts SET read_status = %(result_status)s, extracted = %(result_json)s
WHERE receipt_id = %(receipt_id)s AND user_id = %(user_id)s
  AND read_status = 'processing'
  AND JSON_UNQUOTE(JSON_EXTRACT(extracted, '$.read_id')) = %(read_id)s;
```

R6 reads privately; R7 locks by receipt PK; R8 uses the unique transaction receipt key, including deleted rows. Do not hold R7’s lock during Gemini. No transaction is inserted without first taking R7 and checking R8.

```sql
SELECT image_path FROM receipts
WHERE receipt_id = %(receipt_id)s AND user_id = %(user_id)s;

SELECT image_path, read_status, extracted
FROM receipts
WHERE receipt_id = %(receipt_id)s AND user_id = %(user_id)s
FOR UPDATE;

SELECT txn_id, deleted_at FROM transactions
WHERE receipt_id = %(receipt_id)s AND user_id = %(user_id)s;
```

R9/R10 update on `receipts.PRIMARY`, after validating state and ownership under R7. Keep the DB path unchanged.

```sql
UPDATE receipts SET read_status = 'pending', extracted = NULL
WHERE receipt_id = %(receipt_id)s AND user_id = %(user_id)s;

UPDATE receipts SET read_status = 'processing', extracted = %(attempt_json)s
WHERE receipt_id = %(receipt_id)s AND user_id = %(user_id)s;
```

**Build order**
1. [ ] Freeze D3–D5. Add file, fake-provider and concurrent-request tests first; use temporary private upload storage.
2. [ ] Build upload saver and Gemini extraction wrapper; verify invalid file handling independently.
3. [ ] Build receipt insert/finalize, private image serving and queue rendering. Prove upload and re-read cannot post money.
4. [ ] Add locked save/correct, then discard/re-read and stale attempt recovery. Add plain controls before gestures.
5. [ ] Add gesture mapping, run automated tests, then run owner-receipt validation and the real-phone P2 gate. Capture a misread corrected through `← 修正`.

**Tests**
- `test_bad_upload_does_not_create_receipt` — oversized bytes/dimensions get 413, forged or unsupported image bytes get 415, and neither case adds a receipt, retained file, or transaction.
- `test_upload_creates_private_pending_card_only` — one valid photo with a valid fake extraction gives 303, one owned `done` receipt, one queue card after refresh and zero transactions or callable Gemini money tools.
- `test_missing_extract_fields_require_correction` — `amount=null` renders the amount question; direct accept returns 422 and writes nothing; valid correction writes the supplied whole-yen amount.
- `test_five_cards_stable_order` — five `done` receipts with equal upload timestamps render in ascending receipt ID order with labels `1/5` through `5/5`.
- `test_receipt_accept_replay_and_undo` — two concurrent accepts for the same read result in one `photo` transaction and one saved message; undo sets `deleted_at` and does not requeue the receipt.
- `test_receipt_correct_uses_reviewed_fields` — overwrite misread `7540` to `540` and submit correction; ledger stores `540` and the submitted date, shop, and category.
- `test_discard_keeps_image_and_reread_needs_review` — discard preserves image bytes, sets `pending,NULL`, and removes card; re-read yields a new read ID, stale save returns 409, and ledger stays empty until explicit accept.
- `test_save_and_discard_race_has_one_winner` — racing save and discard for the same read yields either one linked transaction and 409 on discard, or `pending,NULL` and 409 on save; never both effects.
- `test_processing_recovery_rejects_late_result` — fresh attempt cannot re-read; attempt older than 60 seconds can; late finalization for the old ID affects zero rows.
- `test_provider_failure_retains_retryable_image` — timeout leaves one `failed` receipt and its bytes, no queue card, and no ledger row.
- `test_receipt_routes_are_owner_scoped` — B cannot fetch, save, discard or re-read A’s receipt; each request gets 404, no state change, and no image bytes.
- `phone_swipe_and_buttons_match` — right swipe and `保存 →` each save exactly one receipt; left swipe and `← 修正` each reveal prefilled fields and save nothing until submitted; discard never saves; vertical scroll/canceled drag does not submit.
- `phone_five_receipt_gate` — photograph five on the real phone without being forced to clear earlier cards; all five save with distinct receipt links and the measured interval is under 30 seconds. Demonstrate one deliberate misread correction separately.

**Validation and handoff:** `.\.venv\Scripts\python.exe -m pytest -q tests/test_p0.py tests/test_p1_auth.py tests/test_p1_chat.py tests/test_p2_receipts.py` passes. Record phone/browser, timing, five distinct links, correction result, owner receipt proof and unexpected failures. Reviewer verifies filesystem isolation, owner checks, ledger write locking, and exclusion of soft-deleted links from the queue. Roll back the P2 application checkpoint without deleting images, receipt rows, chat history, or posted transactions. Residual risks: camera-specific format behavior, large-image latency, and orphan files after indeterminate upload commit; do not add an unapproved background cleanup process.

## Ownership and dependencies

| Barrier | Integration order and parallel work | Parent acceptance decision |
|---|---|---|
| Before P0 | P0-01 owns the application checkout. Read-only preparation of school/demo evidence does not overlap implementation. | Accept D2 configuration/HTTP defaults; confirm MySQL 8.4 availability or record an installation blocker. |
| P0 → P1 | Integrate only after README boot, schema/seed and health pass. Then P1-01 owns its files. Live-case labeling can proceed in parallel without editing app files. | Accept the real-MySQL P0 gate and auth assumptions before exposing private routes. |
| P1-01 → P1-02 | Review session/CSRF and isolation. Integrate P1-01 before the AI writer modifies the same router and template. | Accept D1 and the test corpus; allow live calls only with a rotated key. |
| P1 → P2 | Integrate only after fake-provider tests and the phone/DB P1 gate. Owner-receipt labeling and browser preparation may proceed read-only alongside code work. | Accept D3–D5 before P2 work, including the measurement and fallback policy. |
| P2 acceptance | Run automated regression, independent safety/state review, then live owner-receipt and phone checks. | Accept only with measured evidence. If a live gate fails, identify the failing assumption before changing limits, model, or behavior. |

No parallel application writers: later tasks modify earlier wiring. Reviewer and tester consume immutable checkpoints and report findings to the parent. Complexity: **P0 small/medium** (minimum medium reasoning), **P1-01 medium** (minimum medium), **P1-02 and P2-01 high** (minimum high for evidence validation, state transitions and races). Parent makes final model and reasoning selections.

## Validation and rollback

Run the setup from repo root in PowerShell. If `mysql` is not on PATH after install, open a fresh terminal or use the installed `mysql.exe` path recorded in README. Provision a dedicated non-root runtime account with only required SELECT/INSERT/UPDATE access to the demo schema. Apply schema and seed with a provisioning account. Use separate test credentials and a database ending in `_test`; only that account/harness may perform test cleanup.

```powershell
winget install --id Oracle.MySQL --exact
mysql --version
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
mysql -u root -p --execute="CREATE DATABASE snaptrack CHARACTER SET utf8mb4; CREATE DATABASE snaptrack_test CHARACTER SET utf8mb4;"
mysql -u root -p -D snaptrack --execute="SOURCE db/schema.sql"
mysql -u root -p -D snaptrack --execute="SOURCE db/seed.sql"
mysql -u root -p -D snaptrack_test --execute="SOURCE db/schema.sql"
mysql -u root -p -D snaptrack_test --execute="SOURCE db/seed.sql"
mysql -u root -p -D snaptrack --execute="SELECT COUNT(*) AS categories FROM categories"
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory
```

Configure `.env` and the test environment before starting the app or tests. In a second fresh terminal run `curl.exe -i http://127.0.0.1:8000/health`; expect HTTP 200 and `{"status":"ok"}`. Expect MySQL `8.4.x` and category count `9`. Use `.\.venv\Scripts\python.exe -m pytest -q` as the final regression command; all implemented-phase tests must pass. Review the SQL index paths on MySQL; no test should require the optimizer to choose an index on a nine-row or otherwise tiny fixture. For a phone on a trusted LAN, explicitly start Uvicorn with `--host 0.0.0.0`, configure local HTTP cookies per D2, use the laptop’s LAN address, and stop the listener after the test.

Checkpoint each accepted task. Roll back app code before considering any data change. P1 and P2 need no DDL or backfill. If code is rolled back, retain all durable messages, transactions and receipts; newer UI content may temporarily be unavailable. Check ambiguous commits by reloading or reconciling DB/file state. Never use re-seed, schema reset, retry, or receipt re-read to reconstruct a ledger write.

## Risks, assumptions, and gaps

- The plan treats D1–D5 defaults as proposed execution contracts, not base-plan facts. Confirm them at the listed gates.
- The bounded parser intentionally asks rather than guessing on unsupported date or amount phrasing. Improperly expanding it can undermine the core safety rule.
- The model pin reflects existing proof, not a promise of perfect receipt OCR or quota availability. Live phone and owner-receipt evidence remain necessary.
- The exact school dates and paperwork are outside this implementation. ER diagram and requirements-document reconciliation remain required by the base plan, but are not additional files for this P0–P2 implementation handoff.