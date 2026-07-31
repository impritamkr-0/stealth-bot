import os
import sys
import subprocess
import time
import random
import string
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def get_chrome_version():
    """Get installed Chrome major version"""
    try:
        result = subprocess.run(
            ['google-chrome', '--version'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        version_str = result.stdout.strip()
        log(f"Detected: {version_str}")
        # Extract major version (e.g., "150" from "Google Chrome 150.0.7871.0")
        version = int(version_str.split()[-1].split('.')[0])
        return version
    except Exception as e:
        log(f"Version detection failed: {e}")
        return None

def generate_random_email():
    domains = ["1secmail.com", "1secmail.net", "1secmail.org"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{random.choice(domains)}"

def generate_strong_password():
    upper = random.choice(string.ascii_uppercase)
    lower = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice("!@#$%^&*")
    remaining = ''.join(random.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(8))
    password = upper + lower + digit + special + remaining
    password = ''.join(random.sample(password, len(password)))
    return password

def wait_for_element(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    except:
        return None

def smart_fill_field(driver, element, text):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        element.clear()
        element.send_keys(text)
        time.sleep(0.3)
        # Verify it was filled
        if element.get_attribute("value") == text:
            return True
        # Fallback to JS
        driver.execute_script(f"arguments[0].value = '{text}';", element)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", element)
        return True
    except:
        return False

def click_submit_button(driver, final=False):
    selectors = [
        "//button[contains(text(), 'Create account')]",
        "//button[contains(text(), 'Create Account')]",
        "//button[@type='submit']",
        "//button[contains(@class, 'btn-primary')]",
    ]
    if final:
        selectors = ["//button[contains(text(), 'Create account')]"] + selectors
    
    for selector in selectors:
        try:
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            driver.execute_script("arguments[0].click();", btn)
            log("Submit clicked")
            return True
        except:
            continue
    return False

def click_audio_button(driver):
    log("Switching to audio CAPTCHA...")
    try:
        time.sleep(2)
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        challenge_iframe = None
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            if "recaptcha" in src and ("challenge" in src or "bframe" in src):
                challenge_iframe = iframe
                break
        
        if challenge_iframe:
            driver.switch_to.frame(challenge_iframe)
            log("Switched to challenge iframe")
            time.sleep(1)
            
            # Try to click audio button
            try:
                btn = driver.find_element(By.ID, "recaptcha-audio-button")
                driver.execute_script("arguments[0].click();", btn)
                log("Audio button clicked")
                driver.switch_to.default_content()
                return True
            except:
                # Try alternative selectors
                for sel in ["//button[contains(@class, 'rc-button-audio')]", "//button[@title='Get an audio challenge']"]:
                    try:
                        btn = driver.find_element(By.XPATH, sel)
                        driver.execute_script("arguments[0].click();", btn)
                        log("Audio button clicked (alt)")
                        driver.switch_to.default_content()
                        return True
                    except:
                        continue
        
        driver.switch_to.default_content()
        return False
    except Exception as e:
        log(f"Audio button error: {e}")
        driver.switch_to.default_content()
        return False

def check_for_captcha(driver):
    try:
        return len(driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")) > 0
    except:
        return False

def launch_driver():
    """Launch Chrome with version 150"""
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    buster_path = os.environ.get('BUSTER_PATH', '/opt/buster')
    proxy = os.environ.get('PROXY_URL')
    
    # Create fresh options
    options = uc.ChromeOptions()
    
    if is_github:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
    
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    
    if proxy:
        options.add_argument(f'--proxy-server=http://{proxy}')
        log(f"Proxy: {proxy}")
    
    if os.path.exists(buster_path) and os.path.exists(f"{buster_path}/manifest.json"):
        options.add_argument(f"--load-extension={buster_path}")
        log("Buster loaded")
    
    # Launch with version 150 (hardcoded to match actual Chrome)
    log("Launching Chrome...")
    try:
        return uc.Chrome(options=options, version_main=150)
    except Exception as e:
        log(f"Launch error: {e}")
        # Fallback - create fresh options again!
        options = uc.ChromeOptions()
        if is_github:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        if proxy:
            options.add_argument(f'--proxy-server=http://{proxy}')
        if os.path.exists(buster_path):
            options.add_argument(f"--load-extension={buster_path}")
        return uc.Chrome(options=options)  # Auto-detect

def run_bot():
    log("=" * 60)
    log("EURODNS BOT STARTING")
    log("=" * 60)
    
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    # Generate credentials
    email = generate_random_email()
    password = generate_strong_password()
    
    log(f"Email: {email}")
    log(f"Password: {'*' * len(password)} ({len(password)} chars)")
    
    # Save immediately
    if is_github:
        with open("account_credentials.txt", "w") as f:
            f.write(f"Email: {email}\nPassword: {password}\n")
    
    # Setup Chrome
    log("Setting up Chrome...")
    driver = None
    
    # Try launching with retry
    for attempt in range(3):
        try:
            log(f"Launch attempt {attempt + 1}...")
            driver = launch_driver()
            log("Chrome launched successfully")
            break
        except Exception as e:
            log(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    
    if not driver:
        log("Fatal: Could not launch Chrome")
        sys.exit(1)
    
    # Apply stealth
    try:
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    except:
        pass
    
    driver.implicitly_wait(10)
    
    try:
        # Navigate to registration
        log("Loading registration page...")
        driver.get("https://my.eurodns.com/login/createNewAccount")
        time.sleep(5)
        
        if is_github:
            driver.save_screenshot("screenshot_01_loaded.png")
        
        # Fill form
        log("Filling form...")
        
        # Email
        email_field = wait_for_element(driver, By.XPATH, "//input[@type='email']", timeout=15)
        if not email_field:
            raise Exception("Email field not found")
        
        smart_fill_field(driver, email_field, email)
        log("Email filled")
        time.sleep(1)
        
        # Password fields
        pass_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
        if len(pass_fields) >= 2:
            smart_fill_field(driver, pass_fields[0], password)
            log("Password filled")
            time.sleep(0.5)
            smart_fill_field(driver, pass_fields[1], password)
            log("Confirm password filled")
        else:
            log(f"Warning: Found {len(pass_fields)} password field(s)")
        
        # Checkboxes
        try:
            for cb in driver.find_elements(By.XPATH, "//input[@type='checkbox']"):
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
        except:
            pass
        
        if is_github:
            driver.save_screenshot("screenshot_02_filled.png")
        
        # Submit
        log("Submitting form...")
        click_submit_button(driver)
        time.sleep(8)
        
        if is_github:
            driver.save_screenshot("screenshot_03_submitted.png")
        
        # Handle CAPTCHA
        if check_for_captcha(driver):
            log("CAPTCHA detected!")
            
            if click_audio_button(driver):
                log("Waiting for Buster (30s)...")
                time.sleep(30)
                
                if not check_for_captcha(driver):
                    log("CAPTCHA solved!")
                else:
                    log("CAPTCHA still present")
            
            if is_github:
                driver.save_screenshot("screenshot_04_captcha.png")
        
        # Final submit
        log("Final submission...")
        time.sleep(3)
        
        for i in range(3):
            if click_submit_button(driver, final=True):
                break
            time.sleep(2)
        
        time.sleep(10)
        
        if is_github:
            driver.save_screenshot("screenshot_05_final.png")
        
        # Check result
        url = driver.current_url
        page = driver.page_source.lower()
        
        success = any(x in page for x in ["welcome", "success", "verification", "dashboard"]) or "create" not in url
        
        log("=" * 60)
        log("SUCCESS!" if success else "UNCLEAR")
        log(f"URL: {url}")
        log("=" * 60)
        
        if is_github:
            with open("account_credentials.txt", "a") as f:
                f.write(f"URL: {url}\nStatus: {'SUCCESS' if success else 'UNKNOWN'}\n")
        
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        if is_github:
            driver.save_screenshot("screenshot_error.png")
    finally:
        log("Closing browser...")
        try:
            driver.quit()
        except:
            pass
        log("Done")

if __name__ == "__main__":
    run_bot()
