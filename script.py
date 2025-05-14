import os, time, json, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
CHATS = os.getenv("CHAT_FILTER", "").split(",")
STATE_FILE = "state.json"

def load_state():
    return json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-data-dir=/tmp/chrome-profile")  # persistent session
    return webdriver.Chrome(ChromeDriverManager().install(), options=options)

def send_to_discord(chat, message):
    payload = {"content": f"📥 New message in *{chat}*:\n{message}"}
    requests.post(DISCORD_WEBHOOK, json=payload)

def main():
    state = load_state()
    driver = setup_driver()

    try:
        driver.get("https://web.whatsapp.com")
        time.sleep(15)  # wait for QR scan or auto-login

        for chat in CHATS:
            try:
                chat = chat.strip()
                if not chat: continue

                search = driver.find_element(By.XPATH, f'//span[@title="{chat}"]')
                search.click()
                time.sleep(2)

                messages = driver.find_elements(By.CSS_SELECTOR, 'div.message-in span.selectable-text')
                if messages:
                    last_msg = messages[-1].text.strip()
                    if last_msg and last_msg != state.get(chat):
                        send_to_discord(chat, last_msg)
                        state[chat] = last_msg

            except Exception as e:
                print(f"Error processing chat '{chat}':", str(e))

    finally:
        save_state(state)
        driver.quit()

if __name__ == "__main__":
    main()
