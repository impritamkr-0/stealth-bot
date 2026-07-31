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
    except Exception as e:
        log(f"Could not detect Chrome version: {e}")
        return None

def generate_random_email():
    domains = ["1secmail.com", "1secmail.net", "1secmail.org"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{random.choice(domains)}"

def generate_strong_password():
    """Generate password meeting requirements: min 8 chars, upper, lower, number, special"""
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

def wait_for_element(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    except:
        return None

def fill_field_robust(driver, element, text, field_name="field"):
    """Robustly fill a field with verification"""
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # Click to focus
            element.click()
            time.sleep(0.3)
            
            # Clear field thoroughly
            element.clear()
            time.sleep(0.2)
            
            # Select all and delete (extra clear)
            element.send_keys("\u0003")  # Ctrl+A
            element.send_keys("\u0008")  # Backspace
            time.sleep(0.2)
            
            # Type the text
            element.send_keys(text)
            time.sleep(0.5)
            
            # Trigger input events
            driver.execute_script("""
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('blur', {bubbles: true}));
            """, element)
            
            # Verify the value was set
            actual_value = element.get_attribute("value")
            if actual_value == text:
                log(f"{field_name} filled successfully ({len(text)} chars)")
                return True
            else:
                log(f"{field_name} verification failed: expected {len(text)} chars, got {len(actual_value)}")
                
                # Try JavaScript injection as fallback
                driver.execute_script(f"arguments[0].value = '{text}';", element)
                driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                """, element)
                
                # Verify again
                actual_value = element.get_attribute("value")
                if actual_value == text:
                    log(f"{field_name} filled via JavaScript")
                    return True
                    
        except Exception as e:
            log(f"{field_name} fill attempt {attempt + 1} failed: {e}")
            time.sleep(0.5)
    
    log(f"Failed to fill {field_name} after {max_attempts} attempts")
    return False

def click_submit_button(driver, final=False):
    selectors = [
        "//button[contains(text(), 'Create account')]",
        "//button[contains(text(), 'Create Account')]",
        "//button[@type='submit']",
        "//button[contains(@class, 'btn-primary')]",
        "//input[@type='submit']",
    ]
    
    if final:
        selectors = ["//button[contains(text(), 'Create account')]"] + selectors
    
    for selector in selectors:
        try:
            by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((by, selector))
            )
            driver.execute_script("arguments[0].click();", btn)
            log("Submit clicked")
            return True
        except:
            continue
    
    try:
        driver.execute_script("""
            var btns = document.querySelectorAll('button[type="submit"]');
            if(btns.length > 0) btns[0].click();
        """)
        return True
    except:
        pass
    return False

def click_audio_button(driver):
    log("Switching to audio CAPTCHA...")
    
    try:
        time.sleep(2)
        
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
            time.sleep(1)
            
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
            
            try:
                driver.execute_script("""
                    var btn = document.querySelector('#recaptcha-audio-button, .rc-button-audio');
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

def launch_driver_with_retry(max_retries=3):
    driver = None
    
    for attempt in range(max_retries):
        log(f"Launch attempt {attempt + 1}/{max_retries}...")
        
        options = uc.ChromeOptions()
        is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
        buster_path = os.environ.get('BUSTER_PATH', '/opt/buster')
        
        if is_github:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
        
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        
        # Add proxy if configured
        proxy = os.environ.get('PROXY_URL')
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
            log(f"Using proxy: {proxy}")
        
        if os.path.exists(buster_path) and os.path.exists(f"{buster_path}/manifest.json"):
            options.add_argument(f"--load-extension={buster_path}")
            log("Buster loaded")
        
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
                        options = uc.ChromeOptions()
                        if is_github:
                            options.add_argument("--headless=new")
                            options.add_argument("--no-sandbox")
                            options.add_argument("--disable-dev-shm-usage")
                            options.add_argument("--disable-gpu")
                        options.add_argument("--window-size=1920,1080")
                        options.add_argument("--disable-notifications")
                        if proxy:
                            options.add_argument(f'--proxy-server={proxy}')
                        if os.path.exists(buster_path):
                            options.add_argument(f"--load-extension={buster_path}")
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
        time.sleep(5)
        
        if is_github:
            driver.save_screenshot("screenshot_01_loaded.png")
        
        log("Filling form...")
        
        # Fill email
        email_field = wait_for_element(driver, By.XPATH, "//input[@type='email']", timeout=15)
        if not email_field:
            raise Exception("Email field not found")
        
        fill_field_robust(driver, email_field, email, "Email")
        time.sleep(1)
        
        # Find password fields with multiple selectors
        pass_fields = []
        
        # Try multiple approaches to find password fields
        selectors = [
            "//input[@type='password']",
            "//input[@name='password']",
            "//input[@id='password']",
            "//input[contains(@name, 'password')]",
            "//input[contains(@id, 'password')]",
        ]
        
        for selector in selectors:
            pass_fields = driver.find_elements(By.XPATH, selector)
            if len(pass_fields) >= 2:
                log(f"Found {len(pass_fields)} password fields with: {selector}")
                break
        
        # If still not found, try broader search
        if len(pass_fields) < 2:
            pass_fields = driver.find_elements(By.TAG_NAME, "input")
            pass_fields = [f for f in pass_fields if f.get_attribute("type") == "password"]
            log(f"Found {len(pass_fields)} password fields by tag filtering")
        
        if len(pass_fields) >= 2:
            # Fill password with verification
            success1 = fill_field_robust(driver, pass_fields[0], password, "Password")
            time.sleep(0.5)
            success2 = fill_field_robust(driver, pass_fields[1], password, "Confirm Password")
            
            if not (success1 and success2):
                log("WARNING: Password fields may not be filled correctly")
        else:
            log(f"ERROR: Only found {len(pass_fields)} password field(s)")
            raise Exception("Password fields not found")
        
        # Handle checkboxes
        try:
            checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            log(f"Found {len(checkboxes)} checkboxes")
            for i, cb in enumerate(checkboxes):
                try:
                    if not cb.is_selected():
                        driver.execute_script("arguments[0].click();", cb)
                        log(f"Clicked checkbox {i+1}")
                        time.sleep(0.3)
                except:
                    pass
        except Exception as e:
            log(f"Checkbox error: {e}")
        
        if is_github:
            driver.save_screenshot("screenshot_02_filled.png")
        
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
