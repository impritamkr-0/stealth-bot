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
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    pwd = ''.join(random.choice(chars) for _ in range(11))
    return pwd + "!"  # Ensure special char at end

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
    """Click audio button for Buster to solve"""
    log("Switching to audio CAPTCHA...")
    
    try:
        # Switch to CAPTCHA iframe
        iframe = driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
        driver.switch_to.frame(iframe)
        
        # Click audio button
        btn = driver.find_element(By.XPATH, "//button[@id='recaptcha-audio-button']")
        driver.execute_script("arguments[0].click();", btn)
        
        driver.switch_to.default_content()
        log("Audio button clicked")
        time.sleep(3)
        return True
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

def run_bot():
    log("=" * 60)
    log("EURODNS BOT STARTING")
    log("=" * 60)
    
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    # Generate credentials
    email = generate_random_email()
    password = generate_strong_password()
    
    log(f"Email: {email}")
    
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
    
    # Load Buster if available
    buster_path = os.environ.get('BUSTER_PATH', '/opt/buster')
    if os.path.exists(buster_path) and os.path.exists(f"{buster_path}/manifest.json"):
        options.add_argument(f"--load-extension={buster_path}")
        log("Buster loaded")
    
    # Get Chrome version and launch with matching driver
    chrome_version = get_chrome_version()
    
    log("Launching Chrome...")
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
            driver = uc.Chrome(options=options)  # Let it auto-detect
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
        
        # Fill form
        log("Filling form...")
        
        email_field = wait_for_element(driver, By.XPATH, "//input[@type='email']", timeout=15)
        if not email_field:
            raise Exception("Email field not found")
        
        smart_fill_field(driver, email_field, email)
        log("Email filled")
        
        time.sleep(1)
        
        pass_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
        if len(pass_fields) >= 2:
            smart_fill_field(driver, pass_fields[0], password)
            log("Password filled")
            time.sleep(0.5)
            smart_fill_field(driver, pass_fields[1], password)
            log("Confirm password filled")
        
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
