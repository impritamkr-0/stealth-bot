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

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def get_chrome_version():
    try:
        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True, timeout=5)
        version = int(result.stdout.strip().split()[-1].split('.')[0])
        return version
    except:
        return None

def generate_random_email():
    domains = ["1secmail.com", "1secmail.net", "1secmail.org"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{random.choice(domains)}"

def generate_strong_password():
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = ''.join(random.choice(chars) for _ in range(12))
    return pwd

def wait_for_element(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except:
        return None

def fill_field(driver, element, text):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        element.click()
        time.sleep(0.2)
        element.clear()
        element.send_keys(text)
        time.sleep(0.3)
        # Verify
        if element.get_attribute("value") == text:
            return True
        # Fallback
        driver.execute_script(f"arguments[0].value = '{text}';", element)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", element)
        return True
    except:
        return False

def click_submit(driver, final=False):
    selectors = ["//button[contains(text(), 'Create account')]", "//button[@type='submit']", "//button[contains(@class, 'btn-primary')]"]
    for sel in selectors:
        try:
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, sel)))
            driver.execute_script("arguments[0].click();", btn)
            log("Submit clicked")
            return True
        except:
            continue
    return False

def click_audio(driver):
    try:
        time.sleep(2)
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            if "recaptcha" in src and "bframe" in src:
                driver.switch_to.frame(iframe)
                time.sleep(1)
                try:
                    btn = driver.find_element(By.ID, "recaptcha-audio-button")
                    driver.execute_script("arguments[0].click();", btn)
                    log("Audio button clicked")
                    driver.switch_to.default_content()
                    return True
                except:
                    pass
                driver.switch_to.default_content()
        return False
    except Exception as e:
        log(f"Audio error: {e}")
        driver.switch_to.default_content()
        return False

def has_captcha(driver):
    return len(driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")) > 0

def create_driver():
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    proxy = os.environ.get('PROXY_URL', '')
    
    options = uc.ChromeOptions()
    
    if is_github:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
    
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    
    # Add proxy if provided (ip:port format only)
    if proxy and ":" in proxy:
        # Check if proxy has auth (ip:port:user:pass)
        parts = proxy.split(":")
        if len(parts) == 4:
            # Has auth - use ip:port only for Chrome, auth handled separately
            proxy_str = f"{parts[0]}:{parts[1]}"
        else:
            proxy_str = proxy
        options.add_argument(f'--proxy-server=http://{proxy_str}')
        log(f"Using proxy: {proxy_str}")
    
    # Load Buster
    buster = '/opt/buster'
    if os.path.exists(f"{buster}/manifest.json"):
        options.add_argument(f"--load-extension={buster}")
    
    # Get Chrome version and create driver
    chrome_ver = get_chrome_version()
    log(f"Chrome version: {chrome_ver}")
    
    try:
        if chrome_ver:
            return uc.Chrome(options=options, version_main=chrome_ver)
        return uc.Chrome(options=options)
    except Exception as e:
        log(f"Driver error: {e}")
        # Try without version
        return uc.Chrome(options=options)

def run_bot():
    log("=" * 60)
    log("EURODNS BOT STARTING")
    log("=" * 60)
    
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    email = generate_random_email()
    password = generate_strong_password()
    
    log(f"Email: {email}")
    log(f"Password: {'*' * len(password)}")
    
    if is_github:
        with open("account_credentials.txt", "w") as f:
            f.write(f"Email: {email}\nPassword: {password}\n")
    
    driver = None
    retries = 0
    max_retries = 3
    
    while retries < max_retries:
        try:
            log(f"Launching Chrome (attempt {retries + 1})...")
            driver = create_driver()
            break
        except Exception as e:
            log(f"Launch failed: {e}")
            retries += 1
            time.sleep(2)
    
    if not driver:
        log("Fatal: Could not launch Chrome")
        sys.exit(1)
    
    try:
        stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", 
                webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    except:
        pass
    
    try:
        log("Loading page...")
        driver.get("https://my.eurodns.com/login/createNewAccount")
        time.sleep(5)
        
        if is_github:
            driver.save_screenshot("screenshot_01.png")
        
        # Fill email
        email_field = wait_for_element(driver, By.XPATH, "//input[@type='email']", 15)
        if not email_field:
            raise Exception("Email field not found")
        
        fill_field(driver, email_field, email)
        log("Email filled")
        time.sleep(1)
        
        # Fill passwords
        pass_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
        if len(pass_fields) >= 2:
            fill_field(driver, pass_fields[0], password)
            log("Password filled")
            time.sleep(0.5)
            fill_field(driver, pass_fields[1], password)
            log("Confirm password filled")
        else:
            raise Exception("Password fields not found")
        
        # Checkboxes
        for cb in driver.find_elements(By.XPATH, "//input[@type='checkbox']"):
            try:
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.3)
            except:
                pass
        
        if is_github:
            driver.save_screenshot("screenshot_02.png")
        
        # Submit
        log("Submitting...")
        click_submit(driver)
        time.sleep(8)
        
        if is_github:
            driver.save_screenshot("screenshot_03.png")
        
        # Handle CAPTCHA
        if has_captcha(driver):
            log("CAPTCHA found, clicking audio...")
            if click_audio(driver):
                log("Waiting for Buster...")
                time.sleep(30)
        
        # Final submit
        time.sleep(3)
        click_submit(driver, final=True)
        time.sleep(10)
        
        if is_github:
            driver.save_screenshot("screenshot_04.png")
        
        url = driver.current_url
        success = "create" not in url
        
        log("=" * 60)
        log("SUCCESS!" if success else "CHECK SCREENSHOTS")
        log(f"URL: {url}")
        log("=" * 60)
        
        if is_github:
            with open("account_credentials.txt", "a") as f:
                f.write(f"URL: {url}\n")
        
    except Exception as e:
        log(f"ERROR: {e}")
        if is_github and driver:
            driver.save_screenshot("screenshot_error.png")
    finally:
        if driver:
            driver.quit()
        log("Done")

if __name__ == "__main__":
    run_bot()
