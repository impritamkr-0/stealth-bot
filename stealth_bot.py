import os
import sys
import platform
import time
import random
import string
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"

def generate_random_email():
    """Generate a random email using 1secmail"""
    try:
        domains = ["1secmail.com", "1secmail.net", "1secmail.org"]
        domain = random.choice(domains)
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{username}@{domain}"
        print(f"    ✓ Generated: {email}")
        return email, "TempPass123!"
    except Exception as e:
        timestamp = str(int(time.time()))[-6:]
        email = f"user{timestamp}@mailinator.com"
        return email, "TempPass123!"

def generate_strong_password():
    """Generate password meeting strict criteria"""
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
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))
    except:
        return None

def smart_fill_field(driver, element, text):
    """Fill field with human-like typing"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        element.click()
        element.clear()
        time.sleep(0.2)
        
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
            
        time.sleep(0.5)
        return True
    except:
        try:
            driver.execute_script(f"arguments[0].value = '{text}';", element)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', {{ bubbles: true }}));", element)
            return True
        except:
            return False

def click_submit_button(driver, final=False):
    """Click submit button"""
    selectors = [
        "//button[contains(text(), 'Create account')]",
        "//button[contains(text(), 'Create Account')]",
        "//button[@type='submit']",
        "//button[contains(@class, 'btn-primary')]",
        "//button[contains(@class, 'submit')]",
        "//input[@type='submit']",
    ]
    
    if final:
        selectors = ["//button[contains(text(), 'Create account')]"] + selectors
    
    for selector in selectors:
        try:
            by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((by, selector)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", btn)
            print(f"    ✓ Clicked submit")
            return True
        except:
            continue
    
    try:
        driver.execute_script("""
            var btns = document.querySelectorAll('button[type="submit"], input[type="submit"]');
            if(btns.length > 0) btns[0].click();
        """)
        return True
    except:
        pass
    return False

def click_audio_button(driver):
    """
    Click the audio button on reCAPTCHA to switch to audio challenge
    This allows Buster to solve it automatically
    """
    print("    Switching to audio CAPTCHA...")
    
    # Try multiple selectors for the audio button
    audio_selectors = [
        "//button[@id='recaptcha-audio-button']",
        "//button[@title='Get an audio challenge']",
        "//button[@aria-label='Get an audio challenge']",
        "//div[@class='rc-buttons']//button[3]",
        "//span[@id='recaptcha-audio-button']",
        "//button[contains(@class, 'audio-button')]",
        "//button[contains(@class, 'recaptcha') and contains(@class, 'audio')]",
    ]
    
    for selector in audio_selectors:
        try:
            by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
            btn = driver.find_element(by, selector)
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                print("    ✓ Audio button clicked")
                time.sleep(3)  # Wait for audio to load
                return True
        except:
            continue
    
    # JavaScript fallback
    try:
        result = driver.execute_script("""
            // Look for audio button by various attributes
            var buttons = document.querySelectorAll('button');
            for(var i=0; i<buttons.length; i++) {
                var title = buttons[i].getAttribute('title') || '';
                var aria = buttons[i].getAttribute('aria-label') || '';
                var id = buttons[i].id || '';
                if(title.toLowerCase().includes('audio') || 
                   aria.toLowerCase().includes('audio') ||
                   id.includes('audio')) {
                    buttons[i].click();
                    return 'audio button clicked';
                }
            }
            
            // Try to find by icon/aria-label in parent
            var allElements = document.querySelectorAll('*');
            for(var i=0; i<allElements.length; i++) {
                if(allElements[i].getAttribute('aria-label') === 'Get an audio challenge') {
                    allElements[i].click();
                    return 'found by aria-label';
                }
            }
            return 'not found';
        """)
        if 'clicked' in result or 'found' in result:
            print(f"    ✓ Audio button clicked via JS: {result}")
            time.sleep(3)
            return True
    except Exception as e:
        print(f"    [!] JS audio click failed: {e}")
    
    return False

def check_for_captcha(driver):
    """Check if CAPTCHA is present"""
    try:
        indicators = [
            "//div[contains(@class, 'g-recaptcha')]",
            "//iframe[contains(@src, 'recaptcha')]",
            "//div[@data-sitekey]",
            "//div[contains(@class, 'rc-anchor')]",
        ]
        for xpath in indicators:
            elements = driver.find_elements(By.XPATH, xpath)
            if elements and any(e.is_displayed() for e in elements):
                return True
    except:
        pass
    
    page_source = driver.page_source.lower()
    captcha_keywords = ['recaptcha', 'g-recaptcha', 'select all images', 'i\'m not a robot']
    return any(keyword in page_source for keyword in captcha_keywords)

def is_audio_challenge_active(driver):
    """Check if we're on the audio challenge screen"""
    try:
        audio_indicators = [
            "//button[contains(@id, 'audio')]",
            "//span[contains(text(), 'Press PLAY')]",
            "//div[contains(text(), 'audio')]",
            "//audio",
            "//button[contains(@title, 'Play')]",
        ]
        for xpath in audio_indicators:
            elements = driver.find_elements(By.XPATH, xpath)
            if elements and any(e.is_displayed() for e in elements):
                return True
    except:
        pass
    return False

def wait_for_buster_solution(driver, timeout=30):
    """
    Wait for Buster to solve the CAPTCHA
    Buster automatically clicks the solve button when audio challenge appears
    """
    print("    Waiting for Buster to solve...")
    
    for i in range(timeout):
        time.sleep(1)
        
        # Check if CAPTCHA is solved (g-recaptcha-response has value)
        try:
            response = driver.execute_script("""
                var textarea = document.getElementById('g-recaptcha-response');
                return textarea ? textarea.value : '';
            """)
            if response and len(response) > 0:
                print(f"    ✓ Buster solved CAPTCHA!")
                return True
        except:
            pass
        
        # Check if we're past the challenge
        if not check_for_captcha(driver):
            print(f"    ✓ Challenge completed!")
            return True
        
        if i % 5 == 0:
            print(f"    ... still solving ({i}s)")
    
    print("    [!] Timeout waiting for Buster")
    return False

def run_bot():
    print("=" * 60)
    print("EURODNS BOT - BUSTER AUDIO SOLVER")
    print("=" * 60)
    
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    print(f"Environment: {'GitHub Actions' if is_github else 'Local'}")
    
    # Generate credentials
    print("\n[1/6] Generating credentials...")
    email, _ = generate_random_email()
    password = generate_strong_password()
    print(f"    Email: {email}")
    print(f"    Password: {password[:3]}{'*' * (len(password)-3)}")
    
    # Setup Chrome
    print("\n[2/6] Setting up Chrome...")
    options = uc.ChromeOptions()
    
    if is_github:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
    
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Load Buster extension
    buster_path = os.environ.get('BUSTER_PATH', '/opt/buster')
    if os.path.exists(buster_path):
        options.add_argument(f"--load-extension={buster_path}")
        print(f"    ✓ Buster loaded: {buster_path}")
    else:
        print(f"    [!] Buster not found at {buster_path}")
    
    # Launch browser
    try:
        driver = uc.Chrome(options=options)
    except Exception as e:
        print(f"    [!] Chrome error: {e}")
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
        print("\n[3/6] Loading website...")
        driver.get(TARGET_URL)
        time.sleep(random.uniform(8, 10))
        
        if is_github:
            driver.save_screenshot("screenshot_01_initial.png")
        
        # Accept cookies
        print("    Accepting cookies...")
        try:
            for selector in ["#onetrust-accept-btn-handler", "//button[contains(text(), 'ACCEPT')]"]:
                try:
                    by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
                    btn = driver.find_element(by, selector)
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)
                    break
                except:
                    continue
        except:
            pass
        
        # Navigate to registration
        print("    Navigating to registration...")
        driver.get("https://my.eurodns.com/login/createNewAccount")
        time.sleep(random.uniform(6, 8))
        
        if is_github:
            driver.save_screenshot("screenshot_02_form.png")
        
        # Fill form
        print("\n[4/6] Filling form...")
        
        email_field = wait_for_element(driver, By.XPATH, "//input[@type='email']", timeout=15)
        if email_field:
            smart_fill_field(driver, email_field, email)
            print("    ✓ Email filled")
        
        time.sleep(random.uniform(2, 3))
        
        pass_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
        if len(pass_fields) >= 2:
            smart_fill_field(driver, pass_fields[0], password)
            print("    ✓ Password filled")
            time.sleep(random.uniform(1, 2))
            smart_fill_field(driver, pass_fields[1], password)
            print("    ✓ Confirm password filled")
        
        # Checkboxes
        try:
            checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            for cb in checkboxes:
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
        except:
            pass
        
        time.sleep(random.uniform(2, 3))
        
        # First submit
        print("\n[5/6] Submitting form...")
        click_submit_button(driver)
        time.sleep(random.uniform(6, 10))
        
        if is_github:
            driver.save_screenshot("screenshot_03_after_submit.png")
        
        # Handle CAPTCHA with Buster
        captcha_present = check_for_captcha(driver)
        
        if captcha_present:
            print("\n[!] CAPTCHA detected - Activating Buster...")
            
            # Click audio button to switch to audio challenge
            if click_audio_button(driver):
                print("    ✓ Switched to audio challenge")
                
                # Wait for Buster to solve
                if wait_for_buster_solution(driver, timeout=45):
                    print("    ✓ CAPTCHA solved by Buster")
                else:
                    print("    [!] Buster failed to solve")
                    driver.save_screenshot("screenshot_buster_failed.png")
            else:
                print("    [!] Could not click audio button")
                driver.save_screenshot("screenshot_audio_button_failed.png")
            
            if is_github:
                driver.save_screenshot("screenshot_04_captcha_handled.png")
        
        # Final submit
        print("\n[6/6] Final submission...")
        time.sleep(random.uniform(3, 5))
        
        final_clicked = False
        for attempt in range(3):
            if click_submit_button(driver, final=True):
                final_clicked = True
                break
            time.sleep(2)
        
        if not final_clicked:
            driver.execute_script("document.querySelector('form').submit();")
        
        time.sleep(random.uniform(10, 15))
        
        if is_github:
            driver.save_screenshot("screenshot_05_final.png")
        
        # Check success
        current_url = driver.current_url
        page_source = driver.page_source.lower()
        
        success = any([
            "welcome" in page_source,
            "success" in page_source,
            "dashboard" in current_url,
            "verification" in page_source,
            "confirm" in page_source,
            "thank you" in page_source,
        ])
        
        print("\n" + "=" * 60)
        if success:
            print("✓ REGISTRATION SUCCESSFUL")
        else:
            print("? STATUS UNCLEAR")
        print("=" * 60)
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"URL: {current_url}")
        print("=" * 60)
        
        if is_github:
            with open("account_credentials.txt", "w") as f:
                f.write(f"Email: {email}\n")
                f.write(f"Password: {password}\n")
                f.write(f"URL: {current_url}\n")
        
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        if is_github:
            driver.save_screenshot("screenshot_error.png")
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_bot()
