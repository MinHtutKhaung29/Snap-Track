import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

BASE = "\n".join(
    [
        "<!DOCTYPE html>",
        '<html lang="ja">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        '  <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">',
        '  <meta name="theme-color" content="#0f172a" media="(prefers-color-scheme: dark)">',
        "  <title>{% block title %}Snap &amp; Track{% endblock %}</title>",
        '  <link rel="stylesheet" href="/static/base.css">',
        '  <link rel="stylesheet" href="/static/chat.css">',
        '  <link rel="stylesheet" href="/static/receipts.css">',
        '  <link rel="stylesheet" href="/static/commitments.css">',
        "  {% block head %}{% endblock %}",
        "</head>",
        "<body>",
        '  <header class="hdr">',
        '    <h1 class="hdr-title">{% block heading %}Snap &amp; Track{% endblock %}</h1>',
        "    {% if user %}",
        '    <form method="post" action="/logout" class="signout">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <button type="submit">ログアウト</button>',
        "    </form>",
        "    {% endif %}",
        "  </header>",
        "  {% if user %}",
        '  <nav class="tabs">',
        '    <a href="/chat"{% if request.url.path == "/chat" %} aria-current="page"{% endif %}>チャット</a>',
        '    <a href="/receipts"{% if request.url.path.startswith("/receipts") %} aria-current="page"{% endif %}>レシート</a>',
        '    <a href="/commitments"{% if request.url.path.startswith("/commitments") %} aria-current="page"{% endif %}>支払い予定</a>',
        "  </nav>",
        "  {% endif %}",
        '  <main class="wrap">{% block content %}{% endblock %}</main>',
        '  <footer class="foot">{% block foot %}{% endblock %}</footer>',
        "</body>",
        "</html>",
        "",
    ]
)

HOME = "\n".join(
    [
        '{% extends "base.html" %}',
        "{% block title %}Snap &amp; Track — ホーム{% endblock %}",
        "{% block heading %}ホーム{% endblock %}",
        "{% block content %}",
        '<section class="card">',
        "  <h1>{{ user.name }} さん</h1>",
        '  <p class="lead">チャットに話しかけると、AIが支出を記録します。次のフェーズで入ります。</p>',
        '  <dl class="status">',
        "    <dt>DB</dt><dd>{{ health.version }}</dd>",
        "    <dt>テーブル</dt><dd>{{ health.tables }} / 8</dd>",
        "    <dt>モデル</dt><dd>{{ health.model }}</dd>",
        "  </dl>",
        '  <p class="hint">P1 動作確認用の画面です。</p>',
        "</section>",
        "{% endblock %}",
        "",
    ]
)

LOGIN = "\n".join(
    [
        '{% extends "base.html" %}',
        "{% block title %}ログイン — Snap &amp; Track{% endblock %}",
        "{% block heading %}ログイン{% endblock %}",
        "{% block content %}",
        '<section class="card">',
        '  {% if error %}<p class="err">{{ error }}</p>{% endif %}',
        '  <form method="post" action="/login" class="form">',
        '    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '    <label>メールアドレス<input type="email" name="email" value="{{ email }}" required autocomplete="email"></label>',
        '    <label>パスワード<input type="password" name="password" required autocomplete="current-password"></label>',
        '    <button type="submit">ログイン</button>',
        "  </form>",
        '  <p class="hint">アカウントが無い場合は <a href="/register">新規登録</a></p>',
        "</section>",
        "{% endblock %}",
        "",
    ]
)

REGISTER = "\n".join(
    [
        '{% extends "base.html" %}',
        "{% block title %}新規登録 — Snap &amp; Track{% endblock %}",
        "{% block heading %}新規登録{% endblock %}",
        "{% block content %}",
        '<section class="card">',
        '  {% if error %}<p class="err">{{ error }}</p>{% endif %}',
        '  <form method="post" action="/register" class="form">',
        '    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '    <label>名前<input type="text" name="name" value="{{ name }}" placeholder="山田 太郎" required autocomplete="name"></label>',
        '    <label>メールアドレス<input type="email" name="email" value="{{ email }}" placeholder="example@mail.com" required autocomplete="email"></label>',
        '    <label>パスワード<input type="password" name="password" placeholder="8文字以上" required autocomplete="new-password"></label>',
        '    <p class="field-hint">8文字以上の半角英数字</p>',
        '    <label>パスワード（確認）<input type="password" name="password_confirm" placeholder="もう一度入力" required autocomplete="new-password"></label>',
        '    <button type="submit">登録する</button>',
        "  </form>",
        '  <p class="hint">既にアカウントがある場合は <a href="/login">ログイン</a></p>',
        "</section>",
        "{% endblock %}",
        "",
    ]
)

CSS_BASE = "\n".join(
    [
        ":root{--bg:#ffffff;--surface:#f4f5f7;--field:#ffffff;--fg:#0f172a;--muted:#5b6472;--line:#e3e7ee;--line-strong:#858c96;--accent:#2563eb;--accent-fg:#1d4ed8;--accent-on:#ffffff;--accent-press:#1d4ed8;--ok:#047857;--ng:#b91c1c;--warn:#b45309;--overdue:#b45309;--err-bg:#fdecec;--err-fg:#b91c1c;--note-bg:#e8f6ee;--note-fg:#047857;--pick-bg:#dbeafe;--pick-fg:#1d4ed8;--pick-dot:#2563eb;--off:#6b7480;--t1:34px;--t2:20px;--t3:15px;--t4:13px;--t5:12px}",
        "@media (prefers-color-scheme:dark){:root{--bg:#0f172a;--surface:#0a1220;--field:#141d33;--fg:#e6edf7;--muted:#94a3b8;--line:#243049;--line-strong:#5f6f92;--accent:#2f6fe8;--accent-fg:#60a5fa;--accent-on:#ffffff;--accent-press:#2563eb;--ok:#34d399;--ng:#f87171;--warn:#fbbf24;--overdue:#9a5b12;--err-bg:#3b1d24;--err-fg:#fca5a5;--note-bg:#12291d;--note-fg:#86efac;--pick-bg:#172554;--pick-fg:#dbeafe;--pick-dot:#60a5fa;--off:#5f708c}}",
        "*{box-sizing:border-box}",
        "html{-webkit-text-size-adjust:100%;overscroll-behavior-y:none}",
        'body{margin:0;background:var(--bg);color:var(--fg);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP","Yu Gothic",sans-serif;font-size:var(--t3);line-height:1.7;-webkit-font-smoothing:antialiased;overscroll-behavior-y:none;touch-action:manipulation}',
        ".hdr{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:8px;height:56px;padding:0 16px;background:var(--bg);border-bottom:1px solid var(--line)}",
        ".hdr-title{flex:1 1 auto;min-width:0;margin:0;font-size:var(--t3);font-weight:600;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
        ".signout{flex:0 0 auto;display:flex;margin:0 0 0 auto}",
        ".signout button{min-width:44px;min-height:44px;padding:0 4px;border:0;border-radius:12px;background:none;color:var(--muted);font-family:inherit;font-size:var(--t4);white-space:nowrap;cursor:pointer}",
        ".signout button:active{color:var(--fg)}",
        ".tabs{position:sticky;top:56px;z-index:29;display:flex;gap:16px;padding:0 16px;overflow-x:auto;overscroll-behavior-x:contain;background:var(--bg);border-bottom:1px solid var(--line);scrollbar-width:none}",
        ".tabs::-webkit-scrollbar{display:none}",
        ".tabs a{display:flex;align-items:center;min-height:44px;flex:0 0 auto;margin-bottom:-1px;border-bottom:2px solid transparent;color:var(--muted);font-size:var(--t4);text-decoration:none;white-space:nowrap}",
        ".tabs a[aria-current=page]{color:var(--fg);border-bottom-color:var(--accent)}",
        ".wrap{max-width:640px;margin:0 auto;padding:16px}",
        ".foot{max-width:640px;margin:0 auto;padding:8px 16px calc(16px + env(safe-area-inset-bottom));color:var(--muted);font-size:var(--t5)}",
        ".card{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px}",
        "h1{margin:0 0 8px;font-size:var(--t2);font-weight:600}",
        ".lead{margin:0 0 16px;color:var(--muted)}",
        ".status{display:grid;grid-template-columns:auto 1fr;gap:8px 16px;margin:0 0 16px;font-size:var(--t4)}",
        ".status dt{color:var(--muted)}",
        ".status dd{margin:0;font-variant-numeric:tabular-nums}",
        ".ok{color:var(--ok)}",
        ".ng{color:var(--ng)}",
        ".muted{color:var(--muted)}",
        ".hint{margin:12px 0 0;font-size:var(--t4);color:var(--muted)}",
        ".hint a{color:var(--accent-fg)}",
        ".err{margin:0 0 16px;padding:8px 12px;border-radius:12px;background:var(--err-bg);color:var(--err-fg);font-size:var(--t4)}",
        ".note{margin:0 0 16px;padding:8px 12px;border-radius:12px;background:var(--note-bg);color:var(--note-fg);font-size:var(--t4)}",
        ".form{display:grid;gap:16px}",
        ".form label{display:grid;gap:8px;font-size:var(--t4);color:var(--muted)}",
        ".form input,.form select{min-height:48px;padding:0 12px;border-radius:12px;border:1px solid var(--line-strong);background:var(--field);color:var(--fg);font-family:inherit;font-size:16px}",
        ".form input:focus,.form select:focus{outline:2px solid var(--accent);outline-offset:1px}",
        ".form > button{min-height:52px;border:0;border-radius:12px;background:var(--accent);color:var(--accent-on);font-family:inherit;font-size:16px;font-weight:600;cursor:pointer}",
        ".field-hint{margin:-8px 0 0;font-size:var(--t5);color:var(--muted)}",
        ".primary{display:inline-flex;align-items:center;justify-content:center;min-height:52px;padding:0 16px;border:0;border-radius:12px;background:var(--accent);color:var(--accent-on);font-family:inherit;font-size:16px;font-weight:600;text-decoration:none;cursor:pointer}",
        ".primary:active{background:var(--accent-press)}",
        ".btn-link{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 16px;border-radius:12px;font-family:inherit;font-size:var(--t3);font-weight:600;text-decoration:none;cursor:pointer}",
        ".secondary{background:var(--surface);border:1px solid var(--line-strong);color:var(--fg)}",
        ".ghost{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 12px;border:0;border-radius:12px;background:none;color:var(--muted);font-family:inherit;font-size:var(--t4);font-weight:500;cursor:pointer}",
        ".ghost:active{color:var(--fg)}",
        ".sheet{border:1px solid var(--line);border-radius:16px;overflow:hidden;background:var(--surface)}",
        ".row{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:44px;padding:8px 16px;border-top:1px solid var(--line)}",
        ".row:first-child{border-top:0}",
        ".row-k{flex:0 0 auto;font-size:var(--t4);color:var(--muted)}",
        ".row-v{min-width:0;font-size:var(--t3);text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}",
        ".empty{display:grid;gap:12px;padding:24px 16px;background:var(--surface);border:1px solid var(--line);border-radius:16px;text-align:center}",
        ".empty p{margin:0}",
        ".empty-title{margin:0;font-size:var(--t2);font-weight:600;line-height:1.4}",
        ".empty .hint{margin:0}",
        ".empty .primary{width:100%}",
        "@media (max-width:420px){.wrap{padding:12px 16px}}",
        "",
    ]
)


def write(rel, content):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("wrote", rel.replace(os.sep, "/"), os.path.getsize(path), "bytes")


write(os.path.join("app", "shared", "templates", "base.html"), BASE)
write(os.path.join("app", "shared", "templates", "home.html"), HOME)
write(os.path.join("app", "login", "templates", "login.html"), LOGIN)
write(os.path.join("app", "login", "templates", "register.html"), REGISTER)
write(os.path.join("app", "static", "base.css"), CSS_BASE)
