import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

RECEIPTS = "\n".join(
    [
        '{% extends "base.html" %}',
        "{% block title %}レシート — Snap &amp; Track{% endblock %}",
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
        "  {% if not card %}",
        '  <div class="empty">',
        "    <p>未確認のレシートはありません。</p>",
        '    <p class="hint">チャットの📷から追加できます。</p>',
        '    <a class="primary btn-link" href="/chat">チャットへ</a>',
        "  </div>",
        "  {% else %}",
        '  <div class="queue-head"><span>読み取り結果</span><span class="count">{{ index }} / {{ total }}</span></div>',
        '  <div class="swipe" id="card">',
        '    <img class="shot" src="/receipts/{{ card.receipt_id }}/image" alt="レシート">',
        "    {% if card.read_status == 'failed' or not card.data.amount %}",
        '    <p class="warn">うまく読み取れませんでした。「直す」から入力してください。</p>',
        "    {% endif %}",
        '    <div class="label">合計{% if card.edited %}・修正中{% endif %}</div>',
        "    <div class=\"amt\">{% if card.display_amount %}¥{{ \"{:,}\".format(card.display_amount) }}{% else %}—{% endif %}</div>",
        '    <div class="meta">',
        '      <span class="pill">{{ override.shop or card.data.shop or "不明" }}</span>',
        '      <span class="sub">{{ card.date_label or "日付なし" }}</span>',
        "    </div>",
        '    <div class="meta"><span class="pill">{{ card.display_category or card.category_name }}</span></div>',
        "  </div>",
        '  <div class="actions">',
        '    <form method="post" action="/receipts/{{ card.receipt_id }}/discard" class="discard-form">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <button type="submit" class="danger" aria-label="捨てる">✕</button>',
        "    </form>",
        '    <button type="button" class="ghost act" id="fix-btn">← 直す</button>',
        '    <form method="post" action="/receipts/{{ card.receipt_id }}/save" id="save-form" class="save-form">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <button type="submit" class="primary act">保存 →</button>',
        "    </form>",
        "  </div>",
        '  <p class="swipe-hint">右へスワイプで保存 ・ 左へスワイプで直す</p>',
        '  <details class="edit queue-edit" id="fix"{% if error_message %} open{% endif %}>',
        "    <summary></summary>",
        '    <form method="post" action="/receipts/{{ card.receipt_id }}/save" class="form tight">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <label>金額<input type="number" name="amount" value="{{ override.amount or card.data.amount or "" }}" min="1" inputmode="numeric" required></label>',
        '      <label>日付<input type="date" name="date" value="{{ override.date or card.data.date or today }}"></label>',
        '      <label>店・内容<input type="text" name="shop" value="{{ override.shop or card.data.shop or "" }}" maxlength="120"></label>',
        '      <label>分類<select name="category_code">',
        '        {% set chosen = override.category_code or card.data.category_code %}',
        '        {% for c in categories %}<option value="{{ c.code }}" {% if c.code == chosen %}selected{% endif %}>{{ c.category_name }}</option>{% endfor %}',
        "      </select></label>",
        '      <button type="submit" class="primary">この内容で保存</button>',
        "    </form>",
        "  </details>",
        "  {% endif %}",
        "</section>",
        "{% endblock %}",
        "{% block foot %}",
        "<script>",
        "var card=document.getElementById('card');",
        "if(card){var sx=0,dx=0,active=false;",
        "card.addEventListener('pointerdown',function(e){if(e.target.closest('button,a,details,summary,form,summary'))return;active=true;sx=e.clientX;dx=0;card.setPointerCapture(e.pointerId);card.classList.add('drag');});",
        "card.addEventListener('pointermove',function(e){if(!active)return;dx=e.clientX-sx;card.style.transform='translateX('+dx+'px) rotate('+(dx/45)+'deg)';card.classList.toggle('ok',dx>90);card.classList.toggle('no',dx<-90);});",
        "card.addEventListener('pointerup',function(){if(!active)return;active=false;card.classList.remove('drag');card.style.transform='';var go=dx;dx=0;card.classList.remove('ok','no');if(go>90){document.getElementById('save-form').requestSubmit();}else if(go<-90){var f=document.getElementById('fix');f.open=true;f.scrollIntoView({block:'center',behavior:'smooth'});}});",
        "card.addEventListener('pointercancel',function(){active=false;card.style.transform='';});",
        "var fb=document.getElementById('fix-btn');if(fb){fb.addEventListener('click',function(){var f=document.getElementById('fix');f.open=true;f.scrollIntoView({block:'center',behavior:'smooth'});});}}",
        "</script>",
        "{% endblock %}",
        "",
    ]
)

CSS = "\n".join(
    [
        ".queue{max-width:520px;margin:0 auto;padding-bottom:40px}",
        ".queue-head{display:flex;justify-content:space-between;align-items:center;font-size:13px;color:var(--muted);margin-bottom:10px}",
        ".count{font-variant-numeric:tabular-nums}",
        ".swipe{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:16px;touch-action:pan-y;user-select:none;transition:transform .18s ease,border-color .18s ease}",
        ".swipe.drag{transition:none}",
        ".swipe.ok{border-color:#15803d}",
        ".swipe.no{border-color:#b45309}",
        ".shot{width:100%;max-height:320px;object-fit:contain;background:#0d1526;border-radius:12px;margin-bottom:14px}",
        ".actions{display:flex;gap:10px;margin-top:14px;align-items:stretch}",
        ".actions form{margin:0}",
        ".actions .discard-form{flex:0 0 56px}",
        ".actions .save-form{flex:1}",
        ".actions .act{width:100%;min-height:52px;border:0;border-radius:12px;font-weight:700;font-size:15px;white-space:nowrap}",
        ".actions>.act{flex:1;width:auto}",
        ".actions .ghost{background:transparent;border:1px solid var(--line);color:var(--fg)}",
        ".danger{width:100%;min-width:56px;min-height:52px;border-radius:12px;border:1px solid var(--line);background:transparent;color:#f87171;font-size:18px}",
        ".queue-edit summary{display:none}",
        ".swipe-hint{margin:12px 0 0;font-size:12px;color:var(--muted);text-align:center}",
        ".empty{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:28px 20px;text-align:center}",
        ".btn-link{display:inline-block;margin-top:14px;padding:12px 20px;border-radius:12px;text-decoration:none;font-weight:700}",
        ".queue .label{margin-top:4px}",
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

css_path = os.path.join(ROOT, "app", "static", "base.css")
with open(css_path, encoding="utf-8") as f:
    css = f.read()
marker = ".queue{"
if marker in css:
    css = css[: css.index(marker)] + CSS
    with open(css_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(css)
    print("updated receipt css")
else:
    with open(css_path, "a", encoding="utf-8", newline="\n") as f:
        f.write(CSS)
    print("appended receipt css")
