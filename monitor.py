import os
import requests
from playwright.sync_api import sync_playwright

EMAIL = os.environ.get("MK_EMAIL")
PASSWORD = os.environ.get("MK_PASSWORD")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")

# Confirm this matches the exact URL where you enter your credentials
LOGIN_URL = "https://meetcritique.com/login" 
DASHBOARD_URL = "https://meetcritique.com/dashboard"

def notify(message):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={"Title": "MeetCritique Alert", "Priority": "urgent", "Tags": "rotating_light"}
    )

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(LOGIN_URL, wait_until="networkidle")

        # Save an image of the landing page to debug if it gets stuck
        page.screenshot(path="login_debug.png")

        # Flexible selector for email / username field
        email_input = page.locator('input[type="email"], input[name="email"], input[name="username"], input[type="text"]').first
        email_input.wait_for(timeout=10000)
        email_input.fill(EMAIL)

        # Flexible selector for password field
        pass_input = page.locator('input[type="password"]').first
        pass_input.fill(PASSWORD)
        
        # Press Enter or click Submit
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle")

        # Navigate to Dashboard
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        page.screenshot(path="dashboard_debug.png")

        # Locate the card
        card = page.locator("text=meetcritiques available:").locator("xpath=..")
        text_content = card.inner_text()

        # Extract number
        digits = "".join([c for c in text_content if c.isdigit()])
        count = int(digits) if digits else 0
        print(f"Current available critiques: {count}")

        if count > 0:
            notify(f"MeetCritique alert! {count} critiques are available for review now.")

        browser.close()

if __name__ == "__main__":
    run()
