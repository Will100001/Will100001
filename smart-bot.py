import os
import time
import random
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import openai
import pytesseract
from PIL import Image

# Load config
load_dotenv("config.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Kelas Bot dengan Emosi
class EmotionalBot:
    def __init__(self):
        self.mood = os.getenv("MOOD_DEFAULT", "netral")
        self.mood_level = 50
        self.memory = []  # Penyimpanan percakapan

    def update_mood(self, text):
        text = text.lower()
        if "senang" in text or "happy" in text:
            self.mood = "senang"
            self.mood_level = min(100, self.mood_level + 15)
        elif "sedih" in text or "sad" in text:
            self.mood = "sedih"
            self.mood_level = max(0, self.mood_level - 15)
        # Update mood secara acak untuk simulasi "perasaan"
        self.mood_level += random.randint(-5, 5)

    def generate_response(self, input_text):
        self.update_mood(input_text)
        self.memory.append(input_text)  # Simpan ke memori

        # Respons berdasarkan mood
        mood_responses = {
            "senang": ["Wah! ", "Hore! ", "😊 "],
            "sedih": ["Aduh... ", "😢 ", "Maaf ya..."],
            "marah": ["Hmph! ", "😠 ", "Jangan begitu..."],
            "netral": ["Oke. ", "Hmm. ", "👍 "]
        }
        prefix = random.choice(mood_responses.get(self.mood, [""]))

        # Gunakan OpenAI untuk respons cerdas
        prompt = f"""
        Kamu adalah bot dengan emosi ({self.mood}). 
        Balas pesan ini dengan singkat dan manusiawi: '{input_text}'
        """
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return prefix + response.choices[0].message.content

# Fungsi Deteksi Teks di Chrome
def detect_text(driver):
    driver.save_screenshot("temp.png")
    text = pytesseract.image_to_string(Image.open("temp.png"), lang="ind+eng")
    return text.strip()

# Main Program
def main():
    bot = EmotionalBot()
    driver = webdriver.Chrome()

    print("Pilih platform:")
    print("1. WhatsApp Web")
    print("2. Website Umum (Deteksi Teks)")
    choice = input("Masukkan pilihan (1/2): ")

    if choice == "1":
        driver.get("https://web.whatsapp.com")
        input("Scan QR WhatsApp Web, lalu tekan Enter...")
        target = input("Nama kontak/grup yang mau dipantau: ")

        while True:
            try:
                last_msg = driver.find_elements("xpath", '//div[@class="_1Gy50"]')[-1].text
                if last_msg and last_msg not in bot.memory:
                    response = bot.generate_response(last_msg)
                    chat_box = driver.find_element("xpath", '//div[@contenteditable="true"]')
                    chat_box.send_keys(response + Keys.ENTER)
            except Exception as e:
                print("Error:", e)
            time.sleep(5)

    elif choice == "2":
        url = input("Masukkan URL website: ")
        driver.get(url)
        while True:
            detected_text = detect_text(driver)
            if detected_text:
                print("Terdeteksi:", detected_text)
                response = bot.generate_response(detected_text)
                print("Bot:", response)
            time.sleep(10)

if __name__ == "__main__":
    main()