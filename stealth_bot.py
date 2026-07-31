import os
import sys
import subprocess
import time
import random
import string
import zipfile
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def create_proxy_extension(proxy_url, save_path="/tmp/proxy_auth_extension"):
    """
    Create a Chrome extension to handle proxy authentication
    proxy_url format: ip:port:username:password
    """
    try:
        parts = proxy_url.split(":")
        if len(parts) != 4:
            log(f"Invalid proxy format. Expected ip:port:user:pass, got: {proxy_url}")
            return None
        
        proxy_ip = parts[0]
        proxy_port = parts[1]
        proxy_user = parts[2]
        proxy_pass = parts[3]
        
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
            host: "{proxy_ip}",
            port: parseInt({proxy_port})
          }},
          bypassList: ["localhost"]
        }}
      }};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

function callbackFn(details) {{
    return {{
        authCredentials: {{
            username: "{proxy_user}",
            password: "{proxy_pass}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
);
"""
        
        # Create extension directory
        os.makedirs(save_path, exist_ok=True)
        
        # Write files
        with open(os.path.join(save_path, "manifest.json"), "w") as f:
            f.write(manifest_json)
        
        with open(os.path.join(save_path, "background.js"), "w") as f:
            f.write(background_js)
        
        # Create zip
        zip_path = f"{save_path}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(os.path.join(save_path, "manifest.json"), "manifest.json")
            zipf.write(os.path.join(save_path, "background.js"), "background.js")
        
        log(f"Proxy extension created at {zip_path}")
        return zip_path
        
    except Exception as e:
        log(f"Failed to create proxy extension: {e}")
        return None

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
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            element.click()
            time.sleep(0.3)
            element.clear()
            time.sleep(0.2)
            element.send_keys("\u0003")
            element.send_keys("\u0008")
            time.sleep(0.2)
            element.send_keys(text)
            time.sleep(0.5)
            driver.execute_script("""
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('blur', {bubbles: true}));
            """, element)
            actual_value = element.get_attribute("value")
            if actual_value == text:
                log(f"{field_name} filled successfully ({len(text)} chars)")
                return True
            else:
                log(f"{field_name} verification failed")
                driver.execute_script(f"arguments[0].value = '{text}';", element)
                driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                """, element)
                actual_value = element.get_attribute("value")
                if actual_value == text:
                    log(f"{field_name} filled via JavaScript")
                    return True
        except Exception as e:
            log(f"{field_name} fill attempt {attempt + 1} failed: {e}")
            time.sleep(0.5)
    log(f"Failed to fill {field_name}")
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
                "//button[contains(@class, 'rc-button-audio')]",
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
        proxy_url = os.environ.get('PROXY_URL')
        
        if is_github:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
        
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        
        extensions = []
        
        # Add proxy extension if proxy is configured
        if proxy_url and ":" in proxy_url:
            proxy_ext = create_proxy_extension(proxy_url)
            if proxy_ext:
                extensions.append(proxy_ext)
                log(f"Proxy extension added")
        
        # Add Buster extension
        if os.path.exists(buster_path) and os.path.exists(f"{buster_path}/manifest.json"):
            extensions.append(buster_path)
            log("Buster loaded")
        
        # Load all extensions
        if extensions:
            options.add_argument(f"--load-extension={','.join(extensions)}")
        
        try:
            log("Trying auto-detection...")
            driver = uc.Chrome(options=options)
            log("Chrome launched successfully")
            return driver
        except Exception as e:
            log(f"Auto-detection failed: {e}")
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
        
        email_field = wait_for_element(driver, By.XPATH, "//input[@type='email']", timeout=15)
        if not email_field:
            raise Exception("Email field not found")
        
        fill_field_robust(driver, email_field, email, "Email")
        time.sleep(1)
        
        pass_fields = []
        selectors = [
            "//input[@type='password']",
            "//input[@name='password']",
            "//input[@id='password']",
            "//input[contains(@name, 'password')]",
        ]
        for selector in selectors:
            pass_fields = driver.find_elements(By.XPATH, selector)
            if len(pass_fields) >= 2:
                log(f"Found {len(pass_fields)} password fields")
                break
        
        if len(pass_fields) < 2:
            pass_fields = driver.find_elements(By.TAG_NAME, "input")
            pass_fields = [f for f in pass_fields if f.get_attribute("type") == "password"]
        
        if len(pass_fields) >= 2:
            fill_field_robust(driver, pass_fields[0], password, "Password")
            time.sleep(0.5)
            fill_field_robust(driver, pass_fields[1], password, "Confirm Password")
        else:
            raise Exception("Password fields not found")
        
        try:
            checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
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
    finally:
        log("Closing browser...")
        try:
            driver.quit()
        except:
            pass
        log("Done")

if __name__ == "__main__":
    run_bot()
