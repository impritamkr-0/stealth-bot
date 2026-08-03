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
from selenium_stealth import stealth

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"
# The official Chrome Web Store ID for NopeCHA
NOPECHA_EXT_ID = "dknlfmjaanfblgfdfebhijalfmhmjjjo"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def get_chrome_major_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version'], text=True)
        version_str = output.strip().split()[-1]
        major = int(version_str.split('.')[0])
        log(f"Detected Chrome Version: {major}")
        return major
    except:
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

def wait_for_cloudflare_clear(driver, max_wait=30):
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if "just a moment" in driver.title.lower() or "cf-challenge" in driver.page_source.lower() or "turnstile" in driver.page_source.lower():
            time.sleep(2)
        else:
            log("Cloudflare cleared.")
            return True
    return False

def fast_human_type(element, text):
    element.clear()
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.01, 0.05))

def smart_fill_field(driver, element, text):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.1)
        fast_human_type(element, text)
        time.sleep(0.1)
        if element.get_attribute("value") != text:
            driver.execute_script(f"arguments[0].value = '{text}';", element)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", element)
        return True
    except:
        return False

def solve_captcha_with_free_nopecha(driver, max_wait=60):
    log("Checking for CAPTCHA image challenge popup...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            challenge_frame = None
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "recaptcha" in src and ("bframe" in src or "challenge" in src):
                    if iframe.is_displayed():
                        challenge_frame = iframe
                        break
            
            if not challenge_frame:
                time.sleep(2)
                continue

            log("Challenge popup detected! Switching to frame...")
            driver.switch_to.frame(challenge_frame)
            time.sleep(2)

            # 1. Trigger NopeCHA solver
            try:
                # NopeCHA dynamically injects a button with these classes
                nopecha_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'nopecha') or contains(@id, 'nopecha')]"))
                )
                driver.execute_script("arguments[0].click();", nopecha_btn)
                log("Clicked NopeCHA visual solver button! Waiting for AI to finish...")
            except Exception as e:
                log("Could not find NopeCHA button. It may be solving automatically.")

            driver.switch_to.default_content()
            
            # 2. Sit patiently and wait for the AI to solve it (NO SPAM CLICKING)
            for _ in range(30):
                time.sleep(2)
                visible_challenges = [
                    f for f in driver.find_elements(By.TAG_NAME, "iframe")
                    if "bframe" in (f.get_attribute("src") or "") and f.is_displayed()
                ]
                if not visible_challenges:
                    log("CAPTCHA cleared successfully by NopeCHA!")
                    return True
        except:
            driver.switch_to.default_content()
            time.sleep(2)
            
    log("CAPTCHA challenge wait completed/timed out.")
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
            return None
        
        manifest_json = """
        {
            "version": "1.0.0", "manifest_version": 2, "name": "Chrome Proxy",
            "permissions": ["proxy", "tabs", "unlimitedStorage", "storage", "<all_urls>", "webRequest", "webRequestBlocking"],
            "background": {"scripts": ["background.js"]},
            "minimum_chrome_version":"22.0.0"
        }
        """
        background_js = f"""
        var config = {{mode: "fixed_servers", rules: {{singleProxy: {{scheme: "http", host: "{host.strip()}", port: parseInt({port.strip()}) }}, bypassList: ["localhost"] }}}};
        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
        function callbackFn(details) {{return {{authCredentials: {{username: "{user.strip()}", password: "{password.strip()}"}}}};}}
        chrome.webRequest.onAuthRequired.addListener(callbackFn, {{urls: ["<all_urls>"]}}, ['blocking']);
        """
        ext_dir = tempfile.mkdtemp()
        with open(os.path.join(ext_dir, "manifest.json"), "w") as f: f.write(manifest_json)
        with open(os.path.join(ext_dir, "background.js"), "w") as f: f.write(background_js)
        return ext_dir
    except:
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
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    extensions_to_load = []
    if proxy:
        proxy_ext_dir = create_proxy_auth_extension(proxy)
        if proxy_ext_dir:
            extensions_to_load.append(proxy_ext_dir)
        else:
            clean_proxy = proxy.replace("http://", "").replace("https://", "").strip()
            if clean_proxy.count(":") == 1: options.add_argument(f'--proxy-server=http://{clean_proxy}')
            
    if os.path.exists(nopecha_path) and os.path.exists(f"{nopecha_path}/manifest.json"):
        extensions_to_load.append(nopecha_path)

    if extensions_to_load:
        options.add_argument(f"--load-extension={','.join(extensions_to_load)}")
    return options

def launch_driver():
    major_ver = get_chrome_major_version()
    try:
        return uc.Chrome(options=build_chrome_options(), version_main=major_ver)
    except Exception as e:
        match = re.search(r"Current browser version is (\d+)", str(e))
        if match:
            return uc.Chrome(options=build_chrome_options(), version_main=int(match.group(1)))
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
    
    driver = None
    for attempt in range(3):
        driver = launch_driver()
        if driver: break
        time.sleep(2)
    
    if not driver: sys.exit(1)
    
    try:
        stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    except: pass
    
    driver.implicitly_wait(5)
    
    try:
        # WAKE UP AND ACTIVATE NOPECHA EXTENSION
        log("Activating NopeCHA Extension settings...")
        try:
            driver.get(f"chrome-extension://{NOPECHA_EXT_ID}/setup.html")
            time.sleep(3)
            log("NopeCHA successfully initialized and permitted.")
        except Exception as e:
            log("Could not load NopeCHA settings. It may not be loaded properly.")

        # 1. Open URL & Handle Cloudflare
        log(f"Loading affiliate link: {TARGET_URL}")
        driver.get(TARGET_URL)
        wait_for_cloudflare_clear(driver, max_wait=30)
        time.sleep(3)

        # 2. Accept Cookies
        log("Looking for Accept Cookies button...")
        try:
            cookie_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="cookiescript_accept"]')))
            driver.execute_script("arguments[0].click();", cookie_btn)
            log("Clicked Accept Cookies.")
            time.sleep(random.uniform(2.0, 5.0))
        except Exception as e:
            log("Cookie button not found or already accepted.")

        if is_github: driver.save_screenshot("screenshot_01_loaded.png")

        # 3. Click My Account
        log("Clicking 'My account'...")
        try:
            my_acc = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="account-item-logout"]')))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", my_acc)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", my_acc)
            log("Clicked My Account.")
            time.sleep(2)
        except Exception as e:
            log(f"Failed to click My Account: {e}")

        # 4. Click New Account
        log("Clicking 'New account'...")
        try:
            new_acc = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="logout-user-section"]/a[2]')))
            driver.execute_script("arguments[0].click();", new_acc)
            log("Clicked New Account. Waiting 5 seconds for form...")
            time.sleep(5)
        except Exception as e:
            log(f"Failed to click New Account: {e}")

        # 5. Fill Form
        log("Filling Email and Password...")
        email_fields = driver.find_elements(By.XPATH, "//input[@type='email']")
        if email_fields:
            smart_fill_field(driver, email_fields[0], email)
        
        pass_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
        if len(pass_fields) >= 1:
            smart_fill_field(driver, pass_fields[0], password)
            time.sleep(0.5)
            if len(pass_fields) >= 2:
                smart_fill_field(driver, pass_fields[1], password)

        # 6. Click Small Checkbox
        log("Checking the newsletter/terms checkbox...")
        try:
            checkbox = driver.find_element(By.XPATH, '//*[@id="subscribe-newsletter-checkbox-input"]')
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
            time.sleep(0.5)
            if not checkbox.is_selected():
                driver.execute_script("arguments[0].click();", checkbox)
                log("Checkbox checked.")
        except Exception as e:
            log("Checkbox not found or failed to click.")

        if is_github: driver.save_screenshot("screenshot_02_filled.png")

        # 7. Click Create Account Button
        log("Clicking exact Create Account button...")
        try:
            submit_xpath = '/html/body/edns-root/edns-layout/div/div/edns-side-panels/mat-sidenav-container/mat-sidenav-content/div/div[2]/edns-new-account/div/div/form/div[4]/button/span[2]'
            submit_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, submit_xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", submit_btn)
            log("Submit button clicked!")
        except Exception as e:
            log(f"Failed to click exact Submit Button. Error: {e}")

        time.sleep(4)
        if is_github: driver.save_screenshot("screenshot_03_submitted.png")

        # 8. Solve CAPTCHA
        log("Waiting for and solving pop-up CAPTCHA challenge...")
        solve_captcha_with_free_nopecha(driver, max_wait=60)
        
        time.sleep(8)
        if is_github: driver.save_screenshot("screenshot_04_final.png")
        
        # 9. Verify Success
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
        import traceback
        log(traceback.format_exc())
        if is_github: driver.save_screenshot("screenshot_error.png")
        sys.exit(1)
    finally:
        log("Closing browser...")
        try: driver.quit()
        except: pass
        log("Done")

if __name__ == "__main__":
    run_bot()
