import asyncio
import re
from telethon import TelegramClient, events
from telethon.tl.types import Message
from datetime import datetime
import logging
import requests

# ==================== KONFIGURATSIYA ====================
API_ID = 31303952
API_HASH = '5a20af5ddbfd1d8eff3c6160086c6a20'
SOURCE_CHAT_ID = -1002470337579
TARGET_CHAT_ID = -5524657712

# ==================== HTTP PROKSI ORQALI ULANISH ====================
# Telegram MTProto ni HTTP orqali ulash uchun maxsus sozlamalar
# Bu usul PythonAnywhere da ishlashi mumkin

from telethon.network.connection.http import ConnectionHttp

# Telegram serverlari uchun HTTP proxy
TELEGRAM_HTTP_PROXY = {
    'proxy_type': 'http',  # HTTP proxy
    'addr': '149.154.167.51',  # Telegram server
    'port': 80,  # HTTP port
    'username': None,
    'password': None
}

# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class MessageForwarder:
    def __init__(self):
        # HTTP connection orqali ulanish
        self.client = TelegramClient(
            'koramizda_session',
            API_ID,
            API_HASH,
            connection=ConnectionHttp,
            use_ipv6=False,
            retries=10,
            timeout=30
        )
        
        self.processed_messages = set()
        self.message_count = 0
        
    async def start(self):
        try:
            # Ulanishni boshlash
            await self.client.start()
            
            me = await self.client.get_me()
            logger.info(f"✅ Bot muvaffaqiyatli ishga tushdi!")
            logger.info(f"👤 Foydalanuvchi: {me.first_name}")
            logger.info(f"📡 Manba guruh: {SOURCE_CHAT_ID}")
            logger.info(f"🎯 Maqsad guruh: {TARGET_CHAT_ID}")
            logger.info("=" * 50)
            
            @self.client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
            async def handle_new_message(event):
                await self.process_message(event.message)
            
            logger.info("⏳ Xabarlar kutilmoqda...")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Xatolik: {e}")
            
    async def process_message(self, message: Message):
        try:
            text = message.text or message.caption or ""
            
            if message.id in self.processed_messages:
                return
                
            if len(text.strip()) < 3:
                return
                
            detected_models = self.extract_phone_models(text)
            
            if detected_models:
                formatted_msg = self.format_message(message, detected_models)
                await self.client.send_message(TARGET_CHAT_ID, formatted_msg)
                self.processed_messages.add(message.id)
                self.message_count += 1
                
                logger.info(f"📨 Yuborildi #{self.message_count}: {', '.join(detected_models)}")
                
        except Exception as e:
            logger.error(f"❌ Xatolik: {e}")
            
    def extract_phone_models(self, text: str) -> list:
        text_lower = text.lower()
        found_models = []
        
        # iPhone (ayfon)
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
        
        # Boshqa modellar
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
        }
        
        for key, value in models_list.items():
            if key in text_lower:
                found_models.append(value)
                if 's' in text_lower:
                    found_models.append(f"{value} S")
        
        return sorted(list(set(found_models)))
        
    def format_message(self, message: Message, models: list) -> str:
        original_text = message.text or message.caption or ""
        
        sender_name = "Noma'lum"
        sender_username = ""
        
        if message.sender:
            if message.sender.first_name:
                sender_name = message.sender.first_name
                if hasattr(message.sender, 'last_name') and message.sender.last_name:
                    sender_name += f" {message.sender.last_name}"
            if hasattr(message.sender, 'username') and message.sender.username:
                sender_username = f"(@{message.sender.username})"
        
        msg_date = message.date.strftime("%d.%m.%Y %H:%M")
        
        formatted_msg = f"""
📱 **Yangi telefon e'loni**

👤 **Foydalanuvchi:** {sender_name} {sender_username}
🕒 **Vaqt:** {msg_date}
📋 **Modellar:** {', '.join(models)}

─────────────────
📝 **Xabar matni:**
{original_text}
─────────────────

🔄 @koramizda_bot
"""
        return formatted_msg

async def main():
    print("=" * 50)
    print("📱 TELEGRAM MESSAGE FORWARDER BOT")
    print("🌐 HTTP Connection versiyasi")
    print("=" * 50)
    
    print("\n⚠️ PythonAnywhere da ishlamasa, quyidagi platformalarni ishlating:")
    print("1. Heroku (bepul)")
    print("2. Railway (bepul)")
    print("3. Render (bepul)")
    print("4. O'z VPS hosting")
    print("=" * 50)
    
    forwarder = MessageForwarder()
    try:
        await forwarder.start()
    except KeyboardInterrupt:
        print("\n⏹️ Bot to'xtatildi")
    except Exception as e:
        print(f"❌ Xatolik: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Dastur to'xtatildi")
