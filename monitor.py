import os
import requests
from playwright.sync_api import sync_playwright

EMAIL = os.environ.get("MK_EMAIL")
PASSWORD = os.environ.get("MK_PASSWORD")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
LOGIN_URL = "https://meetcritique.com/login"  # Replace with actual login URL if different
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

        # 1. Login
        page.goto(LOGIN_URL)
        page.fill('input[type="email"]', EMAIL)
        page.fill('input[type="password"]', PASSWORD)
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle")

        # 2. Inspect dashboard
        page.goto(DASHBOARD_URL)
        page.wait_for_selector("text=meetcritiques available:")

        # Locate the container for 'meetcritiques available' and extract the number
        card = page.locator("div", has_text="meetcritiques available:").last
        text_content = card.inner_text()
        
        # Pull digits from the card text
        digits = "".join([c for c in text_content.splitlines()[-1] if c.isdigit()])
        count = int(digits) if digits else 0

        print(f"Current available critiques: {count}")

        # 3. Alert if work is available
        if count > 0:
            notify(f"MeetCritique alert! {count} critiques are available for review now.")

        browser.close()

if __name__ == "__main__":
    run()
