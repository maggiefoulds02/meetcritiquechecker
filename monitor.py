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
        # Launch with arguments to prevent bot detection and rendering issues
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
            page.screenshot(path="step1_login_page.png")

            # Click the 'Login' tab pill at the top of the box if it exists, to ensure login fields are active
            login_tab = page.locator('.um-login-nav, button:has-text("Login"), a:has-text("Login")').first
            if login_tab.count() > 0 and login_tab.is_visible():
                try:
                    login_tab.click()
                    page.wait_for_timeout(500)
                except Exception:
                    pass

            print("2. Filling visible credentials...")
            # Use state='visible' so Playwright skips the hidden registration fields
            user_input = page.locator('input[id^="user_login"]:visible, input[name^="user_login"]:visible, input[type="text"]:visible').first
            user_input.wait_for(state="visible", timeout=15000)
            user_input.fill(EMAIL)

            pass_input = page.locator('input[id^="user_password"]:visible, input[name^="user_password"]:visible, input[type="password"]:visible').first
            pass_input.wait_for(state="visible", timeout=10000)
            pass_input.fill(PASSWORD)

            page.screenshot(path="step2_filled.png")

            print("3. Submitting login...")
            # Click the primary submit button in the login form or hit enter
            submit_btn = page.locator('input[type="submit"][value*="Log"], button:has-text("Login"):visible, input[id="um-submit-btn"]:visible').first
            if submit_btn.count() > 0 and submit_btn.is_visible():
                submit_btn.click()
            else:
                pass_input.press("Enter")

            # Wait for authentication redirect
            page.wait_for_timeout(6000)
            page.screenshot(path="step3_after_submit.png")

            print("4. Navigating to dashboard...")
            page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=30000)
            page.screenshot(path="step4_dashboard.png")

            # Verify and read the critique count
            print("5. Parsing critique count...")
            page.wait_for_selector("text=meetcritiques available:", timeout=15000)
            
            card = page.locator('div:has-text("meetcritiques available:")').last
            card_text = card.inner_text()
            
            numbers = re.findall(r'\d+', card_text)
            count = int(numbers[-1]) if numbers else 0
            print(f"--> SUCCESS! Current available critiques: {count} <--")

            if count > 0:
                notify(f"MeetCritique Alert: {count} critique(s) available for review right now!")

        except Exception as e:
            print(f"Error encountered: {e}")
            page.screenshot(path="error_state.png")
            with open("error_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
