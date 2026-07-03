import asyncio
import re
import os
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import Message
from dotenv import load_dotenv

# ==================== KONFIGURATSIYA ====================
load_dotenv()  # .env faylidan ma'lumotlarni o'qish

# API ma'lumotlari
API_ID = int(os.getenv('API_ID', 31303952))
API_HASH = os.getenv('API_HASH', '5a20af5ddbfd1d8eff3c6160086c6a20')
SOURCE_CHAT_ID = int(os.getenv('SOURCE_CHAT_ID', -1002470337579))
TARGET_CHAT_ID = int(os.getenv('TARGET_CHAT_ID', -5524657712))

# Sessiya nomi
SESSION_NAME = os.getenv('SESSION_NAME', 'koramizda_session')

# ==================== LOGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==================== ASOSIY KLASS ====================
class MessageForwarder:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.processed_messages = set()
        self.message_count = 0
        
    async def start(self):
        """Botni ishga tushirish"""
        try:
            # Ulanish
            await self.client.start()
            
            # Foydalanuvchi ma'lumotlari
            me = await self.client.get_me()
            logger.info("=" * 50)
            logger.info(f"✅ Bot muvaffaqiyatli ishga tushdi!")
            logger.info(f"👤 Foydalanuvchi: {me.first_name} (@{me.username or 'yoq'})")
            logger.info(f"📱 Telefon: {me.phone}")
            logger.info(f"📡 Manba guruh: {SOURCE_CHAT_ID}")
            logger.info(f"🎯 Maqsad guruh: {TARGET_CHAT_ID}")
            logger.info("=" * 50)
            
            # Xabarlarni tinglash
            @self.client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
            async def handle_new_message(event):
                await self.process_message(event.message)
            
            logger.info("⏳ Xabarlar kutilmoqda... (Ctrl+C to'xtatish uchun)")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Xatolik: {e}")
            raise
            
    async def process_message(self, message: Message):
        """Xabarni qayta ishlash"""
        try:
            text = message.text or message.caption or ""
            
            # Takrorlanmaslik
            if message.id in self.processed_messages:
                return
                
            # Qisqa xabarlarni filter qilish
            if len(text.strip()) < 3:
                return
                
            # Telefon modellarini topish
            detected_models = self.extract_phone_models(text)
            
            if detected_models:
                # Xabarni formatlash
                formatted_msg = self.format_message(message, detected_models)
                
                # Yuborish
                await self.client.send_message(TARGET_CHAT_ID, formatted_msg)
                self.processed_messages.add(message.id)
                self.message_count += 1
                
                logger.info(f"📨 Yuborildi #{self.message_count}: {', '.join(detected_models)}")
                logger.info(f"📝 Xabar: {text[:50]}...")
                
        except Exception as e:
            logger.error(f"❌ Xatolik: {e}")
            
    def extract_phone_models(self, text: str) -> list:
        """Matndan telefon modellarini ajratib olish"""
        text_lower = text.lower()
        found_models = []
        
        # ========== IPHONE (AYFON) ==========
        if 'ayfon' in text_lower:
            found_models.append("iPhone")
            iphone_numbers = re.findall(r'ayfon\s*(\d{2})', text_lower)
            for num in iphone_numbers:
                model = f"iPhone {num}"
                found_models.append(model)
                if 'pro max' in text_lower:
                    found_models.append(f"{model} Pro Max")
                elif 'pro' in text_lower:
                    found_models.append(f"{model} Pro")
                elif 'max' in text_lower:
                    found_models.append(f"{model} Max")
        
        # iPhone inglizcha
        iphone_match = re.findall(r'iphone\s*(\d{2})', text_lower)
        for num in iphone_match:
            model = f"iPhone {num}"
            found_models.append(model)
            if 'pro max' in text_lower:
                found_models.append(f"{model} Pro Max")
            elif 'pro' in text_lower:
                found_models.append(f"{model} Pro")
            elif 'max' in text_lower:
                found_models.append(f"{model} Max")
        
        # "max" so'zi
        if 'max' in text_lower:
            for model in found_models[:]:
                if 'max' not in model.lower():
                    found_models.append(f"{model} Max")
        
        # ========== BOSHQA MODELLAR ==========
        models_list = {
            'samsung': 'Samsung',
            'galaxy': 'Galaxy',
            'honor': 'Honor',
            'huawei': 'Huawei',
            'redmi': 'Redmi',
            'xiaomi': 'Xiaomi',
            'poco': 'Poco',
            'oppo': 'Oppo',
            'vivo': 'Vivo',
            'realme': 'Realme',
            'oneplus': 'OnePlus',
            'nokia': 'Nokia',
            'google pixel': 'Google Pixel',
            'pixel': 'Google Pixel',
            'sony': 'Sony',
            'lg': 'LG',
            'motorola': 'Motorola',
            'infinix': 'Infinix',
            'tecno': 'Tecno',
            'asus': 'Asus',
            'lenovo': 'Lenovo'
        }
        
        for key, value in models_list.items():
            if key in text_lower:
                found_models.append(value)
                if 's' in text_lower:
                    found_models.append(f"{value} S")
        
        # ========== "S" HARFI BILAN TUGAYDIGAN MODELLAR ==========
        s_models = re.findall(r'\b([A-Za-z]+\s*S)\b', text, re.IGNORECASE)
        for model in s_models:
            if any(phone in model.lower() for phone in ['iphone', 'samsung', 'galaxy', 'honor', 'redmi']):
                found_models.append(model.title())
        
        # Unique qilish va tartiblash
        return sorted(list(set(found_models)))
        
    def format_message(self, message: Message, models: list) -> str:
        """Xabarni formatlash"""
        original_text = message.text or message.caption or ""
        
        # Foydalanuvchi ma'lumotlari
        sender_name = "Noma'lum"
        sender_username = ""
        
        if message.sender:
            if message.sender.first_name:
                sender_name = message.sender.first_name
                if hasattr(message.sender, 'last_name') and message.sender.last_name:
                    sender_name += f" {message.sender.last_name}"
            if hasattr(message.sender, 'username') and message.sender.username:
                sender_username = f"(@{message.sender.username})"
        
        # Xabar vaqti
        msg_date = message.date.strftime("%d.%m.%Y %H:%M")
        
        # Xabar havolasi
        msg_link = f"https://t.me/c/{str(SOURCE_CHAT_ID)[4:]}/{message.id}"
        
        formatted_msg = f"""
📱 **Yangi telefon e'loni**

👤 **Foydalanuvchi:** {sender_name} {sender_username}
🕒 **Vaqt:** {msg_date}
📋 **Modellar:** {', '.join(models)}
🔢 **Xabar ID:** {message.id}

─────────────────
📝 **Xabar matni:**
{original_text}
─────────────────

🔗 [Xabarga o'tish]({msg_link})
🔄 @koramizda_bot
"""
        return formatted_msg

# ==================== ASOSIY FUNKSIYA ====================
async def main():
    """Asosiy funksiya"""
    print("=" * 50)
    print("📱 TELEGRAM MESSAGE FORWARDER BOT")
    print("🐍 Worker versiyasi")
    print("=" * 50)
    
    forwarder = MessageForwarder()
    try:
        await forwarder.start()
    except KeyboardInterrupt:
        print("\n⏹️ Bot to'xtatildi")
        logger.info("Bot to'xtatildi")
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        logger.error(f"Xatolik: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Dastur to'xtatildi")
    except Exception as e:
        print(f"❌ Dastur xatosi: {e}")
