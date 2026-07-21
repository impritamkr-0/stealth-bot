import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from pyvirtualdisplay import Display
import time
import random
import string
import re
import requests
from fake_useragent import UserAgent
import subprocess
import sys

# --- CONFIGURATION ---
TARGET_URL = "https://deepvincilimited.sjv.io/bkP2rv"  # Affiliate Link
POLLING_DELAY = 3  # Seconds between checking Mail.tm API
MAX_POLLING_ATTEMPTS = 40  # Max attempts (120 seconds wait total)

def get_chrome_major_version():
    """Automatically detects the installed Chrome major version on Linux."""
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        major_version = int(output.strip().split()[2].split('.')[0])
        return major_version
    except Exception as e:
        print(f"Failed to detect Chrome version: {e}")
        return None

def human_like_delay(min_sec=0.5, max_sec=1.5):
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_type(element, text, min_delay=0.08, max_delay=0.2):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

# --- MAIL.TM API FUNCTIONS ---
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def create_mail_tm_account():
    """Fetches a domain, generates an address, and returns the email & auth token."""
    try:
        res = requests.get("https://api.mail.tm/domains", headers=API_HEADERS, timeout=10)
        data = res.json()
        if isinstance(data, list):
            domain = data[0]['domain']
        else:
            domain = data.get('hydra:member', [{}])[0].get('domain')

        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        address = f"{username}@{domain}"
        password = "StealthP@ssword123!"  # Strong password for Mail.tm

        payload = {"address": address, "password": password}
        requests.post("https://api.mail.tm/accounts", json=payload, headers=API_HEADERS, timeout=10)
        token_res = requests.post("https://api.mail.tm/token", json=payload, headers=API_HEADERS, timeout=10)
        token = token_res.json()['token']
        return address, token
    except Exception as e:
        print(f"Mail.tm API error: {e}")
        return None, None

def check_mail_tm_inbox(token):
    """Checks the inbox using the secure JWT token."""
    headers = API_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.get("https://api.mail.tm/messages", headers=headers, timeout=10)
        if res.status_code != 200:
            return []
        data = res.json()
        if isinstance(data, list):
            return data
        return data.get('hydra:member', [])
    except Exception:
        return []

def fetch_mail_tm_message(token, msg_id):
    """Fetches the actual body of the email."""
    headers = API_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers, timeout=10)
        return res.json()
    except Exception:
        return {}

def extract_code_from_text(text_content):
    """Parses text to reliably extract a 4 to 6 digit verification code."""
    if not text_content:
        return None
    
    clean_text = re.sub(r'<[^>]+>', ' ', str(text_content))
    patterns = [
        r'(?:code|verification|otp)\s*(?:is|:|\s)\s*([0-9]{4,6})',
        r'([0-9]{4,6})\s*(?:is your verification code|is your code)',
        r'\b([0-9]{4,6})\b'
    ]
    for pat in patterns:
        match = re.search(pat, clean_text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def run_stealth_automation():
    # --- Start Virtual Display (For headless Linux environments) ---
    print("Spinning up the Xvfb Ghost Monitor...")
    display = Display(visible=0, size=(1920, 1080))
    display.start()

    # --- Generate Email via API ---
    print("Generating temporary email via Mail.tm API...")
    my_email, api_token = create_mail_tm_account()
    if not my_email:
        print("Failed to generate email. Exiting.")
        display.stop()
        return
    print(f"Success! Got stealth email: {my_email}")

    # --- Stealth Chrome Setup ---
    ua = UserAgent()
    user_agent = ua.random
    options = uc.ChromeOptions()
    options.add_argument(f"--user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    print("Launching stealth Chrome...")
    chrome_version = get_chrome_major_version()
    if chrome_version:
        driver = uc.Chrome(options=options, version_main=chrome_version)
    else:
        driver = uc.Chrome(options=options)

    wait = WebDriverWait(driver, 20)

    try:
        # --- Navigate to the Website ---
        print(f"Opening registration page: {TARGET_URL}")
        driver.get(TARGET_URL)
        human_like_delay(3, 5)

        # --- Initial Redirect/Login State Check ---
        # The affiliate link often opens Image 0 (Welcome Back / Login) initially.
        try:
            print("Checking if we need to click 'Register' from the Login page (Image 0)...")
            # Wait for Login screen text
            wait.until(EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Welcome Back')]")))
            register_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'account?')]/a[contains(text(), 'Register')]")))
            ActionChains(driver).move_to_element(register_link).click().perform()
            human_like_delay(1, 2)
        except Exception:
            print("Did not find Login screen. Assuming we landed on Register screen.")

        # =========================================================
        # STEP 1: CREATE ACCOUNT (Image 3)
        # =========================================================
        print("Waiting for 'Create Account' screen (Image 3)...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Create Account')]")))
        
        # Locate the email field specifically (using placeholder or surrounding text)
        email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Create Account')]/following-sibling::div//input")))
        print(f"Entering email address: {my_email}")
        human_like_type(email_field, my_email)
        human_like_delay(1, 2)

        # Click the correct "Next Step" button on Image 3
        print("Clicking Next Step (Image 3)...")
        next_btn_create = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Create Account')]/following-sibling::div//button[contains(text(), 'Next Step')]")))
        ActionChains(driver).move_to_element(next_btn_create).click().perform()
        human_like_delay(3, 5)

        # =========================================================
        # STEP 2: SET PASSWORD (Image 1)
        # =========================================================
        print("Waiting for 'Set Password' screen (Image 1)...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Set Password')]")))
        
        # Explicitly locate the Password and Confirm Password inputs on Image 1
        password_input = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Set Password')]/following-sibling::div//input[@placeholder='Password']")))
        confirm_input = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Set Password')]/following-sibling::div//input[@placeholder='Confirm Password']")))
        
        secure_password = "Stealth@P@ssword99!"
        print("Entering Password...")
        human_like_type(password_input, secure_password)
        human_like_delay(0.5, 1)
        
        print("Entering Confirm Password...")
        human_like_type(confirm_input, secure_password)
        
        # Dispatch blur event on confirm field to ensure the form registers the valid state
        driver.execute_script("arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));", confirm_input)
        human_like_delay(1, 2)

        # Click the distinct "Next Step" button on Image 1
        print("Clicking Next Step (Image 1)...")
        next_btn_password = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Set Password')]/following-sibling::div//button[contains(text(), 'Next Step')]")))
        ActionChains(driver).move_to_element(next_btn_password).click().perform()
        
        # Short wait to allow the email request to fire
        human_like_delay(3, 5)

        # =========================================================
        # STEP 3: WAIT FOR CODE VIA MAIL.TM API
        # =========================================================
        print(f"Polling Mail.tm every {POLLING_DELAY}s for verification code (up to {POLLING_DELAY * MAX_POLLING_ATTEMPTS}s)...")
        verification_code = None
        for attempt in range(MAX_POLLING_ATTEMPTS):
            human_like_delay(POLLING_DELAY, POLLING_DELAY + 0.5)
            inbox = check_mail_tm_inbox(api_token)
            if inbox:
                print(f"Email received on attempt {attempt+1}! Parsing code...")
                msg_id = inbox[0]['id']
                email_data = fetch_mail_tm_message(api_token, msg_id)
                full_content = f"{email_data.get('intro', '')} {email_data.get('text', '')} {email_data.get('html', '')}"
                verification_code = extract_code_from_text(full_content)
                if verification_code:
                    print(f"Extracted verification code: {verification_code}")
                    break
        
        if not verification_code:
            print("Failed to receive verification code in time.")
            raise Exception("Timeout waiting for verification email.")

        # =========================================================
        # STEP 4: ENTER CODE & COMPLETE (Image 2)
        # =========================================================
        print("Waiting for 'Email Verification' screen (Image 2)...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Email Verification')]")))

        # Locate the code input field specifically on Image 2
        code_input = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Email Verification')]/following-sibling::div//input[@placeholder='Verification Code']")))
        print(f"Entering extracted code: {verification_code}")
        human_like_type(code_input, verification_code)
        human_like_delay(1, 2)

        # Click the "Complete Registration" button specifically on Image 2
        print("Clicking 'Complete Registration' (Image 2)...")
        complete_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Email Verification')]/following-sibling::div//button[contains(text(), 'Complete Registration')]")))
        ActionChains(driver).move_to_element(complete_btn).click().perform()

        # --- Final Wait/Completion ---
        print("Registration final submission completed! Waiting for final state...")
        human_like_delay(5, 7)
        print("AUTOMATION COMPLETE!")

    except Exception as e:
        print(f"Error encountered: {e}")
        try:
            driver.save_screenshot("debug_error_visual_flow.png")
            print("Debug screenshot saved: debug_error_visual_flow.png")
        except Exception:
            pass
        sys.exit(1)
        
    finally:
        driver.quit()
        display.stop()

if __name__ == "__main__":
    run_stealth_automation()
