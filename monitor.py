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
        browser = p.chromium.launch(headless=True)
        # Emulate a standard desktop user agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Navigating to login page...")
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        # Target the input directly by its label or name
        username_field = page.locator('input[name*="username"], input[name*="user_login"], input[id*="username"], input[type="text"]').first
        username_field.wait_for(timeout=15000)
        username_field.fill(EMAIL)

        password_field = page.locator('input[type="password"]').first
        password_field.fill(PASSWORD)

        # Click the blue 'Login' button at the bottom of the card
        login_btn = page.locator('button:has-text("Login"), input[value="Login"]').first
        if login_btn.count() > 0:
            login_btn.click()
        else:
            page.keyboard.press("Enter")

        # Wait for navigation/auth to complete
        page.wait_for_timeout(5000)

        # Open the dashboard
        print("Navigating to dashboard...")
        page.goto(DASHBOARD_URL, wait_until="networkidle")

        # Wait for the card text to appear
        page.wait_for_selector("text=meetcritiques available:", timeout=15000)

        # Grab the container holding "meetcritiques available"
        card = page.locator('div:has-text("meetcritiques available:")').last
        card_text = card.inner_text()

        # Extract all numbers from the card text
        numbers = re.findall(r'\d+', card_text)
        count = int(numbers[-1]) if numbers else 0

        print(f"Current available critiques: {count}")

        if count > 0:
            notify(f"MeetCritique Alert: {count} critique(s) available for review right now!")

        browser.close()

if __name__ == "__main__":
    run()
