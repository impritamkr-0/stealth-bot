import os
import sys
import time
import random
import string
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def generate_random_email():
    try:
        domains = ["1secmail.com", "1secmail.net", "1secmail.org"]
        domain = random.choice(domains)
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        return f"{username}@{domain}", "TempPass123!"
    except:
        timestamp = str(int(time.time()))[-6:]
        return f"user{timestamp}@mailinator.com", "TempPass123!"

def generate_strong_password():
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    password_chars = [
        random.choice(uppercase),
        random.choice(lowercase),
        random.choice(digits),
        random.choice(special)
    ]
    
    all_chars = uppercase + lowercase + digits + special
    for _ in range(8):
        password_chars.append(random.choice(all_chars))
    
    random.shuffle(password_chars)
    return ''.join(password_chars)

def wait_for_element(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except Exception as e:
        log(f"Element not found: {value} - {e}")
        return None

def smart_fill_field(driver, element, text):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        element.clear()
        element.send_keys(text)
        time.sleep(0.5)
        return True
    except:
        try:
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
    ]
    
    if final:
        selectors = ["//button[contains(text(), 'Create account')]"] + selectors
    
    for selector in selectors:
        try:
            by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((by, selector)))
            driver.execute_script("arguments[0].click();", btn)
            log("Submit button clicked")
            return True
        except:
            continue
    
    try:
        driver.execute_script("document.querySelector('form').submit();")
        return True
    except:
        pass
    return False

def click_audio_button(driver):
    log("Looking for audio button...")
    
    # Try to switch to CAPTCHA iframe first
    try:
        captcha_iframe = driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
        driver.switch_to.frame(captcha_iframe)
        log("Switched to CAPTCHA iframe")
    except:
        log("No CAPTCHA iframe found or already inside")
    
    # Now look for audio button
    selectors = [
        "//button[@id='recaptcha-audio-button']",
        "//button[@title='Get an audio challenge']",
        "//button[@aria-label='Get an audio challenge']",
        "//button[contains(@class, 'audio')]",
        "//div[@class='rc-button-audio']",
        "//button[.//span[contains(text(), 'audio')]]",
    ]
    
    for selector in selectors:
        try:
            btn = driver.find_element(By.XPATH, selector)
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                log("Audio button clicked")
                time.sleep(3)
                
                # Switch back to main content
                driver.switch_to.default_content()
                return True
        except:
            continue
    
    # JavaScript fallback
    try:
        result = driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for(var i=0; i<btns.length; i++) {
                var title = btns[i].getAttribute('title') || '';
                var aria = btns[i].getAttribute('aria-label') || '';
                if(title.includes('audio') || aria.includes('audio')) {
                    btns[i].click();
                    return 'clicked';
                }
            }
            return 'not found';
        """)
        driver.switch_to.default_content()
        if result == 'clicked':
            log("Audio button clicked via JS")
            time.sleep(3)
            return True
    except:
        driver.switch_to.default_content()
    
    return False

def check_for_captcha(driver):
    try:
        iframes = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
        if len(iframes) > 0:
            return True
        page_source = driver.page_source.lower()
        return 'recaptcha' in page_source
    except:
        return False

def run_bot():
    log("=" * 60)
    log("EURODNS BOT STARTING")
    log("=" * 60)
    
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    log(f"Environment: {'GitHub Actions' if is_github else 'Local'}")
    
    # Generate credentials
    log("Generating credentials...")
    email, _ = generate_random_email()
    password = generate_strong_password()
    log(f"Email: {email}")
    
    # Save credentials immediately in case of crash
    if is_github:
        with open("account_credentials.txt", "w") as f:
            f.write(f"Email: {email}\nPassword: {password}\n")
    
    # Setup Chrome
    log("Setting up Chrome...")
    options = uc.ChromeOptions()
    
    if is_github:
        log("Configuring headless mode...")
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Load Buster extension
    buster_path = os.environ.get('BUSTER_PATH', '/opt/buster')
    if os.path.exists(buster_path):
        log(f"Loading Buster from: {buster_path}")
        options.add_argument(f"--load-extension={buster_path}")
        
        # List extension files for debugging
        try:
            import subprocess
            result = subprocess.run(['ls', '-la', buster_path], capture_output=True, text=True)
            log(f"Extension files:\n{result.stdout}")
        except:
            pass
    else:
        log(f"WARNING: Buster not found at {buster_path}")
    
    # Launch browser
    log("Launching Chrome...")
    try:
        driver = uc.Chrome(options=options)
        log("Chrome launched successfully")
    except Exception as e:
        log(f"CRITICAL: Chrome failed to launch: {e}")
        # Try with fewer options
        try:
            log("Retrying with minimal options...")
            options = uc.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            driver = uc.Chrome(options=options)
        except Exception as e2:
            log(f"FATAL: Chrome retry failed: {e2}")
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
        log("Stealth applied")
    except Exception as e:
        log(f"Stealth warning: {e}")
    
    driver.implicitly_wait(10)
    
    try:
        log("Loading website...")
        driver.get(TARGET_URL)
        time.sleep(5)
        
        if is_github:
            driver.save_screenshot("screenshot_01_start.png")
            log("Screenshot saved: screenshot_01_start.png")
        
        # Check if page loaded
        if "eurodns" not in driver.page_source.lower():
            log("WARNING: Page may not have loaded correctly")
        
        # Accept cookies
        log("Handling cookies...")
        try:
            for selector in ["#onetrust-accept-btn-handler", "//button[contains(text(), 'ACCEPT')]"]:
                try:
                    by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
                    btn = driver.find_element(by, selector)
                    btn.click()
                    log("Cookies accepted")
                    time.sleep(2)
                    break
                except:
                    continue
        except:
            pass
        
        # Navigate to registration
        log("Navigating to registration...")
        driver.get("https://my.eurodns.com/login/createNewAccount")
        time.sleep(5)
        
        if is_github:
            driver.save_screenshot("screenshot_02_form.png")
        
        # Check if form loaded
        email_field = wait_for_element(driver, By.XPATH, "//input[@type='email']", timeout=15)
        if not email_field:
            log("ERROR: Email field not found!")
            driver.save_screenshot("screenshot_error_no_form.png")
            sys.exit(1)
        
        log("Filling form...")
        smart_fill_field(driver, email_field, email)
        log("Email filled")
        
        time.sleep(2)
        
        pass_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
        log(f"Found {len(pass_fields)} password fields")
        
        if len(pass_fields) >= 2:
            smart_fill_field(driver, pass_fields[0], password)
            log("Password filled")
            time.sleep(1)
            smart_fill_field(driver, pass_fields[1], password)
            log("Confirm password filled")
        
        # Checkboxes
        try:
            checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            for cb in checkboxes:
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
            log("Checkboxes handled")
        except:
            pass
        
        time.sleep(2)
        
        # Submit form
        log("Submitting form...")
        click_submit_button(driver)
        time.sleep(8)
        
        if is_github:
            driver.save_screenshot("screenshot_03_after_submit.png")
        
        # Handle CAPTCHA
        if check_for_captcha(driver):
            log("CAPTCHA detected!")
            
            if click_audio_button(driver):
                log("Switched to audio challenge")
                log("Waiting 30 seconds for Buster to solve...")
                time.sleep(30)
                
                # Check if solved
                if not check_for_captcha(driver):
                    log("CAPTCHA appears solved!")
                else:
                    log("CAPTCHA still present, waiting more...")
                    time.sleep(20)
            else:
                log("Could not click audio button")
            
            if is_github:
                driver.save_screenshot("screenshot_04_captcha.png")
        
        # Final submit
        log("Final submission...")
        time.sleep(3)
        
        for attempt in range(3):
            if click_submit_button(driver, final=True):
                log(f"Final submit clicked (attempt {attempt+1})")
                break
            time.sleep(2)
        
        time.sleep(10)
        
        if is_github:
            driver.save_screenshot("screenshot_05_final.png")
        
        # Check result
        current_url = driver.current_url
        page_source = driver.page_source.lower()
        
        success_indicators = ["welcome", "success", "dashboard", "verification", "confirm", "thank you"]
        success = any(ind in page_source for ind in success_indicators) or "login" not in current_url
        
        log("=" * 60)
        if success:
            log("✓ REGISTRATION SUCCESSFUL")
        else:
            log("? STATUS UNCLEAR")
            log(f"Current URL: {current_url}")
        log("=" * 60)
        
        # Save final credentials
        if is_github:
            with open("account_credentials.txt", "w") as f:
                f.write(f"Email: {email}\n")
                f.write(f"Password: {password}\n")
                f.write(f"URL: {current_url}\n")
                f.write(f"Status: {'SUCCESS' if success else 'UNKNOWN'}\n")
        
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        if is_github:
            try:
                driver.save_screenshot("screenshot_error.png")
            except:
                pass
        sys.exit(1)
    finally:
        log("Closing browser...")
        try:
            driver.quit()
        except:
            pass
        log("Done")

if __name__ == "__main__":
    run_bot()
