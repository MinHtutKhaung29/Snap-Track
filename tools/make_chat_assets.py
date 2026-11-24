import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

CHAT = "\n".join(
    [
        '{% extends "base.html" %}',
        "{% block title %}チャット — Snap &amp; Track{% endblock %}",
        "{% block nav %}",
        '  <span class="who"><span class="uname">{{ user.name }}</span>',
        '    <form method="post" action="/logout">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <button type="submit" class="linkbtn">ログアウト</button>',
        "    </form>",
        "  </span>",
        "{% endblock %}",
        "{% block content %}",
        '<section class="thread" id="thread">',
        "  {% if not messages %}",
        '  <div class="msg bot intro">',
        "    <p>支出や質問をそのまま送ってください。</p>",
        '    <p class="ex">',
        '      <button type="button" class="chip" data-fill="今日 ランチ 850円">今日 ランチ 850円</button>',
        '      <button type="button" class="chip" data-fill="今月の食費いくら？">今月の食費いくら？</button>',
        "    </p>",
        "  </div>",
        "  {% endif %}",
        "  {% for m in messages %}",
        '    {% set p = m.payload %}',
        '    {% if m.role == "user" %}',
        '    <div class="msg me"><p>{{ m.body }}</p></div>',
        '    {% elif p and p.type == "saved" and p.txn %}',
        '    <div class="msg bot entry">',
        '      <div class="label">記録しました</div>',
        '      <div class="amt">¥{{ "{:,}".format(p.txn.amount) }}</div>',
        '      <div class="meta"><span>{{ p.txn.category }}</span><span class="pill">{{ p.txn.source or "未入力" }}</span><span class="sub">{{ p.txn.date_label }}</span></div>',
        '      <form method="post" action="/undo/{{ p.txn.txn_id }}" class="inline">',
        '        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '        <button type="submit" class="ghost">取り消す</button>',
        "      </form>",
        "    </div>",
        '    {% elif p and p.type == "undone" and p.txn %}',
        '    <div class="msg bot entry undone">',
        '      <div class="label">取り消し済み</div>',
        '      <div class="amt strike">¥{{ "{:,}".format(p.txn.amount) }}</div>',
        '      <div class="meta"><span>{{ p.txn.category }}</span><span class="sub">{{ p.txn.date_label }}</span></div>',
        "    </div>",
        '    {% elif p and p.type == "proposal" and p.status == "pending" %}',
        '    <div class="msg bot entry pending">',
        '      <div class="label">この内容で記録しますか？</div>',
        '      <div class="amt">¥{{ "{:,}".format(p.preview.amount) }}</div>',
        '      <div class="meta"><span>{{ p.preview.category }}</span><span class="pill">{{ p.preview.source or "未入力" }}</span></div>',
        '      <div class="meta"><span class="sub">{{ p.preview.date_label }}</span></div>',
        '      {% if p.preview.reason == "date_inferred" %}<p class="warn">日付は推測です。違っていれば「直す」で変更できます。</p>{% endif %}',
        '      {% if p.preview.reason == "amount_not_in_message" %}<p class="warn">金額がメッセージにありません。</p>{% endif %}',
        '      <div class="row">',
        '        <form method="post" action="/chat/confirm/{{ m.message_id }}">',
        '          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '          <button type="submit" class="primary">保存する</button>',
        "        </form>",
        '        <form method="post" action="/chat/cancel/{{ m.message_id }}">',
        '          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '          <button type="submit" class="ghost">やめる</button>',
        "        </form>",
        "      </div>",
        '      <details class="edit">',
        "        <summary>直す</summary>",
        '        <form method="post" action="/chat/confirm/{{ m.message_id }}" class="form tight">',
        '          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '          <label>金額<input type="number" name="amount" value="{{ p.preview.amount }}" min="1" inputmode="numeric"></label>',
        '          <label>日付<input type="date" name="date" value="{{ p.preview.date }}"></label>',
        '          <label>分類<select name="category_code">',
        '            {% for c in categories %}<option value="{{ c.code }}" {% if c.category_name == p.preview.category %}selected{% endif %}>{{ c.category_name }}</option>{% endfor %}',
        "          </select></label>",
        '          <button type="submit" class="primary">この内容で保存</button>',
        "        </form>",
        "      </details>",
        "    </div>",
        '    {% elif p and p.type == "answer" and p.data %}',
        '    <div class="msg bot answer">',
        '      <div class="label">{{ "支出" if p.data.kind == "expense" else "収入" }}合計<span class="dot">・</span>{{ p.data.from }} 〜 {{ p.data.to }}</div>',
        '      <div class="amt">¥{{ "{:,}".format(p.data.total) }}</div>',
        "      {% if p.data.rows|length > 1 %}",
        '      <ul class="lines">',
        "        {% for r in p.data.rows %}",
        '        <li><span>{{ r.category }}</span><span class="num">¥{{ "{:,}".format(r.total) }}</span><em>{{ r.count }}件</em></li>',
        "        {% endfor %}",
        "      </ul>",
        "      {% endif %}",
        "    </div>",
        "    {% else %}",
        '    <div class="msg bot"><p>{{ m.body }}</p></div>',
        "    {% endif %}",
        "  {% endfor %}",
        "</section>",
        '<form method="post" action="/chat" class="composer">',
        '  <div class="composer-inner">',
        '    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '    <input type="text" name="message" placeholder="今日 ランチ 850円" autocomplete="off" required autofocus>',
        '    <button type="submit">送信</button>',
        "  </div>",
        "</form>",
        "{% endblock %}",
        "{% block foot %}",
        "<script>",
        "var t=document.getElementById('thread');if(t){window.scrollTo(0,document.body.scrollHeight);}",
        "document.querySelectorAll('.chip').forEach(function(c){c.addEventListener('click',function(){var i=document.querySelector('.composer input[name=message]');i.value=c.dataset.fill;i.focus();});});",
        "</script>",
        "{% endblock %}",
        "",
    ]
)

CSS = "\n".join(
    [
        ".thread{display:flex;flex-direction:column;gap:10px;padding-bottom:130px;max-width:640px;margin:0 auto}",
        ".msg{max-width:92%;padding:12px 14px;border-radius:16px;font-size:15px;line-height:1.55}",
        ".msg p{margin:0}",
        ".msg.me{align-self:flex-end;background:#2563eb;color:#fff;border-bottom-right-radius:6px;max-width:86%}",
        ".msg.bot{align-self:flex-start;background:var(--card);border:1px solid var(--line);border-bottom-left-radius:6px}",
        ".msg.intro .ex{margin-top:10px;display:flex;flex-wrap:wrap;gap:8px}",
        ".chip{background:#0d1526;border:1px solid var(--line);color:#93c5fd;font-size:13px;padding:10px 12px;border-radius:999px;min-height:40px}",
        ".entry{min-width:min(300px,92%)}",
        ".label{font-size:12px;color:var(--muted);letter-spacing:.02em;margin-bottom:6px}",
        ".amt{font-size:30px;font-weight:700;letter-spacing:-.01em;font-variant-numeric:tabular-nums;line-height:1.15}",
        ".meta{margin-top:8px;font-size:13px;color:var(--fg);display:flex;flex-wrap:wrap;align-items:center;gap:8px}",
        ".pill{background:#0d1526;border:1px solid var(--line);color:#cbd5e1;font-size:12px;padding:3px 10px;border-radius:999px}",
        ".sub{font-size:12.5px;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap}",
        ".dot{margin:0 6px;opacity:.5}",
        ".strike{text-decoration:line-through;opacity:.55}",
        ".undone{opacity:.65}",
        ".pending{border-color:#2f4670}",
        ".warn{margin:10px 0 0;font-size:12.5px;color:#fbbf24;line-height:1.5}",
        ".row{display:flex;gap:8px;margin-top:12px}",
        ".row form{margin:0;flex:1}",
        ".row button{width:100%;min-height:46px;border:0;border-radius:11px;font-weight:700;font-size:15px}",
        ".primary{background:#15803d;color:#fff}",
        ".primary:active{background:#166534}",
        ".ghost{background:transparent;border:1px solid var(--line);color:var(--muted);font-weight:500}",
        ".inline{margin:12px 0 0}",
        ".inline button{min-height:44px;padding:0 18px;border-radius:10px;font-size:13.5px}",
        ".edit{margin-top:6px}",
        ".edit summary{list-style:none;cursor:pointer;color:#60a5fa;font-size:13.5px;padding:12px 0;min-height:44px;display:flex;align-items:center}",
        ".edit summary::-webkit-details-marker{display:none}",
        ".form.tight{gap:10px;margin-top:4px}",
        ".form.tight input,.form.tight select{padding:11px 12px;border-radius:10px;border:1px solid var(--line);background:#0d1526;color:var(--fg);font-size:16px}",
        ".form.tight button{min-height:46px;border:0;border-radius:11px;font-weight:700;font-size:15px}",
        ".answer{min-width:min(300px,92%)}",
        ".lines{list-style:none;margin:14px 0 0;padding:0;display:grid;gap:6px;font-size:14px}",
        ".lines li{display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:baseline}",
        ".lines .num{font-variant-numeric:tabular-nums;font-weight:600}",
        ".lines em{font-style:normal;color:var(--muted);font-size:12px;min-width:34px;text-align:right}",
        ".composer{position:fixed;left:0;right:0;bottom:0;background:rgba(15,23,42,.96);border-top:1px solid var(--line);backdrop-filter:blur(8px);padding:10px 12px calc(10px + env(safe-area-inset-bottom))}",
        ".composer-inner{max-width:640px;margin:0 auto;display:flex;gap:8px}",
        ".composer input{flex:1;min-height:48px;padding:0 14px;border-radius:12px;border:1px solid var(--line);background:#0d1526;color:var(--fg);font-size:16px}",
        ".composer input:focus{outline:2px solid #3b82f6;outline-offset:1px}",
        ".composer button{min-width:72px;min-height:48px;border:0;border-radius:12px;background:#2563eb;color:#fff;font-weight:700;font-size:15px}",
        ".who{display:flex;align-items:center;gap:10px;font-size:13.5px;color:var(--muted);min-width:0}",
        ".uname{max-width:32vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}",
        ".who form{margin:0}",
        ".linkbtn{min-height:44px;padding:0 2px;display:inline-flex;align-items:center;background:none;border:0;color:#60a5fa;font:inherit;cursor:pointer}",
        "",
    ]
)

REGISTER_EXTRA = "\n".join(
    [
        ".field-hint{margin:-2px 0 0;font-size:12px;color:var(--muted)}",
        "",
    ]
)


def write(rel, content):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("wrote", rel.replace(os.sep, "/"), os.path.getsize(path), "bytes")


write(os.path.join("app", "chat", "templates", "chat.html"), CHAT)

css_path = os.path.join(ROOT, "app", "static", "base.css")
with open(css_path, encoding="utf-8") as f:
    css = f.read()
marker = ".thread{display:flex;flex-direction:column;gap:10px;padding-bottom:130px"
if marker in css:
    head, _, _ = css.partition(marker)
    with open(css_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(head + CSS + REGISTER_EXTRA)
    print("replaced chat css block")
else:
    with open(css_path, "a", encoding="utf-8", newline="\n") as f:
        f.write(CSS + REGISTER_EXTRA)
    print("appended chat css block")
