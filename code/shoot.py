"""Drive the running interface in a browser and photograph it.

WHY THIS EXISTS.  Two reasons, and the second is the important one.

1.  Chapter 4 needs screenshots of the interface, and taking them by hand is a
    step that has to be repeated exactly every time the interface changes.
    Here the sequence of clicks is code, so a figure can be regenerated after a
    change instead of being retaken and quietly going stale.

2.  It closes a loop that was otherwise open.  Every automated check in
    verify_prototype.py runs against Streamlit's AppTest, which executes the
    script and inspects the resulting element tree -- it never renders.  A
    layout that overflows, a colour with no contrast, a control that lands off
    the bottom of a card: none of that is visible to AppTest, and none of it
    was visible to me.  The visual defects in this project were all found by
    the user, at the cost of a round trip each.  This lets them be found here.

It starts its own server and stops it afterwards:

    python code/shoot.py

That is not a convenience.  Streamlit re-executes the main script on every
rerun but keeps imported modules in sys.modules, so a server started before an
edit to uistyle.py goes on serving the old stylesheet.  A run of this script
against a long-lived server therefore photographs whatever was loaded at start
time, and reports "no browser errors" while doing it -- which is exactly how a
round of CSS edits got tested here without ever having been loaded.  Owning the
process removes the failure mode instead of documenting it.

Pass an existing URL to skip that, when iterating against a server you are
already watching:  APP_URL=http://localhost:8501 python code/shoot.py
"""

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOTS = os.path.join(ROOT, "figures", "screenshots")
PORT = int(os.environ.get("APP_PORT", "8502"))
OWN_URL = os.environ.get("APP_URL")
URL = OWN_URL or f"http://localhost:{PORT}"

# A wide viewport: the week is seven columns, and a narrow window collapses it
# into a single column, which is not the layout Chapter 4 is describing.
VIEWPORT = {"width": 1680, "height": 1050}


def settled(page, timeout=180):
    """Wait until Streamlit has finished running the script.

    The corpus load alone takes tens of seconds on a cold start, so a fixed
    sleep is either too short to be reliable or too long to iterate with.  This
    watches for the status widget to disappear instead.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        running = page.locator('[data-testid="stStatusWidget"]').count()
        spinner = page.locator('[data-testid="stSpinner"]').count()
        if not running and not spinner:
            page.wait_for_timeout(700)
            if (not page.locator('[data-testid="stStatusWidget"]').count()
                    and not page.locator('[data-testid="stSpinner"]').count()):
                return True
        page.wait_for_timeout(500)
    return False


def serve(timeout=240):
    """Start a fresh Streamlit process and wait for it to answer."""
    log = open(os.path.join(HERE, "outputs", "shoot_server.log"), "w")
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run",
         os.path.join(HERE, "app.py"),
         "--server.port", str(PORT), "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    health = f"http://localhost:{PORT}/_stcore/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            log.close()
            raise RuntimeError("the server exited during start-up; see "
                               "code/outputs/shoot_server.log")
        try:
            with urllib.request.urlopen(health, timeout=2) as r:
                if r.status == 200:
                    return proc, log
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    proc.terminate()
    log.close()
    raise RuntimeError("the server did not come up within the timeout")


def to_top(page, text):
    """Put a heading at the top of the viewport, not merely inside it.

    scroll_into_view_if_needed stops as soon as the element is visible, which
    for a heading means it lands at the bottom edge with the section it labels
    still off screen -- exactly the wrong framing for a figure.
    """
    target = page.get_by_text(text, exact=False).first
    if not target.count():
        return False
    target.evaluate("el => el.scrollIntoView({block: 'start'})")
    page.wait_for_timeout(800)
    return True


def shoot(page, name, full=False, clip=None):
    os.makedirs(SHOTS, exist_ok=True)
    path = os.path.join(SHOTS, f"{name}.png")
    page.screenshot(path=path, full_page=full, clip=clip)
    print(f"  {name}.png  ({os.path.getsize(path) / 1000:.0f} kB)")
    return path


def shoot_region(page, name, selector, height=None):
    """Photograph one region rather than the whole viewport.

    Every figure in Chapter 4 is reproduced at six inches on the page. A
    full-width capture spends a fifth of that width on the sidebar, which most
    of the figures are not about, and shrinks the text they are about to the
    edge of legibility in print. Clipping to the element under discussion buys
    back that width.
    """
    box = page.locator(selector).first.bounding_box()
    if not box:
        print(f"  (no box for {name}: {selector})")
        return None
    clip = {"x": box["x"], "y": box["y"], "width": box["width"],
            "height": min(box["height"], height or box["height"])}
    return shoot(page, name, clip=clip)


MAIN = '[data-testid="stMain"]'
SIDEBAR = '[data-testid="stSidebar"]'


def capture():
    from playwright.sync_api import sync_playwright

    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)
        page.on("console", lambda m: errors.append(m.text)
                if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))

        print(f"opening {URL}")
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        if not settled(page):
            print("  the app did not settle within the timeout")
            browser.close()
            return 1

        print("photographing")
        shoot(page, "01_form_and_week")

        for name, anchor in (("02_day_by_day", "Day by day"),
                             ("03_nutrition", "How this week feeds you"),
                             ("05_leftovers", "Shopping that carries over")):
            if to_top(page, anchor):
                shoot(page, name)
                if name in ("02_day_by_day", "03_nutrition"):
                    shoot_region(page, name + "_crop", MAIN, height=980)
            else:
                print(f"  (no anchor for {name}: {anchor!r})")

        # A recipe detail dialog, opened the way a user opens one: the card's
        # popover, then the dish inside it.
        to_top(page, "Day by day")
        opener = page.get_by_role("button", name="Open the recipe").first
        if opener.count():
            opener.click()
            page.wait_for_timeout(1500)
            settled(page)
            page.wait_for_timeout(3000)   # the generated note
            shoot(page, "04_recipe_detail")
            page.keyboard.press("Escape")
            page.wait_for_timeout(600)
        else:
            print("  (no 'Open the recipe' control found)")

        # What an excluded term actually caught.  A term is matched by its
        # stem against the start of a word, so "oats" also removes oatmeal and
        # oat bran; the interface names them rather than applying the rule
        # silently, and that is what this photographs.
        avoid = page.get_by_placeholder("olives, coriander")
        if avoid.count():
            avoid.click()
            avoid.fill("oats")
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            settled(page)
            caught = page.get_by_text("removes", exact=False)
            if caught.count():
                shoot(page, "08_exclusion_feedback")
                # A full-height sidebar is 600 by 2100, which at any usable
                # width is taller than the page it has to sit on. Clip to the
                # restriction controls and the feedback beneath them.
                side = page.locator(SIDEBAR).first.bounding_box()
                field = avoid.bounding_box()
                if side and field:
                    shoot(page, "08_exclusion_feedback_crop",
                          clip={"x": side["x"], "width": side["width"],
                                "y": max(field["y"] - 300, 0), "height": 620})
            else:
                errors.append("the exclusion feedback did not render")
            avoid.fill("")
            page.keyboard.press("Enter")
            page.wait_for_timeout(1500)
            settled(page)

        # The safety state: a restriction changed, the plan not yet rebuilt.
        # Photographed because it is the fix for a defect a user reported, and
        # a claim that the interface locks is worth more with the lock visible.
        allergy = page.locator('[data-testid="stSidebar"] '
                               '[data-testid="stMultiSelect"] input').first
        if allergy.count():
            allergy.click()
            page.wait_for_timeout(600)
            page.keyboard.type("Peanut")
            page.wait_for_timeout(900)
            # Click the option itself.  Typing and pressing Enter left the
            # combobox open with nothing selected, so the page went on showing
            # an unlocked plan and the screenshot proved the opposite of what
            # it was taken to prove.
            option = page.locator('[role="option"]').first
            if option.count():
                option.click()
            else:
                page.keyboard.press("Enter")
            page.wait_for_timeout(1800)
            settled(page)

            # Assert the state before photographing it.
            banner = page.get_by_text("Locked while your changes are "
                                      "pending", exact=False)
            if not banner.count():
                errors.append("the restriction-change banner did not appear; "
                              "06/07 would misrepresent the interface")
            else:
                # Dismiss the still-open dropdown before photographing, and
                # frame on the title so the red banner is in shot -- the banner
                # is the point of the figure.
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)
                to_top(page, "Your week")
                shoot(page, "06_restriction_changed")
                shoot_region(page, "06_restriction_changed_crop", MAIN,
                             height=560)
                to_top(page, "Day by day")
                shoot(page, "07_cards_locked")
        else:
            print("  (no allergy control found)")

        browser.close()

    if errors:
        print(f"\n{len(errors)} browser error(s):")
        for e in errors[:12]:
            print(f"  {e[:200]}")
        return 1
    print("\nno browser errors")
    return 0


def main():
    if OWN_URL:
        print(f"using the server already at {OWN_URL}")
        return capture()
    print(f"starting a server on port {PORT}")
    proc, log = serve()
    try:
        return capture()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()
        print("server stopped")


if __name__ == "__main__":
    sys.exit(main())
