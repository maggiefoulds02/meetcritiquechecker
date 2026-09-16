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

            print("2. Filling visible credentials...")
            user_input = page.locator('input[id^="user_login"]:visible, input[name^="user_login"]:visible, input[type="text"]:visible').first
            user_input.wait_for(state="visible", timeout=15000)
            user_input.fill(EMAIL)

            pass_input = page.locator('input[id^="user_password"]:visible, input[name^="user_password"]:visible, input[type="password"]:visible').first
            pass_input.wait_for(state="visible", timeout=10000)
            pass_input.fill(PASSWORD)

            print("3. Submitting login...")
            submit_btn = page.locator('input[type="submit"][value*="Log"], button:has-text("Login"):visible, input[id="um-submit-btn"]:visible').first
            if submit_btn.count() > 0 and submit_btn.is_visible():
                submit_btn.click()
            else:
                pass_input.press("Enter")

            page.wait_for_timeout(5000)

            print("4. Navigating to dashboard...")
            page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            print("5. Parsing critique count...")
            # Use JavaScript directly in the browser to scan elements for "available"
            card_data = page.evaluate("""() => {
                const elements = Array.from(document.querySelectorAll('div, p, span, h1, h2, h3, h4'));
                const match = elements.find(el => {
                    const text = el.innerText || "";
                    return text.toLowerCase().includes("available") && text.toLowerCase().includes("meetcritique");
                });
                return match ? match.innerText : null;
            }""")

            print(f"Extracted card text: {repr(card_data)}")

            if not card_data:
                # Fallback: inspect the 4 top header boxes directly
                page.screenshot(path="dashboard_fallback.png")
                raise Exception("Could not find the 'meetcritiques available' card on the page.")

            # Grab the digits from the card text
            numbers = re.findall(r'\d+', card_data)
            count = int(numbers[-1]) if numbers else 0
            print(f"--> SUCCESS! Current available critiques: {count} <--")

            if count > 0:
                notify(f"MeetCritique Alert: {count} critique(s) available for review right now!")

        except Exception as e:
            print(f"Error encountered: {e}")
            page.screenshot(path="error_state.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
