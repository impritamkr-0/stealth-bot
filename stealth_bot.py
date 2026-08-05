import os
import sys
import time
import random
import string
from playwright.sync_api import sync_playwright

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"

BROWSERLESS_API_KEY = os.environ.get("BROWSERLESS_API_KEY")

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

def run_bot():
    if not BROWSERLESS_API_KEY:
        log("Error: BROWSERLESS_API_KEY environment variable missing.")
        sys.exit(1)

    log("=" * 60)
    log("EURODNS BROWSERLESS BOT STARTING")
    log("=" * 60)
    
    email = generate_random_email()
    password = generate_strong_password()
    
    log(f"Email: {email}")
    log(f"Password: {'*' * len(password)} ({len(password)} chars)")
    
    websocket_url = f"wss://production-sfo.browserless.io/stealth?token={BROWSERLESS_API_KEY}&solveCaptchas=true"
    
    with sync_playwright() as p:
        log("Connecting Playwright to remote Browserless.io browser...")
        try:
            browser = p.chromium.connect_over_cdp(websocket_url)
            context = browser.contexts[0]
            page = context.pages[0]
            
            # FIX: Force a large desktop viewport so the navigation menu doesn't get hidden!
            page.set_viewport_size({"width": 1920, "height": 1080})
            
            log(f"Loading URL: {TARGET_URL}")
            page.goto(TARGET_URL, timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            
            # 1. Accept all cookies button
            log("Looking for Accept Cookies button...")
            try:
                cookie_xpath = 'xpath=//*[@id="cookiescript_accept"]'
                page.locator(cookie_xpath).click(force=True, timeout=10000)
                log("Clicked Accept Cookies.")
                
                # Wait for 2-5 seconds
                time.sleep(random.uniform(2.0, 5.0))
            except Exception as e:
                log(f"Cookie button not found or skipped: {e}")

            # 2. My account button
            log("Clicking 'My account' button...")
            try:
                my_acc_xpath = 'xpath=//*[@id="account-item-logout"]'
                page.locator(my_acc_xpath).click(force=True, timeout=10000)
                log("Clicked My Account.")
            except Exception as e:
                log(f"Failed to click My Account: {e}")

            # 3. New account button
            log("Clicking 'New account' button...")
            try:
                new_acc_xpath = 'xpath=//*[@id="logout-user-section"]/a[2]'
                page.locator(new_acc_xpath).click(force=True, timeout=10000)
                log("Clicked New Account.")
                
                # Wait for 5 seconds to open the email and password entry box
                time.sleep(5)
            except Exception as e:
                log(f"Failed to click New Account: {e}")

            # Fill Email and Password
            log("Filling Email and Password...")
            page.fill("xpath=//input[@type='email']", email)
            
            passwords = page.locator("xpath=//input[@type='password']").all()
            for pw_field in passwords:
                pw_field.fill(password)
                
            # 4. Click on small checkbox button
            log("Checking terms/newsletter checkbox...")
            try:
                checkbox_xpath = 'xpath=//*[@id="subscribe-newsletter-checkbox-input"]'
                page.locator(checkbox_xpath).check(force=True, timeout=5000)
                log("Checkbox checked.")
            except Exception as e:
                log(f"Checkbox click failed or skipped: {e}")
                
            # 5. Click on create account button to open captcha solver and verifier
            log("Clicking Create Account button...")
            submit_xpath = 'xpath=/html/body/edns-root/edns-layout/div/div/edns-side-panels/mat-sidenav-container/mat-sidenav-content/div/div[2]/edns-new-account/div/div/form/div[4]/button/span[2]'
            page.locator(submit_xpath).click(force=True)
            
            log("Form submitted! Waiting for Browserless CAPTCHA auto-solver and redirection...")
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
