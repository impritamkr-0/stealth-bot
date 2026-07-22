import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth
import time
import random
import string
import re
import requests
import sys

TARGET_URL = "https://deepvincilimited.sjv.io/bkP2rv"
POLLING_DELAY = 4  
MAX_POLLING_ATTEMPTS = 45

def human_like_delay(min_sec=1.5, max_sec=3.0):
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_type(driver, element, text):
    """Types characters one by one and triggers React validation events."""
    element.click()
    for char in text:
        element.send_keys(char)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
        time.sleep(random.uniform(0.1, 0.25))
    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element)
    driver.execute_script("arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));", element)

# --- MAIL.TM API ---
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def create_mail_tm_account():
    try:
        res = requests.get("https://api.mail.tm/domains", headers=API_HEADERS, timeout=10)
        data = res.json()
        domain = data[0]['domain'] if isinstance(data, list) else data.get('hydra:member', [{}])[0].get('domain')
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        address = f"{username}@{domain}"
        password = "StealthBotPassword123!"

        payload = {"address": address, "password": password}
        requests.post("https://api.mail.tm/accounts", json=payload, headers=API_HEADERS, timeout=10)
        token_res = requests.post("https://api.mail.tm/token", json=payload, headers=API_HEADERS, timeout=10)
        return address, token_res.json()['token']
    except Exception as e:
        print(f"Mail.tm API error: {e}")
        return None, None

def check_mail_tm_inbox(token):
    headers = API_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.get("https://api.mail.tm/messages", headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data if isinstance(data, list) else data.get('hydra:member', [])
    except Exception:
        pass
    return []

def fetch_mail_tm_message(token, msg_id):
    headers = API_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers, timeout=10)
        return res.json()
    except Exception:
        return {}

def extract_code_from_text(text_content):
    if not text_content:
        return None
    clean_text = re.sub(r'<[^>]+>', ' ', str(text_content))
    patterns = [
        r'(?:code|verification|otp|pin)\s*(?:is|:|\s)\s*([0-9]{4,6})',
        r'([0-9]{4,6})\s*(?:is your verification code|is your code|is your pin)',
        r'\b([0-9]{4,6})\b'
    ]
    for pat in patterns:
        match = re.search(pat, clean_text, re.IGNORECASE)
        if match:
            code = match.group(1)
            if code not in ["2024", "2025", "2026", "8080", "5000", "443"]:
                return code
    return None

def run_stealth_automation():
    print("Generating temporary email via Mail.tm API...")
    my_email, api_token = create_mail_tm_account()
    if not my_email:
        print("Failed to generate email. Exiting.")
        return
    print(f"Success! Got stealth email: {my_email}")

    options = uc.ChromeOptions() 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US,en;q=0.9")
    
    # We remove version_main so uc automatically detects the GitHub runner's Chrome version
    print("Launching stealth Chrome...")
    driver = uc.Chrome(options=options, version_main=150, headless=True)
    
    # Apply advanced selenium-stealth masking for macOS
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="MacIntel",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    # Strip the remaining Selenium variables
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """
    })

    wait = WebDriverWait(driver, 20)
    actions = ActionChains(driver)

    try:
        print(f"Opening registration landing page: {TARGET_URL}")
        driver.get(TARGET_URL)
        human_like_delay(5, 7)

        # Scroll slightly to look human
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
        human_like_delay(1, 2)

        print("Triggering registration modal view...")
        driver.execute_script("""
            let regLink = Array.from(document.querySelectorAll('a, span, button')).find(
                el => el.textContent.trim().toLowerCase() === 'register'
            );
            if (regLink) regLink.click();
        """)
        human_like_delay(2, 4)

        # 1. ENTER EMAIL
        print("Waiting for Email input field...")
        email_field = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@type='email'] | //input[contains(@placeholder, 'Email') or contains(@placeholder, 'email')]"
        )))
        print(f"Entering email address: {my_email}")
        human_like_type(driver, email_field, my_email)
        human_like_delay(1, 2)

        print("Clicking Next Step...")
        next_btn_email = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[contains(translate(text(), 'NEXT STEP', 'next step'), 'next step')]"
        )))
        actions.move_to_element(next_btn_email).pause(0.5).click().perform()
        human_like_delay(3, 4)

        # 2. ENTER PASSWORD
        print("Waiting for Password input fields...")
        password_input = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@placeholder='Password'] | (//input[@type='password'])[1]"
        )))
        confirm_input = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@placeholder='Confirm Password'] | (//input[@type='password'])[2]"
        )))

        secure_password = "StealthP@ssword2026!"
        print("Entering Password...")
        human_like_type(driver, password_input, secure_password)
        human_like_delay(0.5, 1.0)
        
        print("Entering Confirm Password...")
        human_like_type(driver, confirm_input, secure_password)
        human_like_delay(1, 2)

        print("Clicking Next Step for password submission...")
        next_btn_pass = wait.until(EC.presence_of_element_located((
            By.XPATH, "//button[contains(translate(text(), 'NEXT STEP', 'next step'), 'next step')]"
        )))
        
        driver.execute_script("arguments[0].removeAttribute('disabled');", next_btn_pass)
        actions.move_to_element(next_btn_pass).pause(0.5).click().perform()
        print("Password form submitted! Polling inbox for verification email...")
        human_like_delay(4, 6)

        # 3. POLL INBOX FOR CODE
        verification_code = None
        for attempt in range(MAX_POLLING_ATTEMPTS):
            time.sleep(POLLING_DELAY)
            inbox = check_mail_tm_inbox(api_token)

            if inbox:
                print(f"Inbox has {len(inbox)} message(s) on attempt {attempt+1}. Inspecting...")
                msg_id = inbox[0]['id']
                email_data = fetch_mail_tm_message(api_token, msg_id)
                full_content = f"{email_data.get('intro', '')} {email_data.get('text', '')} {email_data.get('html', '')}"
                verification_code = extract_code_from_text(full_content)

                if verification_code:
                    print(f"Extracted valid verification code: {verification_code}")
                    break
            else:
                print(f"Attempt {attempt+1}: Inbox empty, waiting...")

        if not verification_code:
            raise Exception("Timeout waiting for verification email.")

        # 4. ENTER VERIFICATION CODE
        print("Waiting for Verification Code input field...")
        code_input = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@placeholder='Verification Code'] | //input[@type='text']"
        )))
        print(f"Entering code: {verification_code}")
        human_like_type(driver, code_input, verification_code)
        human_like_delay(1, 2)

        print("Clicking Complete Registration...")
        complete_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[contains(translate(text(), 'COMPLETE REGISTRATION', 'complete registration'), 'complete registration')] | //button[contains(text(), 'Submit')]"
        )))
        actions.move_to_element(complete_btn).pause(0.5).click().perform()

        human_like_delay(5, 7)
        print("AUTOMATION COMPLETE SUCCESSFUL!")

    except Exception as e:
        print(f"Error encountered: {e}")
        try:
            driver.save_screenshot("debug_error_visual_flow.png")
        except Exception:
            pass
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_stealth_automation()
