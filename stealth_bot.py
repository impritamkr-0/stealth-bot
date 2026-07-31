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
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def random_delay(min_sec=0.5, max_sec=2.0):
    """Random human-like delay"""
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_typing(element, text):
    """Type text with human-like delays"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))

def get_chrome_version():
    try:
        result = subprocess.run(
            ['google-chrome', '--version'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        version_str = result.stdout.strip()
        version = int(version_str.split()[-1].split('.')[0])
        return version
    except:
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
    remaining_length = 8
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    remaining = ''.join(random.choice(all_chars) for _ in range(remaining_length))
    password = upper + lower + digit + special + remaining
    password = ''.join(random.sample(password, len(password)))
    return password

def create_chrome_options():
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    buster_path = os.environ.get('BUSTER_PATH', '/opt/buster')
    
    options = uc.ChromeOptions()
    
    if is_github:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
    
    # Stealth arguments to avoid detection
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--disable-features=InterestFeedContentSuggestions")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Load Buster if available
    if os.path.exists(buster_path) and os.path.exists(f"{buster_path}/manifest.json"):
        options.add_argument(f"--load-extension={buster_path}")
        log("Buster loaded")
    
    return options

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

def handle_cookies(driver):
    """Handle cookie consent banner"""
    try:
        log("Handling cookies...")
        # Try to find and click "ACCEPT ALL" or "SAVE & CLOSE"
        cookie_buttons = [
            "//button[contains(text(), 'ACCEPT ALL')]",
            "//button[contains(text(), 'Accept All')]",
            "//button[contains(text(), 'SAVE & CLOSE')]",
            "//button[contains(text(), 'Save & Close')]",
            "//button[contains(@class, 'accept')]",
            "//button[contains(text(), 'AGREE')]",
            "//button[contains(text(), 'Agree')]",
        ]
        
        for selector in cookie_buttons:
            try:
                btn = driver.find_element(By.XPATH, selector)
                if btn.is_displayed():
                    btn.click()
                    log("Clicked cookie button")
                    random_delay(1, 2)
                    return True
            except:
                continue
    except:
        pass
    return False

def smart_fill_field(driver, element, text, human_like=True):
    """Fill field with human-like behavior"""
    try:
        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        random_delay(0.3, 0.7)
        
        # Click to focus
        element.click()
        random_delay(0.2, 0.5)
        
        # Clear field
        element.clear()
        random_delay(0.2, 0.4)
        
        if human_like:
            # Type like human
            human_like_typing(element, text)
        else:
            element.send_keys(text)
        
        random_delay(0.3, 0.6)
        
        # Trigger events
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", element)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", element)
        
        return True
    except Exception as e:
        log(f"Fill error: {e}")
        try:
            # Fallback to JavaScript
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
        "//input[@type='submit']",
        "//button[contains(@class, 'submit')]",
        "//button[contains(@class, 'btn') and contains(@class, 'primary')]",
        "//button[contains(text(), 'CREATE')]",
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
            random_delay(0.3, 0.6)
            driver.execute_script("arguments[0].click();", btn)
            log("Submit clicked")
            return True
        except:
            continue
    
    # JavaScript fallback
    try:
        driver.execute_script("""
            var btns = document.querySelectorAll('button[type="submit"], button.btn-primary, input[type="submit"], button');
            for(var i=0; i<btns.length; i++) {
                if(btns[i].offsetParent !== null && (btns[i].innerText.includes('Create') || btns[i].innerText.includes('Account'))) {
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
    log("Switching to audio CAPTCHA...")
    
    try:
        random_delay(2, 3)
        
        challenge_iframe = None
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            if "recaptcha" in src and ("challenge" in src or "bframe" in src):
                challenge_iframe = iframe
                break
        
        if not challenge_iframe:
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "recaptcha" in src:
                    challenge_iframe = iframe
                    break
        
        if challenge_iframe:
            driver.switch_to.frame(challenge_iframe)
            log("Switched to reCAPTCHA challenge iframe")
            random_delay(1, 2)
            
            # Check if we got the "Try again later" block
            try:
                error_text = driver.find_element(By.XPATH, "//div[contains(text(), 'Try again later')]")
                if error_text:
                    log("WARNING: reCAPTCHA detected automation - Try again later")
                    driver.switch_to.default_content()
                    return False
            except:
                pass
            
            audio_selectors = [
                "//button[@id='recaptcha-audio-button']",
                "//button[contains(@class, 'audio-button')]",
                "//button[contains(@title, 'audio')]",
                "//button[contains(@aria-label', 'audio')]",
                "//button[contains(@class, 'rc-button-audio')]",
                "//div[@class='button-holder']//button",
            ]
            
            for selector in audio_selectors:
                try:
                    btn = driver.find_element(By.XPATH, selector)
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        log("Audio button clicked")
                        driver.switch_to.default_content()
                        return True
                except:
                    continue
            
            # JavaScript fallback
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
    try:
        iframes = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
        return len(iframes) > 0
    except:
        return False

def check_for_captcha_error(driver):
    """Check if reCAPTCHA is showing 'Try again later'"""
    try:
        # Switch to challenge iframe and check for error
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            if "recaptcha" in src and ("challenge" in src or "bframe" in src):
                driver.switch_to.frame(iframe)
                try:
                    error = driver.find_element(By.XPATH, "//div[contains(text(), 'Try again later')]")
                    driver.switch_to.default_content()
                    return True
                except:
                    driver.switch_to.default_content()
        return False
    except:
        return False

def wait_for_captcha_solve(driver, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        if not check_for_captcha(driver):
            return True
        time.sleep(1)
    return False

def launch_driver_with_retry(max_retries=3):
    driver = None
    
    for attempt in range(max_retries):
        log(f"Launch attempt {attempt + 1}/{max_retries}...")
        
        options = create_chrome_options()
        
        try:
            log("Trying auto-detection...")
            driver = uc.Chrome(options=options)
            log("Chrome launched successfully")
            return driver
            
        except Exception as e:
            log(f"Auto-detection failed: {e}")
            
            if attempt == 1:
                try:
                    chrome_version = get_chrome_version()
                    if chrome_version:
                        log(f"Trying with version: {chrome_version}")
                        options = create_chrome_options()
                        driver = uc.Chrome(options=options, version_main=chrome_version)
                        log("Chrome launched with version")
                        return driver
                except Exception as e2:
                    log(f"Version-based launch failed: {e2}")
            
            if attempt < max_retries - 1:
                log(f"Waiting before retry...")
                time.sleep(3)
    
    raise Exception("Failed to launch Chrome after all retries")

def run_bot():
    log("=" * 60)
    log("EURODNS BOT STARTING")
    log("=" * 60)
    
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    email = generate_random_email()
    password = generate_strong_password()
    
    log(f"Email: {email}")
    log(f"Password: {'*' * len(password)} ({len(password)} chars)")
    
    if is_github:
        with open("account_credentials.txt", "w") as f:
            f.write(f"Email: {email}\nPassword: {password}\n")
    
    log("Setting up Chrome...")
    driver = None
    
    try:
        driver = launch_driver_with_retry(max_retries=3)
    except Exception as e:
        log(f"Fatal: Could not launch Chrome: {e}")
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
        log("Loading registration page...")
        driver.get("https://my.eurodns.com/login/createNewAccount")
        random_delay(3, 5)
        
        if is_github:
            driver.save_screenshot("screenshot_01_loaded.png")
        
        # Handle cookies first
        handle_cookies(driver)
        
        log("Waiting for form...")
        random_delay(2, 4)
        
        log("Filling form...")
        
        # Find and fill email
        email_field = None
        email_selectors = [
            "//input[@type='email']",
            "//input[@name='email']",
            "//input[@id='email']",
            "//input[contains(@placeholder, 'mail')]",
            "//input[contains(@name, 'email')]",
        ]
        
        for selector in email_selectors:
            email_field = wait_for_element(driver, By.XPATH, selector, timeout=5)
            if email_field:
                log(f"Found email field")
                break
        
        if not email_field:
            raise Exception("Email field not found")
        
        smart_fill_field(driver, email_field, email)
        log("Email filled")
        random_delay(1, 2)
        
        # Find and fill password fields
        pass_fields = []
        pass_selectors = [
            "//input[@type='password']",
            "//input[contains(@name, 'password')]",
            "//input[contains(@id, 'password')]",
            "//input[contains(@placeholder, 'password')]",
        ]
        
        for selector in pass_selectors:
            pass_fields = driver.find_elements(By.XPATH, selector)
            if len(pass_fields) >= 2:
                log(f"Found {len(pass_fields)} password fields")
                break
        
        if len(pass_fields) >= 2:
            smart_fill_field(driver, pass_fields[0], password)
            log("Password filled")
            random_delay(0.5, 1.5)
            smart_fill_field(driver, pass_fields[1], password)
            log("Confirm password filled")
            
            # Verify passwords were filled
            val1 = pass_fields[0].get_attribute("value")
            val2 = pass_fields[1].get_attribute("value")
            log(f"Password field values length: {len(val1)}, {len(val2)}")
        else:
            log(f"Warning: Only found {len(pass_fields)} password field(s)")
        
        # Handle checkboxes
        try:
            checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            log(f"Found {len(checkboxes)} checkboxes")
            for i, cb in enumerate(checkboxes):
                if not cb.is_selected():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cb)
                    random_delay(0.3, 0.6)
                    driver.execute_script("arguments[0].click();", cb)
                    log(f"Clicked checkbox {i+1}")
                    random_delay(0.3, 0.6)
        except Exception as e:
            log(f"Checkbox error: {e}")
        
        if is_github:
            driver.save_screenshot("screenshot_02_filled.png")
        
        # Submit form
        log("Submitting form...")
        random_delay(1, 3)
        click_submit_button(driver)
        random_delay(6, 10)
        
        if is_github:
            driver.save_screenshot("screenshot_03_submitted.png")
        
        # Check for CAPTCHA error first
        if check_for_captcha_error(driver):
            log("ERROR: reCAPTCHA showing 'Try again later' - IP likely flagged")
            if is_github:
                driver.save_screenshot("screenshot_04_captcha_blocked.png")
            log("Consider using a proxy or VPN")
        
        # Handle CAPTCHA
        captcha_attempts = 0
        while check_for_captcha(driver) and captcha_attempts < 3:
            log("CAPTCHA detected!")
            captcha_attempts += 1
            
            if click_audio_button(driver):
                log("Waiting for Buster (30s)...")
                time.sleep(30)
                
                if wait_for_captcha_solve(driver, timeout=10):
                    log("CAPTCHA solved!")
                    break
                else:
                    log("CAPTCHA still present")
            else:
                log("Could not click audio button - may be blocked")
                break
            
            if is_github:
                driver.save_screenshot(f"screenshot_04_captcha_{captcha_attempts}.png")
        
        # Final submit
        log("Final submission...")
        random_delay(2, 4)
        
        for i in range(3):
            if click_submit_button(driver, final=True):
                log(f"Final submit clicked (attempt {i+1})")
            random_delay(2, 4)
        
        random_delay(8, 12)
        
        if is_github:
            driver.save_screenshot("screenshot_05_final.png")
        
        # Check result
        url = driver.current_url
        page = driver.page_source.lower()
        
        success_indicators = ["welcome", "success", "verification", "dashboard", "account created", "confirm", "thank you"]
        failure_indicators = ["error", "invalid", "failed", "captcha", "robot", "try again", "automated"]
        
        has_success = any(x in page for x in success_indicators)
        has_failure = any(x in page for x in failure_indicators) or check_for_captcha_error(driver)
        still_on_form = "create" in url or "newaccount" in url
        
        success = has_success and not has_failure
        
        log("=" * 60)
        log("SUCCESS!" if success else "FAILED/UNCLEAR")
        log(f"URL: {url}")
        if has_success:
            log("Success indicators found")
        if has_failure:
            log("Failure indicators found")
        log("=" * 60)
        
        if is_github:
            with open("account_credentials.txt", "a") as f:
                f.write(f"URL: {url}\nStatus: {'SUCCESS' if success else 'FAILED/UNKNOWN'}\n")
        
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
    
