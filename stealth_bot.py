import os
import sys
import time
import random
import string
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"

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
    special = random.choice("!@#$%^&*")
    remaining = ''.join(random.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(8))
    password = upper + lower + digit + special + remaining
    password = ''.join(random.sample(password, len(password)))
    return password

def wait_for_element(driver, by, value, timeout=15):
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
        if element.get_attribute("value") == text:
            return True
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
            try:
                btn = driver.find_element(By.ID, "recaptcha-audio-button")
                driver.execute_script("arguments[0].click();", btn)
                log("Audio button clicked")
                driver.switch_to.default_content()
                return True
            except:
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

def create_proxy_auth_extension(proxy_str):
    """Creates a temporary Chrome extension to authenticate proxies automatically."""
    try:
        clean_proxy = proxy_str.replace("http://", "").replace("https://", "")
        if "@" not in clean_proxy:
            return None
        
        auth, host_port = clean_proxy.split("@", 1)
        user, password = auth.split(":", 1)
        host, port = host_port.split(":", 1)
        
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = f"""
        var config = {{
                mode: "fixed_servers",
                rules: {{
                  singleProxy: {{
                    scheme: "http",
                    host: "{host}",
                    port: parseInt({port})
                  }},
                  bypassList: ["localhost"]
                }}
              }};

        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{user}",
                    password: "{password}"
                }}
            }};
        }}

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {{urls: ["<all_urls>"]}},
                    ['blocking']
        );
        """
        ext_dir = tempfile.mkdtemp()
        with open(os.path.join(ext_dir, "manifest.json"), "w") as f:
            f.write(manifest_json)
        with open(os.path.join(ext_dir, "background.js"), "w") as f:
            f.write(background_js)
        return ext_dir
    except Exception as e:
        log(f"Failed to build proxy extension: {e}")
        return None

def launch_driver():
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    buster_path = os.environ.get('BUSTER_PATH', '/opt/buster')
    proxy = os.environ.get('PROXY_URL')
    
    options = Options()
    
    # Hide automation banners and automation flags
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    if is_github:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
    
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    
    # Handle authenticated Webshare proxy via extension
    extensions_to_load = []
    if proxy:
        proxy_ext_dir = create_proxy_auth_extension(proxy)
        if proxy_ext_dir:
            extensions_to_load.append(proxy_ext_dir)
            log("Authenticated Proxy Extension configured")
        else:
            clean_proxy = proxy.replace("http://", "").replace("https://", "")
            options.add_argument(f'--proxy-server=http://{clean_proxy}')
            log(f"Unauthenticated Proxy argument added: {clean_proxy}")
    
    if os.path.exists(buster_path) and os.path.exists(f"{buster_path}/manifest.json"):
        extensions_to_load.append(buster_path)
        log("Buster extension located")

    if extensions_to_load:
        options.add_argument(f"--load-extension={','.join(extensions_to_load)}")
    
    log("Launching Chrome using Selenium Manager (Auto-matching driver)...")
    try:
        # Standard Selenium driver handles driver matching automatically!
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        log(f"Launch error: {e}")
        return None

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
    for attempt in range(3):
        try:
            log(f"Launch attempt {attempt + 1}...")
            driver = launch_driver()
            if driver:
                log("Chrome launched successfully")
                break
        except Exception as e:
            log(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    
    if not driver:
        log("Fatal: Could not launch Chrome")
        sys.exit(1)
    
    try:
        # Apply selenium-stealth to mask headless Selenium detection
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    except Exception as e:
        log(f"Stealth warning: {e}")
    
    driver.implicitly_wait(5)
    
    try:
        log("Loading registration page...")
        driver.get("https://my.eurodns.com/login/createNewAccount")
        
        body = wait_for_element(driver, By.TAG_NAME, "body", timeout=20)
        time.sleep(5)
        
        log(f"Current Page Title: {driver.title}")
        log(f"Current URL: {driver.current_url}")
        
        if is_github:
            driver.save_screenshot("screenshot_01_loaded.png")
        
        log("Filling form...")
        email_field = wait_for_element(driver, By.XPATH, "//input[@type='email']", timeout=20)
        if not email_field:
            raise Exception("Email field not found. Proxy might be blocked or page failed to load.")
        
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
        else:
            log(f"Warning: Found {len(pass_fields)} password field(s)")
        
        try:
            for cb in driver.find_elements(By.XPATH, "//input[@type='checkbox']"):
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
        except:
            pass
        
        if is_github:
            driver.save_screenshot("screenshot_02_filled.png")
        
        log("Submitting form...")
        click_submit_button(driver)
        time.sleep(8)
        
        if is_github:
            driver.save_screenshot("screenshot_03_submitted.png")
        
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
