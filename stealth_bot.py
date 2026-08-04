import os
import sys
import time
import random
import string
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"

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
            "solveCaptchas": True 
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code not in [200, 201]:
        log(f"Failed to create Browserbase session: {response.text}")
        sys.exit(1)
        
    data = response.json()
    connect_url = data.get("connectUrl")
    log(f"Browserbase Session created! ID: {data.get('id')}")
    return connect_url

def run_bot():
    log("=" * 60)
    log("EURODNS BROWSERBASE BOT STARTING")
    log("=" * 60)
    
    email = generate_random_email()
    password = generate_strong_password()
    
    log(f"Email: {email}")
    log(f"Password: {'*' * len(password)} ({len(password)} chars)")
    
    websocket_url = create_browserbase_session()
    
    with sync_playwright() as p:
        log("Connecting Playwright to remote Browserbase browser...")
        try:
            browser = p.chromium.connect_over_cdp(websocket_url)
            context = browser.contexts[0]
            page = context.pages[0]
            
            log(f"Loading URL: {TARGET_URL}")
            page.goto(TARGET_URL, timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            
            # Step 1: Accept all cookies
            log("Looking for Accept Cookies button...")
            try:
                cookie_xpath = '//*[@id="cookiescript_accept"]'
                page.locator(cookie_xpath).click(force=True, timeout=10000)
                log("Clicked Accept Cookies.")
                time.sleep(random.uniform(2.0, 5.0))
            except Exception as e:
                log(f"Cookie button not found or skipped: {e}")

            # Step 2: Click My account button
            log("Clicking 'My account' button...")
            try:
                my_acc_xpath = '//*[@id="account-item-logout"]'
                page.locator(my_acc_xpath).click(force=True, timeout=10000)
                log("Clicked My Account.")
                time.sleep(2)
            except Exception as e:
                log(f"Failed to click My Account: {e}")

            # Step 3: Click New account button & wait 5 seconds
            log("Clicking 'New account' button...")
            try:
                new_acc_xpath = '//*[@id="logout-user-section"]/a[2]'
                page.locator(new_acc_xpath).click(force=True, timeout=10000)
                log("Clicked New Account. Waiting 5 seconds for form...")
                time.sleep(5)
            except Exception as e:
                log(f"Failed to click New Account: {e}")

            # Fill Email and Password
            log("Filling Email and Password...")
            page.fill("//input[@type='email']", email)
            
            passwords = page.locator("//input[@type='password']").all()
            for pw_field in passwords:
                pw_field.fill(password)
                
            # Step 4: Click on small checkbox button
            log("Checking terms/newsletter checkbox...")
            try:
                checkbox_xpath = '//*[@id="subscribe-newsletter-checkbox-input"]'
                page.locator(checkbox_xpath).check(force=True, timeout=5000)
                log("Checkbox checked.")
            except Exception as e:
                log(f"Checkbox click failed or skipped: {e}")
                
            # Step 5: Click on exact create account button
            log("Clicking Create Account button...")
            # ADDED 'xpath=' SO PLAYWRIGHT DOES NOT CRASH HERE!
            submit_xpath = 'xpath=/html/body/edns-root/edns-layout/div/div/edns-side-panels/mat-sidenav-container/mat-sidenav-content/div/div[2]/edns-new-account/div/div/form/div[4]/button/span[2]'
            page.locator(submit_xpath).click(force=True)
            
            log("Form submitted! Waiting for Browserbase CAPTCHA auto-solver and redirection...")
            page.wait_for_url(lambda url: "createNewAccount" not in url, timeout=40000)
            
            success = "createNewAccount" not in page.url
            log("=" * 60)
            log("SUCCESS! Account created!" if success else "FAILED - Page URL did not change.")
            log(f"Final URL: {page.url}")
            log("=" * 60)
            
        except Exception as e:
            log(f"An error occurred during execution: {e}")
            sys.exit(1)
            
        finally:
            log("Closing cloud browser connection...")
            try:
                browser.close()
            except Exception:
                pass
            log("Done.")

if __name__ == "__main__":
    run_bot()
