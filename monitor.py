import os
import re
import requests
from playwright.sync_api import sync_playwright

EMAIL = os.environ.get("MK_EMAIL")
PASSWORD = os.environ.get("MK_PASSWORD")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")

LOGIN_URL = "https://www.meetcritique.com/login/"
DASHBOARD_URL = "https://www.meetcritique.com/dashboard/"

def notify(message):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={"Title": "MeetCritique Alert", "Priority": "urgent", "Tags": "rotating_light"}
    )

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1920,1080"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("1. Loading login page...")
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)

            login_tab = page.locator('.um-login-nav, button:has-text("Login"), a:has-text("Login")').first
            if login_tab.count() > 0 and login_tab.is_visible():
                try:
                    login_tab.click()
                    page.wait_for_timeout(500)
                except Exception:
                    pass

            print("2. Filling credentials...")
            user_input = page.locator('input[id^="user_login"]:visible, input[name^="user_login"]:visible, input[type="text"]:visible').first
            user_input.wait_for(state="visible", timeout=15000)
            user_input.fill(EMAIL)

            pass_input = page.locator('input[id^="user_password"]:visible, input[name^="user_password"]:visible, input[type="password"]:visible').first
            pass_input.wait_for(state="visible", timeout=10000)
            pass_input.fill(PASSWORD)

            print("3. Submitting...")
            submit_btn = page.locator('input[type="submit"][value*="Log"], button:has-text("Login"):visible, input[id="um-submit-btn"]:visible').first
            if submit_btn.count() > 0 and submit_btn.is_visible():
                submit_btn.click()
            else:
                pass_input.press("Enter")

            page.wait_for_timeout(5000)

            print("4. Opening dashboard...")
            page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            print("5. Parsing target counter...")
            # Targeted script: find the element containing 'meetcritiques' and 'available',
            # then find the closest large number inside that specific card.
            count = page.evaluate("""() => {
                // Find all leaf elements that mention 'available'
                const allElements = Array.from(document.querySelectorAll('*'));
                
                const label = allElements.find(el => {
                    const txt = el.innerText || "";
                    return txt.toLowerCase().includes("meetcritiques") && 
                           txt.toLowerCase().includes("available") &&
                           el.children.length <= 2;
                });

                if (!label) return null;

                // Move up to the containing card/box
                let card = label;
                while (card && card.parentElement && card.offsetHeight < 250 && card.offsetWidth < 400) {
                    card = card.parentElement;
                }

                // Look for the element displaying the big stat number inside this card
                const innerText = card ? card.innerText : label.innerText;
                console.log("Found card content:", innerText);
                
                // Match lines or words that are solely numbers
                const matches = innerText.match(/\\b\\d+\\b/g);
                return matches ? parseInt(matches[0], 10) : 0;
            }""")

            print(f"--> Extracted Count: {count} <--")

            if count is None:
                raise Exception("Unable to isolate the stat box.")

            if count > 0:
                print(f"Triggering notification for {count} critiques...")
                notify(f"MeetCritique Alert: {count} critique(s) available for review right now!")
            else:
                print("Count is 0. No notification sent.")

        except Exception as e:
            print(f"Error encountered: {e}")
            page.screenshot(path="error_state.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
