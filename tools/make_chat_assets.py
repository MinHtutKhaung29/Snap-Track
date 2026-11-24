import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

CHAT = "\n".join(
    [
        '{% extends "base.html" %}',
        "{% block title %}チャット — Snap &amp; Track{% endblock %}",
        "{% block nav %}",
        '  <span class="who">{{ user.name }}',
        '    <form method="post" action="/logout">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <button type="submit" class="linkbtn">ログアウト</button>',
        "    </form>",
        "  </span>",
        "{% endblock %}",
        "{% block content %}",
        '<section class="thread" id="thread">',
        "  {% if not messages %}",
        '  <div class="msg bot"><p>こんにちは。例のように話しかけてください。</p><p class="ex">「今日 ランチ 850円」<br>「今月の食費いくら?」</p></div>',
        "  {% endif %}",
        "  {% for m in messages %}",
        '    {% if m.role == "user" %}',
        '    <div class="msg me"><p>{{ m.body }}</p></div>',
        "    {% else %}",
        '    <div class="msg bot">',
        "      <p>{{ m.body }}</p>",
        '      {% if m.payload and m.payload.type == "saved" and m.payload.txn %}\n'
        '      <form method="post" action="/undo/{{ m.payload.txn.txn_id }}" class="inline">\n'
        '        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">\n'
        '        <button type="submit" class="ghost">元に戻す</button>\n'
        "      </form>",
        "      {% elif m.payload and m.payload.type == 'proposal' and m.payload.status == 'pending' %}",
        '      <div class="card mini">',
        "        <dl class=\"kv\">",
        "          <dt>金額</dt><dd>¥{{ m.payload.preview.amount }}</dd>",
        "          <dt>日付</dt><dd>{{ m.payload.preview.date }}</dd>",
        "          <dt>内容</dt><dd>{{ m.payload.preview.source or '店名なし' }}</dd>",
        "          <dt>分類</dt><dd>{{ m.payload.preview.category }}</dd>",
        "        </dl>",
        '        {% if m.payload.preview.reason == "date_inferred" %}<p class="warn">日付は推測です。確認してください。</p>{% endif %}',
        '        {% if m.payload.preview.reason == "amount_not_in_message" %}<p class="warn">金額がメッセージにありません。</p>{% endif %}',
        '        <div class="row">',
        '          <form method="post" action="/chat/confirm/{{ m.message_id }}">',
        '            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '            <button type="submit">保存する</button>',
        "          </form>",
        '          <form method="post" action="/chat/cancel/{{ m.message_id }}">',
        '            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '            <button type="submit" class="ghost">キャンセル</button>',
        "          </form>",
        "        </div>",
        "      </div>",
        "      {% endif %}",
        "    </div>",
        "    {% endif %}",
        "  {% endfor %}",
        "</section>",
        '<form method="post" action="/chat" class="composer">',
        '  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '  <input type="text" name="message" placeholder="今日 ランチ 850円" autocomplete="off" required autofocus>',
        '  <button type="submit">送信</button>',
        "</form>",
        "{% endblock %}",
        "{% block foot %}",
        "<script>var t=document.getElementById('thread');if(t){window.scrollTo(0,document.body.scrollHeight);}</script>",
        "{% endblock %}",
        "",
    ]
)

CSS = "\n".join(
    [
        ".thread{display:flex;flex-direction:column;gap:10px;padding-bottom:90px}",
        ".msg{max-width:86%;padding:10px 14px;border-radius:16px;font-size:15px;line-height:1.55}",
        ".msg p{margin:0}",
        ".msg.me{align-self:flex-end;background:#2563eb;color:#fff;border-bottom-right-radius:6px}",
        ".msg.bot{align-self:flex-start;background:var(--card);border:1px solid var(--line);border-bottom-left-radius:6px}",
        ".msg .ex{margin-top:6px;color:var(--muted);font-size:13px}",
        ".composer{position:fixed;left:0;right:0;bottom:0;display:flex;gap:8px;padding:10px 12px calc(10px + env(safe-area-inset-bottom));background:rgba(15,23,42,.95);border-top:1px solid var(--line);backdrop-filter:blur(8px)}",
        ".composer input{flex:1;padding:13px 14px;border-radius:12px;border:1px solid var(--line);background:#0d1526;color:var(--fg);font-size:16px}",
        ".composer button{padding:13px 18px;border:0;border-radius:12px;background:#2563eb;color:#fff;font-weight:600;font-size:15px}",
        ".card.mini{margin-top:10px;padding:12px;border-radius:12px;background:#0d1526;border:1px solid var(--line)}",
        ".kv{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:0 0 10px;font-size:14px}",
        ".kv dt{color:var(--muted)}",
        ".kv dd{margin:0;font-variant-numeric:tabular-nums}",
        ".row{display:flex;gap:8px}",
        ".row form{margin:0;flex:1}",
        ".row button{width:100%;padding:11px;border:0;border-radius:10px;background:#16a34a;color:#fff;font-weight:600;font-size:15px}",
        ".ghost{background:transparent!important;border:1px solid var(--line)!important;color:var(--muted)!important;font-weight:500!important}",
        ".inline{margin:8px 0 0}",
        ".inline button{padding:7px 12px;border-radius:8px;font-size:13px}",
        ".warn{margin:8px 0 0;font-size:13px;color:#fbbf24}",
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
if ".thread{" in css:
    print("css already contains chat rules, skipped")
else:
    with open(css_path, "a", encoding="utf-8", newline="\n") as f:
        f.write(CSS)
    print("appended chat rules to base.css")
