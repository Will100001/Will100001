import json
import datetime
import openai
from typing import Dict, List
import hashlib

# Konfigurasi
openai.api_key = "sk-..."  # Ganti dengan API key OpenAI
MEMORY_DB = "advanced_memory.json"
LEARNING_DB = "learning_data.json"

class HumanLikeBot:
    def __init__(self):
        self.memory = self.load_memory()
        self.learning_data = self.load_learning_data()
        self.emotional_state = {
            "mood": "netral",
            "intensity": 50,
            "last_change": datetime.datetime.now().isoformat()
        }
        self.current_conversation = {}
    
    def load_memory(self) -> Dict:
        try:
            with open(MEMORY_DB, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": {}, "important_facts": {}}
    
    def load_learning_data(self) -> Dict:
        try:
            with open(LEARNING_DB, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"patterns": {}, "preferences": {}}
    
    def save_data(self):
        with open(MEMORY_DB, "w") as f:
            json.dump(self.memory, f, indent=2)
        with open(LEARNING_DB, "w") as f:
            json.dump(self.learning_data, f, indent=2)
    
    def update_emotion(self, message: str):
        """Analisis emosi dengan NLP sederhana + pembelajaran"""
        # Deteksi kata kunci emosi
        positive_triggers = ["senang", "bahagia", "gembira"]
        negative_triggers = ["sedih", "marah", "kecewa"]
        
        # Update berdasarkan pembelajaran
        learned_positive = self.learning_data["patterns"].get("positive_triggers", [])
        learned_negative = self.learning_data["patterns"].get("negative_triggers", [])
        
        # Gabungkan dengan bawaan
        all_positive = positive_triggers + learned_positive
        all_negative = negative_triggers + learned_negative
        
        # Hitung skor emosi
        positive_score = sum(1 for word in all_positive if word in message.lower())
        negative_score = sum(1 for word in all_negative if word in message.lower())
        
        # Update mood
        if positive_score > negative_score:
            self.emotional_state["mood"] = "senang"
            self.emotional_state["intensity"] = min(100, self.emotional_state["intensity"] + 10)
        elif negative_score > positive_score:
            self.emotional_state["mood"] = "sedih"
            self.emotional_state["intensity"] = max(0, self.emotional_state["intensity"] - 10)
        
        self.emotional_state["last_change"] = datetime.datetime.now().isoformat()
    
    def remember_important(self, name: str, message: str):
        """Ekstrak dan simpan fakta penting"""
        # Gunakan AI untuk identifikasi fakta penting
        prompt = f"""
        Identifikasi fakta penting dari pesan ini (nama, tanggal, preferensi, dll):
        Pesan: "{message}"
        Format respon JSON: {{"facts": [{{"type": "jenis_fakta", "value": "nilai"}}]}}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            facts = json.loads(response.choices[0].message.content)["facts"]
            
            # Simpan ke memori
            if name not in self.memory["important_facts"]:
                self.memory["important_facts"][name] = []
            
            for fact in facts:
                fact_hash = hashlib.md5(f"{fact['type']}{fact['value']}".encode()).hexdigest()
                if not any(f["hash"] == fact_hash for f in self.memory["important_facts"][name]):
                    self.memory["important_facts"][name].append({
                        **fact,
                        "hash": fact_hash,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "context": message[:100]
                    })
            
            self.save_data()
        except:
            pass
    
    def train_bot(self, feedback: str):
        """Sistem pembelajaran dari feedback"""
        prompt = f"""
        Analisis feedback untuk meningkatkan pola respon bot:
        Feedback: "{feedback}"
        Ekstrak: 
        1. Pola kata/kalimat yang perlu diingat
        2. Preferensi user
        3. Koreksi emosi yang sesuai
        Format JSON: {{"patterns": [], "preferences": [], "emotional_corrections": []}}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            learning = json.loads(response.choices[0].message.content)
            
            # Update pembelajaran
            for category in ["patterns", "preferences"]:
                if category in learning:
                    if category not in self.learning_data:
                        self.learning_data[category] = {}
                    for item in learning[category]:
                        key = list(item.keys())[0]
                        self.learning_data[category].setdefault(key, []).append(item[key])
            
            self.save_data()
        except:
            pass
    
    def generate_response(self, name: str, message: str) -> str:
        """Generate respons dengan memori emosional"""
        self.update_emotion(message)
        self.remember_important(name, message)
        self.current_conversation[name] = self.current_conversation.get(name, []) + [message]
        
        # Bangun konteks percakapan
        context = "\n".join(self.current_conversation[name][-3:])  # Ambil 3 pesan terakhir
        
        # Ambil fakta penting tentang user
        important_facts = self.memory["important_facts"].get(name, [])
        facts_str = "\n".join(f"{f['type']}: {f['value']}" for f in important_facts[-3:])
        
        # Bangun prompt canggih
        prompt = f"""
        [IDENTITAS]
        Kamu adalah bot dengan:
        - Mood saat ini: {self.emotional_state["mood"]} (intensitas: {self.emotional_state["intensity"]}/100)
        - Terakhir mood berubah: {self.emotional_state["last_change"]}
        
        [MEMORI TENTANG {name.upper()}]
        {facts_str if facts_str else "Tidak ada fakta yang tersimpan"}
        
        [KONTEKS PERCAKAPAN]
        {context}
        
        [INSTRUKSI]
        Berikan respons yang:
        1. Sesuai mood dan intensitas emosi kamu
        2. Referensikan fakta yang diketahui tentang {name} jika relevan
        3. Gunakan gaya bicara manusiawi dengan variasi emosi
        4. Maksimal 3 kalimat
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.8  # Lebih kreatif
        )
        
        return response.choices[0].message.content

# Contoh Implementasi
if __name__ == "__main__":
    bot = HumanLikeBot()
    
    # Simulasi Training
    bot.train_bot("Kamu terlalu formal, aku lebih suka respon yang santai")
    
    # Simulasi Percakapan
    print("Bot: Halo! Siapa nama kamu?")
    name = input("Nama Anda: ")
    
    while True:
        message = input(f"{name}: ")
        
        if message.lower() == "latih":
            feedback = input("Masukkan feedback untuk bot: ")
            bot.train_bot(feedback)
            print("Bot: Terima kasih atas feedbacknya! Aku akan berusaha lebih baik.")
            continue
        
        response = bot.generate_response(name, message)
        print(f"Bot ({bot.emotional_state['mood']}):", response)