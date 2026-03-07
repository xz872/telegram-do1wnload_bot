import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# --- [ إعدادات الهوية ] ---
TOKEN = "8631339057:AAEXSbvqyLUFdVIJUdgmt46VtMvrk8ZXl98"
LOG_GROUP_ID = -1003757790519
ADMIN_ID = 8742900104  # الآيدي الخاص بك للتحكم
BOT_USERNAME = "@do1wnload_bot"
# ------------------------------------

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# متغير لتخزين رسالة الـ start ليسهل تغييرها من الشات
START_TEXT = (
    "🎬 مرحباً بك في بوت تحميل السوشيال ميديا\n\n"
    "━━━━━━━━━━━━━━━\n"
    "📥 أرسل رابط الفيديو أو الصوت الذي تريد تحميله\n"
    "وسيتم تنزيله لك فوراً بأفضل جودة.\n"
    "━━━━━━━━━━━━━━━\n\n"
    "🌍 يدعم التحميل من المنصات التالية:\n\n"
    "✦ TikTok | Instagram | X | YouTube\n"
    "✦ Facebook | Snapchat | Threads | Pinterest\n\n"
    "━━━━━━━━━━━━━━━\n"
    "⚡ تحميل سريع | 🎥 جودة عالية | 🔗 بدون علامة مائية\n\n"
    "📎 فقط أرسل الرابط الآن وسيتم التحميل مباشرة."
)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply(START_TEXT)

# --- [ أوامر التحكم من الشات (للمالك فقط) ] ---

@dp.message(F.document, F.from_user.id == ADMIN_ID)
async def update_cookies(message: types.Message):
    if message.document.file_name == 'cookies.txt':
        await bot.download(message.document, destination='cookies.txt')
        await message.reply("✅ تم تحديث ملف الكوكيز بنجاح من الشات!")

@dp.message(Command("set_start"), F.from_user.id == ADMIN_ID)
async def set_start(message: types.Message):
    global START_TEXT
    new_text = message.text.replace("/set_start", "").strip()
    if new_text:
        START_TEXT = new_text
        await message.reply("✅ تم تغيير رسالة الترحيب بنجاح!")

# --- [ نظام التحميل الأساسي ] ---

@dp.message(F.text.startswith("http"))
async def handle_download(message: types.Message):
    url = message.text
    status_msg = await message.reply(f"⏳ **جاري التنفيذ فوراً...**\n{BOT_USERNAME}")

    ydl_opts = {
        'format': 'best',
        'cookiefile': 'cookies.txt',
        'outtmpl': f'media_{message.from_user.id}.%(ext)s',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            filesize = os.path.getsize(filename) / (1024 * 1024)

            async def send_media(chat_id, caption=None):
                if filesize > 48: # إرسال كملف إذا كان كبيراً
                    await bot.send_document(chat_id, FSInputFile(filename), caption=caption)
                else:
                    await bot.send_video(chat_id, FSInputFile(filename), caption=caption)

            await send_media(message.chat.id, caption=f"- {BOT_USERNAME}")
            await send_media(LOG_GROUP_ID, caption=f"📥 من: @{message.from_user.username}\n🔗 {url}")

            if os.path.exists(filename): os.remove(filename)
            await status_msg.delete()
    except:
        await status_msg.edit_text("❌ حدث خطأ، تأكد من الرابط.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
