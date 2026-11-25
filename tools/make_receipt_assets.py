import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

RECEIPTS = "\n".join(
    [
        '{% extends "base.html" %}',
        "{% block title %}写真から記録 — Snap &amp; Track{% endblock %}",
        "{% block nav %}",
        '  <span class="who"><span class="uname">{{ user.name }}</span>',
        '    <a class="linkbtn" href="/chat">チャット</a>',
        '    <form method="post" action="/logout">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <button type="submit" class="linkbtn">ログアウト</button>',
        "    </form>",
        "  </span>",
        "{% endblock %}",
        "{% block content %}",
        '<section class="queue">',
        "  {% if error_message %}",
        '  <p class="err" role="alert">{{ error_message }}</p>',
        "  {% endif %}",
        "  {% if request.query_params.get('discarded') %}",
        '  <p class="note">1件を捨てました。</p>',
        "  {% endif %}",
        "  {% if not card %}",
        '  <div class="empty">',
        "    <p class=\"empty-title\">未確認の写真はありません</p>",
        '    <p class="hint">チャットの📷から追加できます。</p>',
        '    <a class="primary btn-link" href="/chat">チャットへ</a>',
        "  </div>",
        "  {% else %}",
        '  <div class="queue-head"><span>確認</span><span class="count">{{ index }} / {{ total }}</span></div>',
        '  <div class="shot-wrap"><img class="shot" src="/receipts/{{ card.receipt_id }}/image" alt=""></div>',

        "  {% if card.mode == 'unreadable' %}",
        '  <div class="ask">',
        '    <p class="ask-title">お支払いとして読み取れませんでした</p>',
        '    <p class="ask-sub">レシートの写真でも、支払い画面のスクリーンショットでもかまいません。金額が見える画像を選んでください。</p>',
        '    <div class="stack">',
        '      <a class="primary btn-link" href="/chat">もう一度とる</a>',
        '      <a class="ghost btn-link" href="/receipts?manual=1">手入力で登録</a>',
        '      <form method="post" action="/receipts/{{ card.receipt_id }}/discard" class="discard-inline">',
        '        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '        <button type="submit" class="ghost">この画像を捨てる</button>',
        "      </form>",
        "    </div>",
        "  </div>",

        "  {% else %}",
        '  <form method="post" action="/receipts/{{ card.receipt_id }}/save" class="ask" id="save-form">',
        '    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        "    {% if card.mode == 'ask' %}",
        '    <p class="ask-title">{% if card.want_amount %}金额を教えてください{% else %}内容を確かめてください{% endif %}</p>',
        "    {% endif %}",

        '    <label class="field{% if card.want_amount %} field-missing{% endif %}">',
        '      <span class="field-label">金額{% if card.want_amount %}<em>読み取れませんでした</em>{% endif %}</span>',
        '      <span class="field-input"><span class="yen">¥</span>',
        '        <input type="number" name="amount" value="{{ card.display_amount or "" }}" min="1" inputmode="numeric" placeholder="0" {% if card.want_amount %}required autofocus{% endif %}>',
        "      </span>",
        "    </label>",

        '    <label class="field{% if card.want_date %} field-missing{% endif %}">',
        '      <span class="field-label">日付{% if card.want_date %}<em>推測できません。今日を入れてあります</em>{% endif %}</span>',
        '      <input type="date" name="date" value="{{ override.date or card.data.date or today }}">',
        "    </label>",

        '    <label class="field">',
        '      <span class="field-label">店・内容</span>',
        '      <input type="text" name="shop" value="{{ override.shop or card.data.shop or "" }}" maxlength="120" placeholder="セブン-イレブン、家賃 など">',
        "    </label>",

        '    <div class="field">',
        '      <span class="field-label">分類{% if card.want_category %}<em>選んでください</em>{% endif %}</span>',
        '      <div class="chips">',
        "        {% for c in categories %}",
        '        <input type="radio" name="category_code" id="cat{{ loop.index }}" value="{{ c.code }}" {% if c.code == card.data.category_code %}checked{% endif %}>',
        '        <label for="cat{{ loop.index }}">{{ c.category_name }}</label>',
        "        {% endfor %}",
        "      </div>",
        "    </div>",

        '    <div class="actions">',
        '      <button type="submit" class="primary">保存する</button>',
        "    </div>",
        "  </form>",
        '  <form method="post" action="/receipts/{{ card.receipt_id }}/discard" class="discard-inline">',
        '    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '    <button type="submit" class="ghost">この画像を捨てる</button>',
        "  </form>",
        "  {% endif %}",
        "  {% endif %}",
        "</section>",
        "{% endblock %}",
        "",
    ]
)

CSS = "\n".join(
    [
        ".queue{max-width:520px;margin:0 auto;padding-bottom:40px}",
        ".queue-head{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--muted);margin-bottom:8px;letter-spacing:.04em}",
        ".count{font-variant-numeric:tabular-nums}",
        ".shot-wrap{background:#0b1220;border:1px solid var(--line);border-radius:16px;overflow:hidden;margin-bottom:12px}",
        ".shot{display:block;width:100%;max-height:300px;object-fit:contain}",
        ".ask{display:grid;gap:14px}",
        ".ask-title{margin:0;font-size:15px;font-weight:600}",
        ".ask-sub{margin:-6px 0 0;font-size:13px;color:var(--muted);line-height:1.6}",
        ".field{display:grid;gap:6px}",
        ".field-label{font-size:12px;color:var(--muted);letter-spacing:.03em;display:flex;justify-content:space-between;gap:8px}",
        ".field-label em{font-style:normal;color:#fbbf24;font-size:11px}",
        ".field input{width:100%;min-height:48px;padding:0 14px;border-radius:12px;border:1px solid var(--line);background:#0d1526;color:var(--fg);font-size:16px}",
        ".field-missing input{border-color:#7c5a12;background:#1a1508}",
        ".field-input{display:flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:12px;background:#0d1526;padding-left:12px}",
        ".field-input input{border:0;background:transparent;padding-left:0}",
        ".field-missing .field-input{border-color:#7c5a12;background:#1a1508}",
        ".yen{font-size:18px;color:var(--muted)}",
        ".chips{display:flex;flex-wrap:wrap;gap:8px}",
        ".chips input{position:absolute;opacity:0;pointer-events:none}",
        ".chips label{padding:9px 14px;border-radius:999px;border:1px solid var(--line);background:#0d1526;font-size:13.5px;color:var(--fg);cursor:pointer}",
        ".chips input:checked+label{background:#1d4ed8;border-color:#1d4ed8;color:#fff;font-weight:600}",
        ".actions button{width:100%;min-height:52px;border:0;border-radius:13px;font-weight:700;font-size:16px}",
        ".discard-inline{margin-top:10px}",
        ".discard-inline button{width:100%;min-height:44px;border-radius:11px;font-size:13px}",
        ".stack{display:grid;gap:10px;margin-top:6px}",
        ".btn-link{display:flex;align-items:center;justify-content:center;min-height:50px;border-radius:13px;text-decoration:none;font-weight:700}",
        ".empty{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:28px 20px;text-align:center}",
        ".empty-title{margin:0 0 6px;font-weight:600}",
        "",
    ]
)


def write(rel, content):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("wrote", rel.replace(os.sep, "/"), os.path.getsize(path), "bytes")


write(os.path.join("app", "receipts", "templates", "receipts.html"), RECEIPTS)
write(os.path.join("app", "static", "receipts.css"), CSS)
