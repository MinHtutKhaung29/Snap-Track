# Snap & Track — Base Plan (v3)

Written 2026-11-24. v3 answers an independent review of v2 (25 findings, verdict *fail*). Every schema and safety change below is a fix for a specific defect, listed in §13 so nothing changes silently.

Target: working demo by **2026-12-17**, finished and rehearsed before **2027-02-01**.

---

## 0. What changed across versions

| v1 | v2 | v3 (this) |
|---|---|---|
| Photo → expense | Chat first, 4 money kinds, one thread | same product, schema and safety fixed |
| 4 entities | 7 entities | 7 entities that actually support the flows |
| — | — | deterministic confirm gate, security section, delivery section |

---

## 1. What the app is

You talk to it like a person. 「今日 ランチ 850円」 → it files 850 under 食費, dated today, and shows a card you can undo. 「来月から 冷蔵庫 6回払い 総額72000円 27日払い」 → it builds a six-payment plan and tells you which day each lands. 「先月 何に一番使った?」 → it reads your rows and answers, because the numbers are computed in SQL, not remembered.

**Core promise:** zero typing, and it never has to be taught twice. One thread that never resets.

### Definition of done

A stranger opens the app on a phone, types 「今日 ランチ 1200円」 and sees it filed immediately under 食費 with the right date, types 「先週の金曜 ランチ 1200円」 and sees a **confirm card with the resolved date** (correct behaviour — see §2), undoes one entry, photographs three receipts and clears all three cards in under 30 seconds, then asks 「今月いくら使った?」 — all unaided, under two minutes.

---

## 2. The AI rule, made enforceable

**The AI never guesses money.** v2 stated this as a policy and leaned on the model behaving. v3 makes it a server-side check, because a policy the server cannot test is not a policy.

| Input | Server check before any write |
|---|---|
| Chat, amount and a date token present in the text | the digits must appear literally in the normalised user message, and a date token must match (`今日`, `昨日`, `YYYY-MM-DD`, `M月D日`, `M/D`) → **auto-commit** + undo card |
| Chat, amount present but no date token, or a relative date (`先週`, `来月`) | **confirm card** with the resolved date |
| Chat, amount absent | ask a short question. Never default |
| Photo | **swipe card**, always. The chat model never receives images |

Mechanics: the message is NFKC-normalised and its digits extracted; the proposed amount must be present in that digit string, otherwise the tool call is rejected and re-asked once. This is a string check, not a model self-report — that is the whole point.

Three nets on top: every save is undoable for 24 h (`deleted_at`), every row records `source_kind`, and the confirm endpoint locks the pending row (`SELECT … FOR UPDATE`) so a double-tap cannot write twice.

---

## 2b. The swipe card and its queue

```
        ┌───────────────────────────┐
        │  [receipt photo]     2/5  │
        │  支出（レシート）           │
        │  ¥1,000                   │
        │  2026-11-20  セブン-イレブン │
        │  食費  ▾                   │
        └───────────────────────────┘
          ✕ 捨てる    ← 修正    保存 →
```

| Gesture | Button | Effect |
|---|---|---|
| Swipe right | 保存 → | one `transactions` row; card flips; 元に戻す 24 h |
| Swipe left | ← 修正 | fields open pre-filled; category is a one-tap chip row, not a form |
| ✕ | ✕ 捨てる | sets `receipts.discarded_at` — the card leaves the queue for good |

**Queue query** (a pending card is a receipt with no *live* transaction):

```sql
SELECT r.* FROM receipts r
WHERE r.user_id = %s AND r.read_status = 'done' AND r.discarded_at IS NULL
  AND NOT EXISTS (SELECT 1 FROM transactions t
                  WHERE t.receipt_id = r.receipt_id AND t.deleted_at IS NULL)
ORDER BY r.uploaded_at
```

Buttons sit under every card and share one handler with the gestures — a gesture nobody knows is a dead end, and a drag is unusable for some people.

---

## 3. Scope

**Must work:** login · one chat thread that files typed sentences · expense and income with category · 24 h undo · receipt photo → swipe card · bills and installments with a due list and mark-paid · questions answered from own rows · strict per-user isolation.

**Should work:** edit/delete an entry · month and category filters · running total · standing facts (salary day, rent day) · category change as one tap on the card.

**Not building:** many chat sessions · conversation list · bank or card sync · background auto-posting of bills · line-item splitting inside one receipt · multi-currency · budget goals · push notifications · native store release · comments/posts/admin (WBS leftovers).

---

## 4. Data model (ER v4, 8 tables)

Tables are declared in dependency order — `commitments` before `transactions`, because `transactions` references it. Getting this wrong is MySQL error 1824.

```sql
CREATE TABLE users (
  user_id       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(80)  NOT NULL,
  email         VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
  category_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  code          VARCHAR(32)  NOT NULL,
  category_name VARCHAR(40)  NOT NULL,
  kind          ENUM('expense','income') NOT NULL,
  sort_order    SMALLINT     NOT NULL DEFAULT 0,
  UNIQUE KEY uq_cat_code_kind (kind, code),
  UNIQUE KEY uq_cat_id_kind   (category_id, kind)
);

CREATE TABLE receipts (
  receipt_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id      INT UNSIGNED NOT NULL,
  image_path   VARCHAR(255) NOT NULL,
  uploaded_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  read_status  ENUM('pending','processing','done','failed') NOT NULL DEFAULT 'pending',
  discarded_at DATETIME     NULL,
  extracted    JSON         NULL,
  CONSTRAINT fk_rcpt_user FOREIGN KEY (user_id) REFERENCES users(user_id),
  KEY idx_rcpt_queue (user_id, read_status, discarded_at, uploaded_at)
);

CREATE TABLE commitments (
  commitment_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id       INT UNSIGNED NOT NULL,
  category_id   INT UNSIGNED NOT NULL,
  kind          ENUM('bill','installment') NOT NULL,
  title         VARCHAR(120) NOT NULL,
  amount        INT UNSIGNED NOT NULL,
  total_amount  INT UNSIGNED NULL,
  months        TINYINT UNSIGNED NULL,
  paid_count    TINYINT UNSIGNED NOT NULL DEFAULT 0,
  due_day       TINYINT UNSIGNED NOT NULL,
  start_date    DATE         NOT NULL,
  next_due_date DATE         NOT NULL,
  status        ENUM('active','done','canceled') NOT NULL DEFAULT 'active',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cmt_user FOREIGN KEY (user_id)     REFERENCES users(user_id),
  CONSTRAINT fk_cmt_cat  FOREIGN KEY (category_id) REFERENCES categories(category_id),
  CONSTRAINT ck_cmt_amount CHECK (amount > 0),
  CONSTRAINT ck_cmt_due    CHECK (due_day BETWEEN 1 AND 31),
  CONSTRAINT ck_cmt_months CHECK (months IS NULL OR (months BETWEEN 1 AND 24)),
  CONSTRAINT ck_cmt_count  CHECK (paid_count <= COALESCE(months, 1)),
  KEY idx_cmt_user_due (user_id, status, next_due_date)
);

CREATE TABLE transactions (
  txn_id        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id       INT UNSIGNED NOT NULL,
  kind          ENUM('expense','income') NOT NULL,
  amount        INT UNSIGNED NOT NULL,
  txn_date      DATE         NOT NULL,
  category_id   INT UNSIGNED NOT NULL,
  source        VARCHAR(120) NULL,
  memo          VARCHAR(255) NULL,
  receipt_id    INT UNSIGNED NULL,
  commitment_id INT UNSIGNED NULL,
  source_kind   ENUM('chat','photo','manual') NOT NULL,
  deleted_at    DATETIME     NULL,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  active_receipt_id INT UNSIGNED
    GENERATED ALWAYS AS (IF(deleted_at IS NULL, receipt_id, NULL)) STORED,
  CONSTRAINT fk_txn_user     FOREIGN KEY (user_id)       REFERENCES users(user_id),
  CONSTRAINT fk_txn_cat_kind FOREIGN KEY (category_id, kind) REFERENCES categories(category_id, kind),
  CONSTRAINT fk_txn_rcpt     FOREIGN KEY (receipt_id)    REFERENCES receipts(receipt_id),
  CONSTRAINT fk_txn_cmt      FOREIGN KEY (commitment_id) REFERENCES commitments(commitment_id),
  CONSTRAINT ck_txn_amount   CHECK (amount > 0),
  UNIQUE KEY uq_txn_active_receipt (active_receipt_id),
  KEY idx_txn_cat_kind (category_id, kind),
  KEY idx_txn_user_date (user_id, deleted_at, txn_date),
  KEY idx_txn_user_cat  (user_id, deleted_at, category_id, txn_date),
  KEY idx_txn_user_cmt  (user_id, commitment_id)
);

CREATE TABLE chat_message (
  message_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id    INT UNSIGNED NOT NULL,
  role       ENUM('user','assistant') NOT NULL,
  body       TEXT         NOT NULL,
  payload    JSON         NULL,
  created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_chat_user FOREIGN KEY (user_id) REFERENCES users(user_id),
  KEY idx_chat_user (user_id, message_id)
);

CREATE TABLE memory_fact (
  fact_id    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id    INT UNSIGNED NOT NULL,
  topic      VARCHAR(40)  NOT NULL,
  value      VARCHAR(64)  NOT NULL,
  created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_fact_user FOREIGN KEY (user_id) REFERENCES users(user_id),
  UNIQUE KEY uq_fact (user_id, topic)
);

CREATE TABLE ai_usage (
  user_id    INT UNSIGNED NOT NULL,
  usage_date DATE         NOT NULL,
  call_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, usage_date),
  CONSTRAINT fk_usage_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**Decisions the DDL encodes, each from a review finding:**

- `transactions.commitment_id` has a FK and an index — the ER already claimed that relation (§13 #4).
- `commitments.category_id` exists — otherwise `mark_paid` cannot lawfully insert a row while `transactions.category_id` is NOT NULL (§13 #5).
- `transactions.source` is **nullable**. P0.5 proved a real receipt can have no readable shop name; `NOT NULL` would crash on save. The card shows 不明 (§13 #6).
- `receipts.discarded_at` replaces guessing — a discarded receipt leaves the queue permanently (§13 #7).
- `active_receipt_id` is a stored generated column: one *live* transaction per receipt, while soft-delete still allows undo then re-save (§13 #7).
- `due_day` is unsigned with a CHECK, and **due dates are computed, never incremented**: `date = min(due_day, last_day_of_month(year, month))` from the original `due_day`. A 31st bill must not drift to the 28th forever after one February (§13 #11).
- Installments store `amount = floor(total_amount / months)`; the **final** payment is `total_amount - amount * (months - 1)`, so ¥100,000 ÷ 6 loses no yen (§13 #12).
- `(category_id, kind)` composite FK makes an income row categorised as 食費 impossible at the database level (§13 #21).
- Indexes lead with `deleted_at` because every read filters on it (§13 #21).
- All timestamps are **JST**: the connection runs `SET time_zone = '+09:00'` and Python uses `ZoneInfo('Asia/Tokyo')`. The 24 h undo window and "today" checks must not depend on the server clock (§13 #23).

**Chat has no session id.** One row per message per user; "one main chat" is enforced by the schema, not by a filter in code.

Seed categories — expense: `food 食費`, `transport 交通費`, `daily 日用品`, `social 交際費`, `utility 光熱費`, `other その他`. Income: `salary 給与`, `support 仕送り`, `other_income その他収入`.

Money is a whole yen integer.

### Relations for ⑭ (redraw)

```
users 1 ── 0..* receipts            users 1 ── 0..* chat_message
users 1 ── 0..* commitments         users 1 ── 0..* memory_fact
users 1 ── 0..* transactions        users 1 ── 0..* ai_usage
categories 1 ── 0..* transactions   categories 1 ── 0..* commitments
commitments 1 ── 0..* transactions  receipts 1 ── 0..1 transactions
```

---

## 5. Chat, tools, and memory

Per request: system prompt + `memory_fact` rows (≤ 20) + last 20 `chat_message` rows. The model may call only these tools; it never writes SQL and never receives a `user_id` parameter — the server supplies it from the session, in every query.

| Tool | Arguments | Server validation |
|---|---|---|
| `record_expense` | amount, date, source?, category_code, memo? | amount > 0 and present in the user's digits; date not in the future; category must be an expense category |
| `record_income` | amount, date, source?, category_code | as above, income categories |
| `create_bill` | title, amount, due_day, start_date, category_code | due_day 1–31; `start_date` may be **up to +12 months** (a bill legitimately starts later) |
| `create_installment` | title, total_amount, months, due_day, start_date, category_code | months 1–24; total > 0; due_day 1–31 |
| `list_commitments` | status? | returns id, title, kind, amount, next_due_date, paid_count, months |
| `mark_paid` | commitment_id | row must belong to the session user and be active; increments `paid_count`; writes exactly one transaction |
| `query_money` | from, to, kind, category_code?, keyword?, group_by? | `keyword` → parameterised `LIKE` on `source`/`memo`; `group_by` ∈ none/category/source |
| `save_fact` | topic, value | **topic must be in a closed list** (`salary_day`, `rent_day`, `payday_amount`, `no_spend_weekday`, `currency`, `other`); day values normalised to 1–31 |
| `search_history` | keyword, from?, to? | read-only search of past `chat_message.body` and `transactions.source`/`memo` |

The `save_fact` closed list is not pedantry: P0.5 showed the model storing `topic: 給料日`. Thirty of those across three months is a facts table the prompt cannot use.

**Memory over months — what is real, not aspirational.** The database is the memory: 「先月コンビニでいくら?」 is `query_money(keyword='コンビニ')`. 「先月 何に一番使った?」 is `query_money(group_by='category')`. 「先月なんて言ったっけ?」 is `search_history`. There is **no background compaction job** — v2 claimed one and it did not exist. Messages are never deleted; only the last 20 ride in the prompt, and anything older is reachable through the tools.

---

## 6. Security (was missing in v2)

| Surface | Rule |
|---|---|
| Secrets | `.env` only, gitignored. The key pasted into chat on 2026-11-24 is burned — revoke it, issue a new one, never commit |
| Uploads | stored **outside** static dirs, filename = random UUID + `.jpg`; ≤ 5 MB; decoded and re-encoded with Pillow, which strips EXIF/GPS; HEIC converted client-side before upload |
| Serving images | never static. One route, `WHERE receipt_id = %s AND user_id = %s`, 404 on zero rows |
| Sessions | `SessionMiddleware(same_site='lax', https_only=True in production, max_age=…)`, secret from `.env`; logout rotates the cookie |
| CSRF | every mutating POST carries a per-session token; rejected with 403 otherwise |
| Password | `hashlib.scrypt(n=2**14, r=8, p=1)` with a 16-byte `secrets.token_bytes` salt, compared with `hmac.compare_digest` |
| Isolation (IDOR) | `user_id` appears in every WHERE clause, taken from the session only. Foreign keys do not enforce it; the handler does, failing closed on zero rows |
| SQL | parameter placeholders only; dynamic `ORDER BY`/filters from a hard allowlist |
| XSS | the swipe card renders with `textContent` only — never `innerHTML`, because `shop_name` comes from OCR and from an LLM |
| Abuse | login/register rate-limited per IP; `ai_usage` caps AI calls per user per day |

---

## 7. Delivery on a real phone (the demo risk)

- Use `<input type="file" accept="image/*" capture="environment">`. It works over plain HTTP and needs no camera permission; `getUserMedia` does not, so it is not the plan.
- **Downscale in the browser before upload** with Canvas to ≤ 1280 px JPEG q0.8. Measured latency on 12 MP photos was 6.9–11.0 s; small images are where the "2 seconds" claim becomes true.
- The demo runs over **HTTPS via a tunnel** (Cloudflare Tunnel or ngrok) so Add-to-Home-Screen, secure cookies and a stable URL all work. Laptop-over-LAN is the fallback, and it must be tested at the venue: campus Wi-Fi often blocks phone-to-laptop traffic. A phone hotspot is the third option — bring it.

---

## 8. Stack

| Layer | Choice | Reason |
|---|---|---|
| App form | Mobile-first web app, add to home screen | phone camera, one codebase |
| Language | Python 3.13 (`py -3.13`) | installed; 3.9 in PATH is unmaintained |
| Framework | FastAPI 0.165 | typed models reject bad AI arguments; `/docs` free for the report |
| Pages | Jinja2 3.1 server-rendered | login check stays on the server |
| Swipe card | plain JS pointer events | no dependency, no library fighting iOS Safari |
| Database | MySQL 8.4 | your WBS and 報告書 say MySQL |
| Driver | `mysql-connector-python` 26.10 | official wheel, no compiler, handles 8.4 auth |
| AI | `gemini-3.1-flash-lite` | measured cheapest **and** most accurate — §12 |

All of the above was verified installing cleanly on this machine in a throwaway venv on 2026-11-24.

---

## 9. Phases and gates

Corrected: v2 claimed a mid-December demo while its own phases ended 12/27, and put hardening on top of 年末年始. The holidays are now used for writing, not building.

| Phase | Dates | Deliverable | Gate (observed) |
|---|---|---|---|
| **P0 Base** | 11/24 – 11/30 | MySQL running, schema + seed applied, app boots, `/health` green, one page renders | fresh terminal installs and runs it from the README |
| **P0.5 技術検証** | 11/25 – 12/02 | receipt half **done**; owner's 10 receipts re-run; chat tools re-tested after the `save_fact` enum | a table with the pinned model name — class requirement |
| **P1 Chat spine** | 12/01 – 12/08 | sentence → deterministic gate → tool call → row → undo | 10 sentences on a phone; undo verified in the DB |
| **P2 Photo + swipe** | 12/09 – 12/17 | upload → read → swipe card → saved; queue; discard | 3 receipts cleared in < 30 s on a phone; one misread fixed via ← 修正 |
| **P3 Commitments** | 12/18 – 12/24 | bills, installments, due list, mark paid | 6-payment plan counts down; Feb-2027 `due_day=31` clamps and does not drift |
| **年末年始** | 12/25 – 01/04 | ⑭ ER図 + 要件定義書 Ver.3 redraw, manual draft, low capacity assumed | documents match the code |
| **P4 Ask & remember** | 01/05 – 01/12 | `query_money`, `search_history`, facts | a chat total equals the same total computed by hand in SQL |
| **P5 Hardening** | 01/13 – 01/20 | isolation, bad input, AI down, CSRF, upload abuse | user B cannot read user A's rows — proven by a test |
| **P6 Demo finish** | 01/21 – 01/29 | manual, poster, demo data, recorded run | full run recorded end to end |
| **Buffer** | 01/30 – 02/01 | fixes only | no new features |

---

## 10. Risks and what retires each

| Risk | Retired by |
|---|---|
| AI files a wrong amount | §2 deterministic gate + 24 h undo + `source_kind` trace |
| Chat prompt-injects a tool call (e.g. OCR text says "ignore rules") | `user_id` never a tool parameter; every handler scopes by session; validation per argument |
| Accidental swipe | 元に戻す on every saved card; ✕ 捨てる separate from ← 修正 |
| Receipt with no readable shop | `source` nullable, card shows 不明 |
| Feb-2027 `due_day` 29–31 | clamp by computing from `due_day` each period; test in P3 |
| Installment remainder lost | `amount = floor`, final payment absorbs the remainder; test with ¥100,000 ÷ 6 |
| Long chat slows or forgets | last 20 messages + facts + `search_history`; numbers always from SQL |
| 12 MP photo takes 11 s | client-side downscale to ≤ 1280 px before upload |
| iPhone HEIC breaks the pipeline | Canvas converts to JPEG in the browser |
| Campus Wi-Fi blocks the phone | HTTPS tunnel first, hotspot as backup, tested at the venue |
| MySQL install fails on Windows | one install block, MariaDB 13 documented fallback |
| Chat cost runs away | `ai_usage` daily cap, cheap model, measured at ~¥0.06/receipt |
| Data leak between users | session-scoped queries + XSS/CSRF rules + isolation test in P5 |
| Graduation grading wants explanation | `AGENTS.md` forbids code comments; the explanation lives in `docs/` and `DECISIONS.md`, which is what the presentation cites |

---

## 11. Facts vs assumptions

**Facts:** 4 original entities and cardinalities (`20261112.pdf`, `kadai1.pdf`, ER images) · flow ⑯, 17 nodes, 16 edges, 3 error exits · 54 WBS tasks, 2026/11/10 → 2027/02/01, all dates 仮 · メモ and チャット履歴 required by WBS 3.5 / 3.8 · 技術検証 mandated by `第6週1日目` · `major.pdf` is a university brochure; no academic calendar exists in your set · all stack packages install on Python 3.13 (verified 2026-11-24).

**Assumptions:** 卒業展 on or after 2027-02-01 · yen only · bills become spending only when marked paid · nine seeded categories · demo over an HTTPS tunnel · chat accepts Japanese, English and mixed input.

---

## 12. P0.5 evidence, corrected

v2 reported "amount 4/5". That counted a `null == null` case as a pass. The honest numbers, on receipts that actually carry a total:

| measure | value |
|---|---|
| amount correct (4 receipts with a total) | **3/4 (75%)** |
| amount correct counting the unknown-total case as correct | 4/5 |
| date correct | 5/5 |
| shop correct | 4/5 |
| category | 5/5 |
| **guessed when the truth was unknown** | **0** |

75% is below the 80% floor I set — so the escalation rule triggers on the owner's own 10 receipts, not on convenience. Tests after the first also overwrote `result_real.json`; per-model result files are now written separately so evidence cannot be replaced by a later run.

The zero-guess result is the one that matters most, because §2 depends on it.

---

## 13. Review log — v2 → v3

| # | Finding | Fixed by |
|---|---|---|
| 1 | API key pasted into chat | §6 secrets rule; revoke and reissue |
| 2 | `uploads/` unauthenticated, unvalidated, EXIF | §6 upload rules + authenticated image route |
| 3 | No CSRF, loose cookies, no session policy | §6 sessions + CSRF |
| 4 | `commitment_id` had no FK; table order broke it | §4 DDL order + `fk_txn_cmt` |
| 5 | `commitments` had no `category_id`, so `mark_paid` could not insert | §4 `category_id` + tool signature |
| 6 | `source NOT NULL` crashed on a receipt with no shop name | §4 nullable `source` |
| 7 | ✕ 捨てる created zombie cards; soft-delete blocked re-save | §4 `discarded_at` + `active_receipt_id` |
| 8 | "Never guesses" relied on the model | §2 deterministic digit and date-token checks |
| 9 | No way to list commitments, so 「家賃払った」 was unresolvable | `list_commitments` tool |
| 10 | Blanket "no future date" blocked 「来月から」 | §5 scoped to transactions; +12 months on start |
| 11 | `due_day` 29–31 crashed or drifted in February | §4 CHECK + computed clamping |
| 12 | Installment remainder lost; undo did not roll back | §4 remainder rule + atomic mark_paid |
| 13 | `query_money` could not answer 「先月コンビニで」 | §5 `keyword` + `group_by` |
| 14 | Chat compaction was claimed but did not exist | §5 `search_history` replaces vaporware |
| 15 | Cross-user IDOR through tool parameters | §6 `user_id` never a tool parameter |
| 16 | Stored XSS via `innerHTML` on OCR text | §6 `textContent` only |
| 17 | Overstated accuracy; evidence overwritten | §12 corrected + per-model files |
| 18 | 12 MP latency contradicted the 2-second claim; HEIC | §7 client-side downscale + conversion |
| 19 | Laptop-HTTP demo breaks PWA and camera; campus Wi-Fi | §7 tunnel, hotspot, venue test |
| 20 | DoD contradicted §2; double-tap could write twice | §1 DoD aligned + `FOR UPDATE` |
| 21 | Indexes ignored `deleted_at`; kind could mismatch category | §4 indexes + composite FK |
| 22 | Schedule contradictions and holiday crunch | §9 dates corrected |
| 23 | Mixed timezones around "today" and 24 h undo | §4 JST everywhere |
| 24 | "Daily cap" had no table; scrypt params unspecified | §4 `ai_usage`, §6 scrypt parameters |
| 25 | Receipt schema forced a category on a non-receipt | §5, and P0.5 schema in `run_real.py` |

Rejected: allowing code comments to help the team explain the code. `AGENTS.md` forbids them and says not to edit it; the explanation lives in `docs/` and `DECISIONS.md` instead, which is better for the presentation anyway.

---

## 14. Still open

1. **Auto-post bills?** Today a bill waits for 「払った」. Should it file itself on the due date?
2. **Your own categories?** Nine seeded values are fixed. May the AI create a new one from chat?
3. **Real dates** — 卒業展 and 要件定義書 submission dates, if you have them.
4. **Team paperwork** — four names in the plan, or written as you + me?
