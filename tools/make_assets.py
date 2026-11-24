import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

BASE = "\n".join(
    [
        "<!DOCTYPE html>",
        '<html lang="ja">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        '  <meta name="theme-color" content="#0f172a">',
        "  <title>{% block title %}Snap &amp; Track{% endblock %}</title>",
        '  <link rel="stylesheet" href="/static/base.css">',
        "</head>",
        "<body>",
        '  <header class="top">',
        '    <a class="brand" href="/">Snap &amp; Track</a>',
        '    <nav class="nav">{% block nav %}{% endblock %}</nav>',
        "  </header>",
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
        "{% block nav %}",
        '  <span class="who">{{ user.name }}',
        '    <form method="post" action="/logout">',
        '      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '      <button type="submit" class="linkbtn">ログアウト</button>',
        "    </form>",
        "  </span>",
        "{% endblock %}",
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
        "{% block content %}",
        '<section class="card">',
        "  <h1>ログイン</h1>",
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
        "{% block content %}",
        '<section class="card">',
        "  <h1>新規登録</h1>",
        '  {% if error %}<p class="err">{{ error }}</p>{% endif %}',
        '  <form method="post" action="/register" class="form">',
        '    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '    <label>名前<input type="text" name="name" value="{{ name }}" required autocomplete="name"></label>',
        '    <label>メールアドレス<input type="email" name="email" value="{{ email }}" required autocomplete="email"></label>',
        '    <label>パスワード<input type="password" name="password" required autocomplete="new-password"></label>',
        '    <label>パスワード（確認）<input type="password" name="password_confirm" required autocomplete="new-password"></label>',
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
        ":root{--bg:#0f172a;--fg:#e6edf7;--muted:#94a3b8;--card:#182338;--ok:#34d399;--ng:#f87171;--line:#243049}",
        "*{box-sizing:border-box}",
        'body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,"Segoe UI",system-ui,"Hiragino Sans","Yu Gothic",sans-serif;-webkit-text-size-adjust:100%}',
        ".top{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(15,23,42,.92);backdrop-filter:blur(8px)}",
        ".brand{color:var(--fg);text-decoration:none;font-weight:700}",
        ".nav{display:flex;align-items:center;gap:12px}",
        ".nav a{color:var(--muted);text-decoration:none;font-size:14px}",
        ".wrap{max-width:640px;margin:0 auto;padding:18px}",
        ".card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px}",
        "h1{margin:0 0 6px;font-size:22px}",
        ".lead{margin:0 0 18px;color:var(--muted)}",
        ".status{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;margin:0 0 16px;font-size:14px}",
        ".status dt{color:var(--muted)}",
        ".status dd{margin:0;font-variant-numeric:tabular-nums}",
        ".ok{color:var(--ok)}",
        ".ng{color:var(--ng)}",
        ".hint{margin:12px 0 0;font-size:13px;color:var(--muted)}",
        ".foot{max-width:640px;margin:0 auto;padding:8px 18px 28px;color:var(--muted);font-size:12px}",
        ".form{display:grid;gap:12px}",
        ".form label{display:grid;gap:6px;font-size:14px;color:var(--muted)}",
        ".form input{padding:12px 14px;border-radius:10px;border:1px solid var(--line);background:#0d1526;color:var(--fg);font-size:16px}",
        ".form input:focus{outline:2px solid #3b82f6;outline-offset:1px}",
        ".form button{margin-top:6px;padding:13px 16px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-size:16px;font-weight:600}",
        ".err{margin:0 0 14px;padding:10px 12px;border-radius:10px;background:#3b1d24;color:#fca5a5;font-size:14px}",
        ".hint a{color:#60a5fa}",
        ".who{display:flex;align-items:center;gap:10px;font-size:14px;color:var(--muted)}",
        ".who form{margin:0}",
        ".linkbtn{background:none;border:0;color:#60a5fa;font:inherit;padding:0;cursor:pointer}",
        "@media (max-width:420px){.wrap{padding:14px}.card{padding:16px}}",
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
