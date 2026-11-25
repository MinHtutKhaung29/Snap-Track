import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

DUE_PAGE = "\n".join(
    [
        '{% extends "base.html" %}',
        "{% block title %}支払い予定 — Snap &amp; Track{% endblock %}",
        "{% block heading %}支払い予定{% endblock %}",
        "{% block content %}",
        '<section class="due">',
        '  {% if note %}<p class="note" role="status">{{ note }}</p>{% endif %}',
        '  {% if error_message %}<p class="err" role="alert">{{ error_message }}</p>{% endif %}',
        "  {% if not rows %}",
        '  <div class="empty">',
        "    <p class=\"empty-title\">支払い予定はありません</p>",
        '    <p class="hint">チャットで「家賃 85000円 27日払い」のように話しかけると登録できます。</p>',
        '    <a class="primary btn-link" href="/chat">チャットへ</a>',
        "  </div>",
        "  {% else %}",
        '  <ul class="list">',
        "    {% for r in rows %}",
        '    <li class="item{% if r.is_due %} due{% endif %}{% if r.overdue %} overdue{% endif %}">',
        '      <div class="item-head">',
        '        <span class="item-title">{{ r.title }}</span>',
        '        <span class="item-kind">{{ "分割払い" if r.kind == "installment" else "毎月" }}</span>',
        "      </div>",
        '      <div class="item-amount">¥{{ "{:,}".format(r.next_amount) }}</div>',
        '      <div class="sheet">',
        '        <div class="row"><span class="row-k">次回</span><span class="row-v">{{ r.next_due_date_label }}{% if r.overdue %} <em class="flag">期限超過</em>{% endif %}</span></div>',
        '        <div class="row"><span class="row-k">分類</span><span class="row-v">{{ r.category_name }}</span></div>',
        '        <div class="row"><span class="row-k">支払済み</span><span class="row-v">{% if r.kind == "installment" %}{{ r.paid_count }} / {{ r.months }} 回{% else %}{{ r.paid_count }} 回{% endif %}</span></div>',
        '        {% if r.kind == "installment" %}<div class="row"><span class="row-k">残り</span><span class="row-v">{{ r.remaining }} 回</span></div>{% endif %}',
        "      </div>",
        '      <form method="post" action="/commitments/{{ r.id }}/pay" class="pay-form">',
        '        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '        <input type="hidden" name="expected_due_date" value="{{ r.next_due_date }}">',
        '        <input type="hidden" name="expected_last_txn_id" value="{{ r.last_txn_id }}">',
        '        <button type="submit" class="{{ "primary" if r.is_due else "ghost" }}"{% if not r.is_due %} disabled{% endif %}>支払った</button>',
        "      </form>",
        '      {% if not r.is_due %}<p class="hint">支払期日が来ると押せます。</p>{% endif %}',
        "    </li>",
        "    {% endfor %}",
        "  </ul>",
        "  {% endif %}",
        "</section>",
        "{% endblock %}",
        "",
    ]
)

MSG_PART = "\n".join(
    [
        "{% set p = m.payload %}",
        '{% if p and p.type == "commitment_payment" and p.status == "pending" %}',
        '<div class="msg bot entry pending">',
        '  <div class="label">この支払いを記録しますか？</div>',
        '  <div class="amt">−¥{{ "{:,}".format(p.preview.amount) }}</div>',
        '  <div class="meta"><span>{{ p.preview.title }}</span><span class="sub">{{ p.preview.due_date_label }}</span></div>',
        '  <div class="meta"><span class="cat"><i></i>{{ p.preview.category }}</span><span class="sub">記録日 {{ p.preview.date_label }}</span></div>',
        '  <div class="acts">',
        '    <form method="post" action="/chat/confirm/{{ m.message_id }}">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <button type="submit" class="primary">支払った</button>',
        "    </form>",
        '    <form method="post" action="/chat/cancel/{{ m.message_id }}">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <button type="submit" class="ghost">やめる</button>',
        "    </form>",
        "  </div>",
        "</div>",
        '{% elif p and p.type == "commitment_proposal" and p.status == "pending" %}',
        '<div class="msg bot entry pending">',
        '  <div class="label">この支払い予定を作りますか？</div>',
        '  <div class="amt">¥{{ "{:,}".format(p.preview.amount) }}</div>',
        '  <div class="meta"><span>{{ p.preview.title }}</span><span class="cat"><i></i>{{ p.preview.category }}</span></div>',
        '  <div class="meta"><span class="sub">{{ p.preview.schedule_label }}</span><span class="sub">初回 {{ p.preview.first_due_date_label }}</span></div>',
        '  <p class="warn">作成しても支出にはなりません。支払ったときに記録されます。</p>',
        '  <div class="acts">',
        '    <form method="post" action="/chat/confirm/{{ m.message_id }}">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <button type="submit" class="primary">作成する</button>',
        "    </form>",
        '    <form method="post" action="/chat/cancel/{{ m.message_id }}">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <button type="submit" class="ghost">やめる</button>',
        "    </form>",
        "  </div>",
        "</div>",
        '{% elif p and p.type == "commitment" and p.commitment %}',
        '<div class="msg bot entry">',
        '  <div class="amt">¥{{ "{:,}".format(p.commitment.amount) }}</div>',
        '  <div class="meta"><span>{{ p.commitment.title }}</span>{% if p.commitment.category_name %}<span class="cat"><i></i>{{ p.commitment.category_name }}</span>{% endif %}</div>',
        '  <div class="meta"><span class="sub">{{ p.commitment.schedule_label }}</span><span class="sub">初回 {{ p.commitment.next_due_date_label }}</span></div>',
        '  <a class="more" href="/commitments">支払い予定を見る</a>',
        "</div>",
        "{% else %}",
        '<div class="msg bot"><p>{{ m.body }}</p>{% if show_time and m.created_at %}<span class="ts">{{ m.created_at.strftime("%H:%M") }}</span>{% endif %}</div>',
        "{% endif %}",
        "",
    ]
)

CSS = "\n".join(
    [
        ".due{padding-bottom:calc(16px + env(safe-area-inset-bottom))}",
        ".list{list-style:none;margin:0;padding:0;display:grid;gap:12px}",
        ".item{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px}",
        ".item.overdue{border-color:#9a5b12}",
        ".item-head{display:flex;align-items:baseline;gap:8px}",
        ".item-title{flex:1;min-width:0;font-size:var(--t3);font-weight:600;line-height:1.4;color:var(--muted);overflow-wrap:anywhere}",
        ".item.due .item-title{color:var(--fg)}",
        ".item-kind{flex:0 0 auto;font-size:var(--t5);color:var(--muted);letter-spacing:.04em}",
        ".item-amount{margin:4px 0 12px;font-size:var(--t2);font-weight:600;line-height:1.3;letter-spacing:-.01em;color:var(--muted);font-variant-numeric:tabular-nums}",
        ".item.due .item-amount{font-size:var(--t1);color:var(--fg)}",
        ".item .sheet{background:var(--field)}",
        ".item .sheet .row{padding:0 12px}",
        ".flag{font-style:normal;font-size:var(--t5);color:var(--ng)}",
        ".pay-form{margin:12px 0 0}",
        ".pay-form button{width:100%;min-height:44px;border:0;border-radius:12px;font-family:inherit;font-size:var(--t3);font-weight:600;cursor:pointer}",
        ".pay-form .primary{min-height:44px;font-size:var(--t3)}",
        ".pay-form .ghost{border:1px solid var(--line);color:var(--muted);font-weight:500}",
        ".pay-form .ghost:disabled{color:#5f708c}",
        ".item .hint{margin:8px 0 0;font-size:var(--t5)}",
        "",
    ]
)


def write(rel, content):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("wrote", rel.replace(os.sep, "/"), os.path.getsize(path), "bytes")


write(os.path.join("app", "commitments", "templates", "commitments.html"), DUE_PAGE)
write(os.path.join("app", "commitments", "templates", "_commitment_msg.html"), MSG_PART)
write(os.path.join("app", "static", "commitments.css"), CSS)
