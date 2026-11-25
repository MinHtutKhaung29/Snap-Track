# Login

Register, sign in, sign out. Built as a scaffold so the UI half can be replaced without touching feature code.

## Sub-features

- Register: 名前 / メールアドレス / パスワード（8文字以上）/ 確認
- Sign in with email and password
- Sign out from the header
- Rejections that explain themselves: wrong password, duplicate email, short password, mismatched confirmation, bad CSRF

## How to get to it (user POV)

`/login` and `/register`. Any protected page redirects to `/login` when there is no session.

## Driving it with Playwright

```python
page.goto(BASE + "/register")
page.fill('input[name="name"]', "検証 太郎")
page.fill('input[name="email"]', email)
page.fill('input[name="password"]', "verify-password-1")
page.fill('input[name="password_confirm"]', "verify-password-1")
page.click('.form button[type="submit"]')
page.wait_for_url("**/chat", timeout=60000)
```

Every form carries `input[name="csrf_token"]`; a POST without it must return 403.

## Gotchas

- `/` is a redirect, not a page: 303 to `/chat` when signed in, 303 to `/login` when not. Asserting 200 on `/` fails by design.
- Passwords are `scrypt` with a per-user salt; a row whose `password_hash` does not start with `scrypt$` is a defect, not a preference.
- The session cookie must be `httponly` and `samesite=lax`; check the `set-cookie` header, not the cookie jar.
- Registration logs the user in immediately; a test that then expects to be on `/login` is asserting the wrong flow.
- 1.4 theories worth keeping: the login screens are another owner's deliverable. Files under `app/login/templates/` take precedence over the built-in ones, so replacing them needs no code change.
