import os
import sys
import time
import random
import string
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"

# Retrieve API keys securely from GitHub Actions environment variables
BB_API_KEY = os.environ.get("BROWSERBASE_API_KEY")
BB_PROJECT_ID = os.environ.get("BROWSERBASE_PROJECT_ID")

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def generate_random_email():
    domains = ["1secmail.com", "1secmail.net", "1secmail.org"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{random.choice(domains)}"

def generate_strong_password():
    upper = random.choice(string.ascii_uppercase)
    lower = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice("!@#$%^&*-_=")
    remaining = ''.join(random.choice(string.ascii_letters + string.digits + "!@#$%^&*-_=") for _ in range(12))
    password = upper + lower + digit + special + remaining
    return ''.join(random.sample(password, len(password)))

def create_browserbase_session():
    """Requests a cloud browser session with automated CAPTCHA solving enabled."""
    if not BB_API_KEY or not BB_PROJECT_ID:
        log("Error: BROWSERBASE_API_KEY or BROWSERBASE_PROJECT_ID environment variables missing.")
        sys.exit(1)

    log("Requesting a new Browserbase cloud session...")
    url = "https://www.browserbase.com/v1/sessions"
    headers = {
        "x-bb-api-key": BB_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "projectId": BB_PROJECT_ID,
        "browserSettings": {
            "solveCaptchas": True  # Enables automated CAPTCHA solving
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        log(f"Failed to create Browserbase session: {response.text}")
        sys.exit(1)
        
    session_id = response.json()["id"]
    log(f"Browserbase Session created! ID: {session_id}")
    return session_id

def run_bot():
    log("=" * 60)
    log("EURODNS BROWSERBASE BOT STARTING")
    log("=" * 60)
    
    email = generate_random_email()
    password = generate_strong_password()
    
    log(f"Email: {email}")
    log(f"Password: {'*' * len(password)} ({len(password)} chars)")
    
    session_id = create_browserbase_session()
    websocket_url = f"wss://connect.browserbase.com?apiKey={BB_API_KEY}&sessionId={session_id}"
    
    with sync_playwright() as p:
        log("Connecting Playwright to remote Browserbase browser...")
        browser = p.chromium.connect_over_cdp(websocket_url)
        context = browser.contexts[0]
        page = context.pages[0]
        
        try:
            log(f"Loading URL: {TARGET_URL}")
            page.goto(TARGET_URL, timeout=60000)
            
            # 1. Accept Cookies
            log("Looking for Accept Cookies button...")
            try:
                page.click('//*[@id="cookiescript_accept"]', timeout=5000)
                log("Clicked Accept Cookies.")
            except Exception:
                log("Cookie button not found or already accepted.")

            # 2. Navigate to Registration
            log("Navigating to Account Registration...")
            page.click('//*[@id="account-item-logout"]')
            page.click('//*[@id="logout-user-section"]/a[2]')
            
            page.wait_for_selector("input[type='email']", timeout=10000)
            
            # 3. Fill Form
            log("Filling Email and Password...")
            page.fill("input[type='email']", email)
            passwords = page.locator("input[type='password']").all()
            for pw_field in passwords:
                pw_field.fill(password)
                
            # 4. Check Terms Checkbox
            try:
                page.check('//*[@id="subscribe-newsletter-checkbox-input"]')
                log("Checked Terms/Newsletter checkbox.")
            except Exception:
                pass
                
            # 5. Submit Form
            log("Clicking Create Account button...")
            submit_xpath = '/html/body/edns-root/edns-layout/div/div/edns-side-panels/mat-sidenav-container/mat-sidenav-content/div/div[2]/edns-new-account/div/div/form/div[4]/button'
            page.click(submit_xpath)
            
            log("Form submitted. Waiting for Browserbase CAPTCHA auto-solver and redirection...")
            page.wait_for_url(lambda url: "createNewAccount" not in url, timeout=35000)
            
            success = "createNewAccount" not in page.url
            log("=" * 60)
            log("SUCCESS! Account created!" if success else "FAILED - Page URL did not change.")
            log(f"Final URL: {page.url}")
            log("=" * 60)
            
        except Exception as e:
            log(f"An error occurred during execution: {e}")
            
        finally:
            log("Closing cloud browser connection...")
            browser.close()
            log("Done.")

if __name__ == "__main__":
    run_bot()
