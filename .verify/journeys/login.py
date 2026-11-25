import _common as v


def flow(page):
    address = v.email("login")
    v.register(page, address)
    v.record("registered and reached chat", v.user_id(address) is not None)

    page.locator('form[action="/logout"] button').first.click()
    page.wait_for_url("**/login", timeout=60000)
    v.shot(page, "01-login-form.png")

    page.fill('input[name="email"]', address)
    page.fill('input[name="password"]', "verify-password-1")
    page.click('.form button[type="submit"]')
    page.wait_for_url("**/chat", timeout=60000)
    v.record("logout then login returns to chat", "/chat" in page.url, page.url)
    v.shot(page, "02-back-on-chat.png")


if __name__ == "__main__":
    v.main(flow)
