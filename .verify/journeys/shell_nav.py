import _common as v

OVERFLOW = "document.documentElement.scrollWidth - document.documentElement.clientWidth"

STATE = (
    "(() => ({"
    " open: document.body.dataset.drawer,"
    " expanded: document.querySelector('[data-drawer-toggle]').getAttribute('aria-expanded'),"
    " transform: getComputedStyle(document.querySelector('.side')).transform,"
    " inert: document.querySelector('.side').hasAttribute('inert'),"
    " scrim: getComputedStyle(document.querySelector('.scrim')).opacity,"
    " focused: document.activeElement.hasAttribute('data-drawer-toggle')"
    "}))()"
)


def drawer_state(page):
    return page.evaluate(STATE)


def flow(page):
    v.register(page, v.email("shell"))
    page.goto(v.BASE + "/chat", wait_until="networkidle")
    page.wait_for_timeout(300)

    state = drawer_state(page)
    v.record("phone drawer starts closed", state["open"] == "closed" and state["expanded"] == "false", state)
    v.record("closed drawer is off-screen", "-" in state["transform"] or state["transform"] == "none", state["transform"])
    v.record("closed drawer is not focusable", state["inert"] is True, state)
    v.record("the menu button is shown on a phone", page.locator("[data-drawer-toggle]").is_visible())
    v.record("the old tab strip is gone", page.locator(".tabs").count() == 0)
    v.record("nothing overflows sideways on a phone", page.evaluate(OVERFLOW) <= 0, page.evaluate(OVERFLOW))
    v.shot(page, "01-phone-closed.png")

    page.locator("[data-drawer-toggle]").click()
    page.wait_for_timeout(400)
    state = drawer_state(page)
    v.record("tapping the menu opens the drawer", state["open"] == "open" and state["expanded"] == "true", state)
    v.record("the opened drawer is on-screen", state["transform"] == "none" or state["transform"].endswith(", 0)"), state["transform"])
    v.record("the page behind is dimmed", float(state["scrim"]) > 0.3, state["scrim"])
    v.record("the opened drawer is focusable", state["inert"] is False, state)
    v.record("チャット is marked as the current page", page.locator('.nav a[aria-current="page"]').inner_text().strip() == "チャット")
    v.record("the drawer holds all three destinations", page.locator(".nav a").count() == 3)
    v.shot(page, "02-phone-drawer-open.png")

    page.emulate_media(color_scheme="dark")
    page.wait_for_timeout(200)
    v.shot(page, "03-phone-drawer-dark.png")
    page.emulate_media(color_scheme="light")

    page.keyboard.press("Escape")
    page.wait_for_timeout(350)
    state = drawer_state(page)
    v.record("Escape closes the drawer", state["open"] == "closed" and state["expanded"] == "false", state)
    v.record("Escape returns focus to the menu button", state["focused"] is True, state)

    page.locator("[data-drawer-toggle]").click()
    page.wait_for_timeout(350)
    page.locator(".scrim").click(position={"x": 380, "y": 400})
    page.wait_for_timeout(350)
    v.record("tapping outside closes the drawer", drawer_state(page)["open"] == "closed")

    page.locator("[data-drawer-toggle]").click()
    page.wait_for_timeout(350)
    page.locator(".nav a", has_text="写真").click()
    page.wait_for_load_state("networkidle")
    v.record("a destination navigates", page.url.endswith("/receipts"), page.url)
    v.record("the current item follows the page", page.locator('.nav a[aria-current="page"]').inner_text().strip() == "写真")
    v.record("the drawer is closed after navigating", page.evaluate("document.body.dataset.drawer") == "closed")

    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(v.BASE + "/chat", wait_until="networkidle")
    page.wait_for_timeout(400)
    side = page.locator(".side").bounding_box()
    v.record("desktop shows a persistent sidebar", side is not None and 220 <= side["width"] <= 300, side)
    v.record("the desktop sidebar sits at the left edge", side is not None and side["x"] <= 1, side)
    v.record("the hamburger is hidden on desktop", page.locator("[data-drawer-toggle]").is_hidden())
    v.record("the sidebar is not inert on desktop", page.evaluate("document.querySelector('.side').hasAttribute('inert')") is False)
    v.record("nothing overflows sideways on desktop", page.evaluate(OVERFLOW) <= 0, page.evaluate(OVERFLOW))
    v.record("the composer clears the sidebar", page.locator(".composer").bounding_box()["x"] >= 240)
    v.shot(page, "04-desktop-chat.png")

    page.emulate_media(color_scheme="dark")
    page.wait_for_timeout(200)
    v.shot(page, "05-desktop-chat-dark.png")
    page.emulate_media(color_scheme="light")
    page.goto(v.BASE + "/receipts", wait_until="networkidle")
    page.wait_for_timeout(300)
    v.shot(page, "06-desktop-receipts.png")


if __name__ == "__main__":
    v.main(flow)
