import os, time, json, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
CHATS = os.getenv("CHAT_FILTER", "").split(",")
STATE_FILE = "state.json"

def load_state():
    return json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def setup_driver():
    options = FirefoxOptions()
    # options.add_argument("--headless")  # Comment this to keep the browser visible
    options.set_preference("dom.webnotifications.enabled", False)
    service = FirefoxService(GeckoDriverManager().install())
    return webdriver.Firefox(service=service, options=options)

def send_to_discord(chat, message):
    payload = {"content": f"📥 New message in *{chat}*:\n{message}"}
    requests.post(DISCORD_WEBHOOK, json=payload)

def main():
    state = load_state()
    driver = setup_driver()

    try:
        driver.get("https://web.whatsapp.com")
        print("🔒 Waiting for QR code to be scanned...")

        WebDriverWait(driver, 180).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[tabindex='-1']"))
        )
        print("✅ Logged in. Monitoring chats... (Press Ctrl+C to stop)")

        while True:
            for chat in CHATS:
                try:
                    chat = chat.strip()
                    if not chat:
                        continue

                    search = driver.find_element(By.XPATH, f'//span[@title="{chat}"]')
                    search.click()
                    time.sleep(2)

                    messages = driver.find_elements(By.CSS_SELECTOR, 'div.message-in span.selectable-text')
                    if messages:
                        last_msg = messages[-1].text.strip()
                        if last_msg and last_msg != state.get(chat):
                            print(f"[{chat}] New message: {last_msg}")
                            send_to_discord(chat, last_msg)
                            state[chat] = last_msg

                except Exception as e:
                    print(f"⚠️ Error processing chat '{chat}': {str(e)}")

            save_state(state)
            time.sleep(30)  # check every 30 seconds

    except KeyboardInterrupt:
        print("\n👋 Exiting on user request.")

    finally:
        save_state(state)
        driver.quit()

if __name__ == "__main__":
    main()
