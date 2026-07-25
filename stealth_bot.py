import os
import sys
import platform
import subprocess
import re
import time
import random
import string
import requests

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth

TARGET_URL = "https://cinderos.sjv.io/jR2ZJ0"

def get_installed_chrome_version():
    """Detects the installed Google Chrome major version across Windows, Linux, and macOS."""
    os_name = platform.system()
    version_str = None

    try:
        if os_name == "Windows":
            import winreg
            reg_paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome")
            ]
            for root, path in reg_paths:
                try:
                    with winreg.OpenKey(root, path) as key:
                        val, _ = winreg.QueryValueEx(key, "version" if "BLBeacon" in path else "DisplayVersion")
                        if val:
                            version_str = val
                            break
                except FileNotFoundError:
                    continue

        elif os_name == "Linux":
            for binary in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
                try:
                    output = subprocess.check_output([binary, "--version"], stderr=subprocess.STDOUT).decode("utf-8")
                    match = re.search(r"\d+\.\d+\.\d+\.\d+", output)
                    if match:
                        version_str = match.group(0)
                        break
                except Exception:
                    continue

        elif os_name == "Darwin": # macOS
            output = subprocess.check_output(
                ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"]
            ).decode("utf-8")
            match = re.search(r"\d+\.\d+\.\d+\.\d+", output)
            if match:
                version_str = match.group(0)

        if version_str:
            major_version = int(version_str.split(".")[0])
            print(f"Detected Chrome major version: {major_version} (Full: {version_str})")
            return major_version

    except Exception as e:
        print(f"Could not auto-detect Chrome version: {e}")

    print("Falling back to default undetected-chromedriver version resolution...")
    return None


def human_like_delay(min_sec=1.5, max_sec=3.0):
    time.sleep(random.uniform(min_sec, max_sec))


def human_like_type(driver, element, text):
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].focus(); arguments[0].click();", element)

    for char in text:
        element.send_keys(char)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
        time.sleep(random.uniform(0.1, 0.25))
    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element)
    driver.execute_script("arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));", element)


def generate_random_name():
    first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth',
                  'David', 'Jessica', 'Richard', 'Sarah', 'Joseph', 'Karen', 'Thomas', 'Nancy', 'Daniel', 'Lisa']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def generate_random_business_name():
    prefixes = ['Quick', 'Elite', 'Prime', 'Summit', 'Pinnacle', 'Apex', 'Zenith', 'Vanguard', 'Titan', 'Nova',
               'Sunset', 'Harbor', 'Peak', 'Crest', 'Beacon', 'Horizon', 'Vista', 'Frontier']
    industries = ['Solutions', 'Ventures', 'Systems', 'Dynamics', 'Innovations', 'Technologies', 'Group',
                 'Enterprises', 'Partners', 'Corp', 'Services', 'Management', 'Consulting', 'Retail', 'Hospitality']
    return f"{random.choice(prefixes)} {random.choice(industries)}"


def generate_random_phone():
    return f"({random.randint(200, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"


def create_mail_tm_account():
    API_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    try:
        res = requests.get("https://api.mail.tm/domains", headers=API_HEADERS, timeout=10)
        data = res.json()
        domain = data[0]['domain'] if isinstance(data, list) else data.get('hydra:member', [{}])[0].get('domain')
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        address = f"{username}@{domain}"
        password = "StealthBotPassword123!"
        payload = {"address": address, "password": password}
        requests.post("https://api.mail.tm/accounts", json=payload, headers=API_HEADERS, timeout=10)
        token_res = requests.post("https://api.mail.tm/token", json=payload, headers=API_HEADERS, timeout=10)
        return address, token_res.json()['token']
    except Exception as e:
        print(f"Mail.tm API error: {e}")
        return None, None


def run_stealth_automation():
    print("Generating temporary email via Mail.tm API...")
    my_email, api_token = create_mail_tm_account()
    if not my_email:
        print("Failed to generate email. Exiting.")
        return
    print(f"Success! Got stealth email: {my_email}")

    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-geolocation")

    # If running headless in GitHub Actions environment
    if os.environ.get("GITHUB_ACTIONS") == "true":
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    # Dynamically detect Chrome version
    detected_version = get_installed_chrome_version()

    print("Launching stealth Chrome...")
    if detected_version:
        driver = uc.Chrome(options=options, version_main=detected_version)
    else:
        driver = uc.Chrome(options=options)

    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32" if platform.system() == "Windows" else "Linux x86_64",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    wait = WebDriverWait(driver, 20)
    actions = ActionChains(driver)

    try:
        print(f"Opening Cinder-OS landing page: {TARGET_URL}")
        driver.get(TARGET_URL)
        human_like_delay(3, 5)

        # 1. Click "Contact sales" button
        print("Looking for Contact Sales button...")
        contact_sales_xpath = "//a[contains(translate(text(), 'CONTACT SALES', 'contact sales'), 'contact sales') or contains(@href, 'contact')]"
        contact_sales_btn = wait.until(EC.element_to_be_clickable((By.XPATH, contact_sales_xpath)))
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", contact_sales_btn)
        human_like_delay(1, 2)
        actions.move_to_element(contact_sales_btn).pause(0.5).click().perform()
        human_like_delay(3, 5)

        print("Starting form filling process...")

        full_name = generate_random_name()
        business_name = generate_random_business_name()
        phone_number = generate_random_phone()
        message = "Hello, I am interested in Cinder-OS for my business. Please contact me."

        field_selectors = {
            'Business Owner Name': "//input[@placeholder='Full name' or contains(@name, 'name')]",
            'Business Name': "//input[@placeholder='Business name' or contains(@name, 'business')]",
            'Email': "//input[@type='email' or contains(@placeholder, 'you@')]",
            'Phone': "//input[contains(@placeholder, '555') or contains(@name, 'phone')]",
            'Current Equipment Provider': "//input[contains(@placeholder, 'Clover') or contains(@name, 'equipment')]",
            'Message': "//textarea[contains(@placeholder, 'Tell us') or contains(@name, 'message')]"
        }

        for field_name, xpath in field_selectors.items():
            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                
                if field_name == 'Business Owner Name':
                    human_like_type(driver, element, full_name)
                elif field_name == 'Business Name':
                    human_like_type(driver, element, business_name)
                elif field_name == 'Email':
                    human_like_type(driver, element, my_email)
                elif field_name == 'Phone':
                    human_like_type(driver, element, phone_number)
                elif field_name == 'Current Equipment Provider':
                    human_like_type(driver, element, random.choice(['Clover', 'Square', 'Toast', 'NCR']))
                elif field_name == 'Message':
                    human_like_type(driver, element, message)

                human_like_delay(0.8, 1.5)
            except Exception as e:
                print(f"Could not fill {field_name}: {e}")

        # Fill dropdown menus if present
        selects = driver.find_elements(By.TAG_NAME, "select")
        for s in selects:
            try:
                sel = Select(s)
                if len(sel.options) > 1:
                    sel.select_by_index(random.randint(1, len(sel.options) - 1))
                    human_like_delay(0.5, 1.0)
            except Exception:
                pass

        # 2. Click "Send Message" button
        print("Submitting form...")
        submit_xpath = "//button[contains(translate(text(), 'SEND MESSAGE', 'send message'), 'send message') or @type='submit']"
        send_button = wait.until(EC.element_to_be_clickable((By.XPATH, submit_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", send_button)
        human_like_delay(1, 2)
        
        actions.move_to_element(send_button).pause(0.5).click().perform()
        print("Form submitted successfully!")

        human_like_delay(5, 7)
        print("AUTOMATION COMPLETE!")

    except Exception as e:
        print(f"Error encountered: {e}")
        try:
            driver.save_screenshot("debug_error_visual_flow.png")
            print("Saved debug screenshot")
        except Exception:
            pass
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    run_stealth_automation()
