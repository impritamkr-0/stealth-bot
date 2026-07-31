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
    """Auto-detect installed Chrome version for driver matching"""
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
        log(f"Could not detect Chrome version: {e}")
        return None

def generate_random_email():
    domains = ["1secmail.com", "1secmail.net", "1secmail.org"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{random.choice(domains)}"

def generate_strong_password():
    """Generate password meeting EuroDNS requirements: min 8 chars, upper, lower, number, special"""
    # Ensure at least one of each required character type
    upper = random.choice(string.ascii_uppercase)
    lower = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice("!@#$%^&*")
    
    # Fill remaining with random mix (total 12 chars for safety)
    remaining_length = 8  # 12 total - 4 required = 8 more
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    remaining = ''.join(random.choice(all_chars) for _ in range(remaining_length))
    
    # Combine and shuffle
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

def wait_for_element_clickable(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
    except:
        return None

def smart_fill_field(driver, element, text):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        element.clear()
        # Click first to ensure focus
        element.click()
        time.sleep(0.2)
        element.send_keys(text)
        time.sleep(0.3)
        return True
    except:
        try:
            driver.execute_script(f"arguments[0].value = '{text}';", element)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', {{bubbles: true}}));", element)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change', {{bubbles: true}}));", element)
            return True
        except:
            return False

def click_submit_button(driver, final=False):
    selectors = [
        "//button[contains(text(), 'Create account')]",
        "//button[contains(text(), 'Create Account')]",
        "//button[@type='submit']",
        "//button[contains(@class, 'btn-primary')]",
        "//input[@type='submit']",
        "//button[contains(@class, 'submit')]",
        "//button[contains(@class, 'btn') and contains(@class, 'primary')]",
    ]
    
    if final:
        selectors = ["//button[contains(text(), 'Create account') or contains(text(), 'Create Account')]"] + selectors
    
    for selector in selectors:
        try:
            by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((by, selector))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", btn)
            log("Submit clicked")
            return True
        except:
            continue
    
    try:
        driver.execute_script("""
            var btns = document.querySelectorAll('button[type="submit"], button.btn-primary, input[type="submit"]');
            for(var i=0; i<btns.length; i++) {
                if(btns[i].offsetParent !== null) {
                    btns[i].click();
                    return true;
                }
            }
        """)
        return True
    except:
        pass
    return False

def click_audio_button(driver):
    """Click audio button for Buster to solve - handles nested reCAPTCHA iframes"""
    log("Switching to audio CAPTCHA...")
    
    try:
        # reCAPTCHA has multiple iframes - we need to find the challenge iframe
        # First, find all iframes with recaptcha
        time.sleep(2)  # Wait for iframe to load
        
        # Try to find and switch to the challenge iframe (usually contains 'bframe' in src)
        challenge_iframe = None
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            if "recaptcha" in src and ("challenge" in src or "bframe" in src):
                challenge_iframe = iframe
                break
        
        if not challenge_iframe:
            # Try broader search
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "recaptcha" in src:
                    challenge_iframe = iframe
                    break
        
        if challenge_iframe:
            driver.switch_to.frame(challenge_iframe)
            log("Switched to reCAPTCHA challenge iframe")
            time.sleep(1)
            
            # Try multiple selectors for audio button
            audio_selectors = [
                "//button[@id='recaptcha-audio-button']",
                "//button[contains(@class, 'audio-button')]",
                "//button[contains(@title, 'audio')]",
                "//button[contains(@aria-label, 'audio')]",
                "//button[contains(@aria-label, 'Audio')]",
                "//div[contains(@class, 'button-holder')]//button",
                "//button[contains(@class, 'rc-button') and contains(@class, 'challenge')]",
                "//span[@id='recaptcha-anchor']/following::button[contains(@class, 'audio')]",
                "//button[@id='recaptcha-audio-button' or contains(@class, 'audio')]",
            ]
            
            for selector in audio_selectors:
                try:
                    btn = driver.find_element(By.XPATH, selector)
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        log(f"Audio button clicked using: {selector}")
                        driver.switch_to.default_content()
                        return True
                except:
                    continue
            
            # Try JavaScript click as last resort
            try:
                driver.execute_script("""
                    var btn = document.querySelector('#recaptcha-audio-button, .rc-button-audio, button[title*="audio"]');
                    if(btn) btn.click();
                """)
                log("Audio button clicked via JavaScript")
                driver.switch_to.default_content()
                return True
            except:
                pass
        
        driver.switch_to.default_content()
        log("Could not find audio button")
        return False
        
    except Exception as e:
        log(f"Audio button error: {e}")
        driver.switch_to.default_content()
        return False

def check_for_captcha(driver):
    """Check for reCAPTCHA presence"""
    try:
        iframes = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
        return len(iframes) > 0
    except:
        return False

def wait_for_captcha_solve(driver, timeout=30):
    """Wait for Buster to solve CAPTCHA"""
    start = time.time()
    while time.time() - start < timeout:
        if not check_for_captcha(driver):
            return True
        time.sleep(1)
    return False

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
    options = uc.ChromeOptions()
    
    if is_github:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
    
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Load Buster if available
    buster_path = os.environ.get('BUSTER_PATH', '/opt/buster')
    if os.path.exists(buster_path) and os.path.exists(f"{buster_path}/manifest.json"):
        options.add_argument(f"--load-extension={buster_path}")
        log("Buster loaded")
    
    # Get Chrome version and launch with matching driver
    chrome_version = get_chrome_version()
    
    log("Launching Chrome...")
    driver = None
    try:
        if chrome_version:
            log(f"Using Chrome version: {chrome_version}")
            driver = uc.Chrome(options=options, version_main=chrome_version)
        else:
            driver = uc.Chrome(options=options)
    except Exception as e:
        log(f"Launch failed: {e}")
        log("Retrying with auto-detection...")
        try:
            driver = uc.Chrome(options=options)
        except Exception as e2:
            log(f"Fatal: {e2}")
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
        
        # Wait for form to be ready
        log("Waiting for form...")
        time.sleep(3)
        
        # Fill form - try multiple selectors for email
        log("Filling form...")
        
        email_field = None
        email_selectors = [
            "//input[@type='email']",
            "//input[@name='email' or @id='email']",
            "//input[contains(@placeholder, 'mail')]",
            "//input[contains(@name, 'email')]",
            "//input[@type='text' and contains(@name, 'mail')]",
        ]
        
        for selector in email_selectors:
            email_field = wait_for_element(driver, By.XPATH, selector, timeout=5)
            if email_field:
                log(f"Found email field with: {selector}")
                break
        
        if not email_field:
            raise Exception("Email field not found")
        
        smart_fill_field(driver, email_field, email)
        log("Email filled")
        time.sleep(1)
        
        # Find password fields - try multiple approaches
        pass_fields = []
        pass_selectors = [
            "//input[@type='password']",
            "//input[contains(@name, 'password') or contains(@id, 'password')]",
            "//input[contains(@placeholder, 'password')]",
        ]
        
        for selector in pass_selectors:
            pass_fields = driver.find_elements(By.XPATH, selector)
            if len(pass_fields) >= 2:
                log(f"Found {len(pass_fields)} password fields with: {selector}")
                break
        
        if len(pass_fields) >= 2:
            smart_fill_field(driver, pass_fields[0], password)
            log("Password filled")
            time.sleep(0.5)
            smart_fill_field(driver, pass_fields[1], password)
            log("Confirm password filled")
        else:
            log(f"Warning: Only found {len(pass_fields)} password field(s)")
        
        # Checkboxes - EuroDNS usually has terms checkbox
        try:
            checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            log(f"Found {len(checkboxes)} checkboxes")
            for i, cb in enumerate(checkboxes):
                if not cb.is_selected():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cb)
                    time.sleep(0.3)
                    driver.execute_script("arguments[0].click();", cb)
                    log(f"Clicked checkbox {i+1}")
                    time.sleep(0.3)
        except Exception as e:
            log(f"Checkbox error: {e}")
        
        if is_github:
            driver.save_screenshot("screenshot_02_filled.png")
        
        # Submit
        log("Submitting form...")
        click_submit_button(driver)
        time.sleep(8)
        
        if is_github:
            driver.save_screenshot("screenshot_03_submitted.png")
        
        # Handle CAPTCHA
        captcha_attempts = 0
        while check_for_captcha(driver) and captcha_attempts < 3:
            log("CAPTCHA detected!")
            captcha_attempts += 1
            
            if click_audio_button(driver):
                log("Waiting for Buster to solve (30s)...")
                time.sleep(30)
                
                if wait_for_captcha_solve(driver, timeout=10):
                    log("CAPTCHA solved!")
                    break
                else:
                    log("CAPTCHA still present, may need manual intervention")
            else:
                log("Could not click audio button, waiting...")
                time.sleep(5)
            
            if is_github:
                driver.save_screenshot(f"screenshot_04_captcha_attempt_{captcha_attempts}.png")
        
        # Final submit - may need to click again after CAPTCHA
        log("Final submission...")
        time.sleep(3)
        
        for i in range(3):
            if click_submit_button(driver, final=True):
                log(f"Final submit clicked (attempt {i+1})")
            time.sleep(3)
        
        time.sleep(10)
        
        if is_github:
            driver.save_screenshot("screenshot_05_final.png")
        
        # Check result
        url = driver.current_url
        page = driver.page_source.lower()
        
        success_indicators = ["welcome", "success", "verification", "dashboard", "account created", "confirm"]
        failure_indicators = ["error", "invalid", "failed", "captcha", "robot"]
        
        has_success = any(x in page for x in success_indicators)
        has_failure = any(x in page for x in failure_indicators)
        still_on_form = "create" in url or "newaccount" in url
        
        success = has_success or (not has_failure and not still_on_form)
        
        log("=" * 60)
        log("SUCCESS!" if success else "UNCLEAR/FAILED")
        log(f"URL: {url}")
        if has_success:
            log("Success indicators found in page")
        if has_failure:
            log("Failure indicators found in page")
        log("=" * 60)
        
        if is_github:
            with open("account_credentials.txt", "a") as f:
                f.write(f"URL: {url}\nStatus: {'SUCCESS' if success else 'UNKNOWN/FAILED'}\n")
        
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        if is_github and driver:
            driver.save_screenshot("screenshot_error.png")
    finally:
        log("Closing browser...")
        try:
            if driver:
                driver.quit()
        except:
            pass
        log("Done")

if __name__ == "__main__":
    run_bot()
