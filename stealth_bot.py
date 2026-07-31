import os
import sys
import time
import random
import string
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

TARGET_URL = "https://eurodns.pxf.io/PzkDy6"

def log(msg):
    print(msg, flush=True)

def generate_email():
    domains = ["1secmail.com", "1secmail.net"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{random.choice(domains)}"

def generate_password():
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(12))

def run_bot():
    log("Starting bot...")
    
    email = generate_email()
    password = generate_password()
    
    # Save credentials immediately
    with open("account_credentials.txt", "w") as f:
        f.write(f"Email: {email}\nPassword: {password}\n")
    
    log(f"Email: {email}")
    
    # Setup Chrome
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Load Buster if exists
    if os.path.exists("/opt/buster"):
        options.add_argument("--load-extension=/opt/buster")
        log("Buster loaded")
    
    try:
        driver = uc.Chrome(options=options)
    except Exception as e:
        log(f"Chrome error: {e}")
        sys.exit(1)
    
    try:
        # Navigate directly to registration
        log("Loading registration page...")
        driver.get("https://my.eurodns.com/login/createNewAccount")
        time.sleep(3)
        
        driver.save_screenshot("screenshot_01.png")
        
        # Fill form
        log("Filling form...")
        
        # Email
        email_field = driver.find_element(By.XPATH, "//input[@type='email']")
        email_field.clear()
        email_field.send_keys(email)
        
        # Passwords
        pass_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
        if len(pass_fields) >= 2:
            pass_fields[0].send_keys(password)
            pass_fields[1].send_keys(password)
        
        # Checkboxes
        for cb in driver.find_elements(By.XPATH, "//input[@type='checkbox']"):
            driver.execute_script("arguments[0].click();", cb)
        
        driver.save_screenshot("screenshot_02_filled.png")
        
        # Submit
        log("Submitting...")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)
        
        driver.save_screenshot("screenshot_03_submitted.png")
        
        # Handle CAPTCHA if present
        if "recaptcha" in driver.page_source.lower():
            log("CAPTCHA found, clicking audio...")
            try:
                # Switch to iframe
                driver.switch_to.frame(driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]"))
                # Click audio button
                driver.find_element(By.XPATH, "//button[@id='recaptcha-audio-button']").click()
                driver.switch_to.default_content()
                log("Audio clicked, waiting for Buster...")
                time.sleep(25)  # Wait for Buster
            except Exception as e:
                log(f"Audio click failed: {e}")
                driver.switch_to.default_content()
        
        driver.save_screenshot("screenshot_04_final.png")
        
        # Final submit
        try:
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
        except:
            driver.execute_script("document.querySelector('form').submit();")
        
        time.sleep(5)
        driver.save_screenshot("screenshot_05_done.png")
        
        log(f"Done. URL: {driver.current_url}")
        
    except Exception as e:
        log(f"Error: {e}")
        driver.save_screenshot("screenshot_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_bot()
