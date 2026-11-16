import re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")

    page = None
    for pg in browser.contexts[0].pages:
        if "flexstudent.nu.edu.pk" in pg.url:
            page = pg
            break

    if page is None:
        print("No FLEX window found.")
    elif page.locator("input[type=password]:visible").count() == 0:
        print("Already logged in. Nothing to do.")
    else:
        print("Login page found. Waiting for the page to fill in and the check to finish...")
        page.wait_for_timeout(12000)
        button = page.get_by_role("button", name=re.compile("Sign In", re.I))
        if button.count() > 0:
            button.first.click()
            page.wait_for_timeout(6000)
            if page.locator("input[type=password]:visible").count() == 0:
                print("Signed in.")
            else:
                print("Still on the login page. You will need to log in by hand.")
        else:
            print("Could not find the Sign In button.")