import os
import sys
import time
import random
import string
import tempfile
import subprocess
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def get_chrome_major_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version'], text=True)
        version_str = output.strip().split()[-1]
        major = int(version_str.split('.')[0])
        log(f"Detected Google Chrome Major Version: {major}")
        return major
    except Exception as e:
        log(f"Version detection failed: {e}. Defaulting to 150.")
        return 150

def generate_random_email():
    domains = ["1secmail.com", "1secmail.net", "1secmail.org"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{random.choice(domains)}"

def generate_strong_password():
    upper = random.choice(string.ascii_uppercase)
    lower = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice("!@#$%^&*-_=")
    remaining = ''.join(random.choice(string.ascii_letters + string.digits + "!@#$%^&*-_=") for _ in range(12))
    password = upper + lower + digit + special + remaining
    return ''.join(random.sample(password, len(password)))

def wait_for_element(driver, by, value, timeout=20):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    except:
        return None

def dismiss_cookie_banner(driver):
    """Detects and clicks 'Accept All' on cookie consent overlays/modals."""
    log("Checking for cookie consent banner...")
    cookie_selectors = [
        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept cookies')]",
        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow all')]",
        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
        "//button[@id='onetrust-accept-btn-handler']",
        "//button[contains(@id, 'cookie') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
        "//button[contains(@class, 'cookie') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]"
    ]
    for selector in cookie_selectors:
        try:
            btn = driver.find_element(By.XPATH, selector)
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                log(f"Clicked Cookie Accept button using selector: {selector}")
                time.sleep(2)
                return True
        except:
            continue
    log("No cookie banner found or already dismissed.")
    return False

def human_type(element, text):
    element.clear()
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))

def smart_fill_field(driver, element, text):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(random.uniform(0.3, 0.7))
        human_type(element, text)
        time.sleep(random.uniform(0.2, 0.5))
        if element.get_attribute("value") == text:
            return True
        driver.execute_script(f"arguments[0].value = '{text}';", element)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", element)
        return True
    except:
        return False

def click_submit_button(driver, final=False):
    selectors = [
        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create account')]",
        "//input[@type='submit']",
        "//button[@type='submit']",
        "//button[contains(@class, 'btn-primary')]"
    ]
    for selector in selectors:
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, selector))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(1)
            try:
                ActionChains(driver).move_to_element(btn).pause(random.uniform(0.2, 0.5)).click().perform()
            except:
                driver.execute_script("arguments[0].click();", btn)
            log(f"Submit button clicked using selector: {selector}")
            return True
        except:
            continue
    log("ERROR: Could not click any Create Account button!")
    return False

def solve_captcha_with_free_nopecha(driver, max_wait=45):
    log("Checking for CAPTCHA image challenge popup...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            challenge_frame = None
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                title = (iframe.get_attribute("title") or "").lower()
                if "recaptcha" in src and ("bframe" in src or "challenge" in src or "recaptcha challenge" in title):
                    if iframe.is_displayed():
                        challenge_frame = iframe
                        break
            
            if not challenge_frame:
                time.sleep(2)
                continue

            log("Challenge popup detected! Switching to challenge frame...")
            driver.switch_to.frame(challenge_frame)
            time.sleep(2)

            try:
                nopecha_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "solver-button"))
                )
                driver.execute_script("arguments[0].click();", nopecha_btn)
                log("Clicked NopeCHA visual solver button! Waiting for solution...")
            except:
                try:
                    alt_btn = driver.find_element(By.XPATH, "//*[contains(@class, 'nopecha') or contains(@title, 'Solve')]")
                    driver.execute_script("arguments[0].click();", alt_btn)
                    log("Clicked alternate NopeCHA solver button...")
                except:
                    log("NopeCHA button not found yet, waiting...")

            driver.switch_to.default_content()
            
            for _ in range(15):
                time.sleep(2)
                visible_challenges = [
                    f for f in driver.find_elements(By.TAG_NAME, "iframe")
                    if "bframe" in (f.get_attribute("src") or "") and f.is_displayed()
                ]
                if not visible_challenges:
                    log("CAPTCHA challenge cleared successfully!")
                    return True

        except Exception as e:
            driver.switch_to.default_content()
            time.sleep(2)

    log("CAPTCHA challenge wait completed.")
    return False

def create_proxy_auth_extension(proxy_str):
    try:
        clean_proxy = proxy_str.replace("http://", "").replace("https://", "").strip()
        if "@" in clean_proxy:
            auth, host_port = clean_proxy.split("@", 1)
            user, password = auth.split(":", 1)
            host, port = host_port.split(":", 1)
        elif clean_proxy.count(":") == 3:
            host, port, user, password = clean_proxy.split(":", 3)
        else:
            log("Proxy format unauthenticated or unrecognized.")
            return None
        
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
                    host: "{host.strip()}",
                    port: parseInt({port.strip()})
                  }},
                  bypassList: ["localhost"]
                }}
              }};

        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{user.strip()}",
                    password: "{password.strip()}"
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

def build_chrome_options():
    nopecha_path = os.environ.get('NOPECHA_PATH', '/opt/nopecha')
    proxy = os.environ.get('PROXY_URL')
    
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    extensions_to_load = []
    if proxy:
        proxy_ext_dir = create_proxy_auth_extension(proxy)
        if proxy_ext_dir:
            extensions_to_load.append(proxy_ext_dir)
            log("Authenticated Proxy Extension configured successfully.")
        else:
            clean_proxy = proxy.replace("http://", "").replace("https://", "").strip()
            if clean_proxy.count(":") == 1:
                options.add_argument(f'--proxy-server=http://{clean_proxy}')
                log(f"Unauthenticated Proxy argument added: {clean_proxy}")
    
    if os.path.exists(nopecha_path) and os.path.exists(f"{nopecha_path}/manifest.json"):
        extensions_to_load.append(nopecha_path)
        log("NopeCHA free-tier extension located")

    if extensions_to_load:
        options.add_argument(f"--load-extension={','.join(extensions_to_load)}")
        
    return options

def launch_driver():
    major_ver = get_chrome_major_version()
    log(f"Launching undetected-chromedriver with explicit version_main={major_ver}...")
    try:
        return uc.Chrome(options=build_chrome_options(), version_main=major_ver)
    except Exception as e:
        err_msg = str(e)
        log(f"Default launch failed: {err_msg}")
        match = re.search(r"Current browser version is (\d+)", err_msg)
        if match:
            major_ver = int(match.group(1))
            log(f"Detected mismatch! Forcing version_main={major_ver} to match browser...")
            try:
                return uc.Chrome(options=build_chrome_options(), version_main=major_ver)
            except Exception as e2:
                log(f"Retry with version_main={major_ver} failed: {e2}")
                return None
        return None

def navigate_via_affiliate_and_menu(driver):
    """Navigates to TARGET_URL first, clears cookies popup, then clicks My Account -> New Account."""
    log(f"Loading affiliate link: {TARGET_URL}")
    driver.get(TARGET_URL)
    time.sleep(5)
    
    # Dismiss cookie banner immediately upon loading affiliate site
    dismiss_cookie_banner(driver)
    time.sleep(2)
    
    # 1. Click 'My account' / Account icon in the top right
    log("Looking for 'My account' menu in top right...")
    account_selectors = [
        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'my account')]",
        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'my account')]",
        "//a[contains(@href, '/login') or contains(@href, '/account')]",
        "//*[contains(@class, 'account') or contains(@class, 'user')]/a"
    ]
    clicked_account = False
    for sel in account_selectors:
        try:
            btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, sel)))
            driver.execute_script("arguments[0].click();", btn)
            log(f"Clicked My Account menu using: {sel}")
            clicked_account = True
            time.sleep(3)
            dismiss_cookie_banner(driver)
            break
        except:
            continue
            
    if not clicked_account:
        log("WARNING: Could not click 'My account' menu directly. Continuing...")

    # 2. Click 'New account' / 'Create account' link
    log("Looking for 'New account' / 'Create account' option...")
    new_account_selectors = [
        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'new account')]",
        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create account')]",
        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign up')]",
        "//a[contains(@href, 'createNewAccount')]"
    ]
    for sel in new_account_selectors:
        try:
            btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, sel)))
            driver.execute_script("arguments[0].click();", btn)
            log(f"Clicked New Account option using: {sel}")
            time.sleep(3)
            dismiss_cookie_banner(driver)
            return True
        except:
            continue

    # Fallback if dropdown didn't open or link wasn't found
    log("Fallback: Directing to createNewAccount URL while keeping affiliate cookies...")
    driver.get("https://my.eurodns.com/login/createNewAccount")
    time.sleep(4)
    dismiss_cookie_banner(driver)
    return True

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
        # Navigate via Affiliate link -> Accept Cookies -> My account -> New account
        navigate_via_affiliate_and_menu(driver)
        
        log("Waiting for DOM to render...")
        email_field = None
        for wait_attempt in range(10):
            time.sleep(5)
            page_source = driver.page_source
            page_lower = page_source.lower()
            
            if "err_tunnel_connection_failed" in page_lower or "err_proxy_connection_failed" in page_lower or "net-error" in page_lower or "chrome://net-error" in page_lower:
                log("CRITICAL ERROR: Proxy authentication rejected or tunnel failed!")
                raise Exception("Proxy Authentication Failed or Bad Proxy IP.")
            
            if "just a moment" in driver.title.lower() or "challenge" in page_lower or "turnstile" in page_lower:
                log(f"[Wait {wait_attempt+1}/10] Cloudflare Challenge present, waiting for auto-resolution...")
                continue
            
            # Dismiss cookie banner again if present on registration page
            dismiss_cookie_banner(driver)
            
            for xpath in ["//input[@type='email']", "//input[contains(@name, 'email')]", "//input[contains(@id, 'email')]"]:
                email_field = wait_for_element(driver, By.XPATH, xpath, timeout=3)
                if email_field:
                    break
            
            if email_field:
                log("Registration form loaded successfully!")
                break
            else:
                log(f"[Wait {wait_attempt+1}/10] Form not visible yet. Refreshing page...")
                driver.refresh()
        
        log(f"Current Page Title: {driver.title}")
        log(f"Current URL: {driver.current_url}")
        
        if is_github:
            driver.save_screenshot("screenshot_01_loaded.png")
        
        if not email_field:
            raise Exception("Email field not found after retries. Proxy blocked or Cloudflare challenge did not clear.")
        
        log("Filling form with human delays...")
        smart_fill_field(driver, email_field, email)
        log("Email filled")
        time.sleep(random.uniform(1.0, 2.0))
        
        log("Looking for password fields...")
        pass_fields = driver.find_elements(By.XPATH, "//input[@type='password' or contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'password')]")
        
        if len(pass_fields) >= 1:
            smart_fill_field(driver, pass_fields[0], password)
            log("Primary password filled")
            time.sleep(random.uniform(0.5, 1.2))
            if len(pass_fields) >= 2:
                smart_fill_field(driver, pass_fields[1], password)
                log("Confirm password filled")
        else:
            log("WARNING: Could not find any password input fields!")
        
        try:
            for cb in driver.find_elements(By.XPATH, "//input[@type='checkbox']"):
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
        except:
            pass
        
        if is_github:
            driver.save_screenshot("screenshot_02_filled.png")
        
        # 1. Click Create Account FIRST to trigger the visual challenge
        log("Submitting form to trigger CAPTCHA challenge...")
        click_submit_button(driver)
        time.sleep(3)
        
        if is_github:
            driver.save_screenshot("screenshot_03_submitted.png")
        
        # 2. Handle the pop-up CAPTCHA image challenge
        log("Waiting for and solving pop-up CAPTCHA challenge...")
        solve_captcha_with_free_nopecha(driver, max_wait=45)
        time.sleep(3)
        
        if is_github:
            driver.save_screenshot("screenshot_04_captcha_solved.png")
        
        # 3. Check if final submission click is needed
        log("Checking if final submission click is needed...")
        for _ in range(2):
            if click_submit_button(driver, final=True):
                time.sleep(5)
                break
        
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
