import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import yt_dlp

# --- [ إعدادات التحكم ] ---
TOKEN = "8631339057:AAEXSbvqyLUFdVIJUdgmt46VtMvrk8ZXl98"
LOG_GROUP_ID = -1003757790519
ADMIN_ID = 8742900104 
BOT_USERNAME = "@do1wnload_bot"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

START_TEXT = "🎬 مرحباً بك في بوت التحميل الذكي..\nأرسل الرابط وسأهتم بالباقي ✨"
WAIT_TEXT = "⏳ جاري تحضير الميديا لك بكل حب.."

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="تشغيل البوت 🚀"),
        BotCommand(command="set_start", description="تغيير رسالة الترحيب ⚙️"),
        BotCommand(command="set_wait", description="تغيير رسالة الانتظار ⏳")
    ]
    await bot.set_my_commands(commands)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply(START_TEXT)

@dp.message(Command("set_start"))
async def set_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        global START_TEXT
        START_TEXT = message.text.replace("/set_start", "").strip() or START_TEXT
        await message.reply("✅ تم تحديث رسالة الترحيب!")

@dp.message(Command("set_wait"))
async def set_wait(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        global WAIT_TEXT
        WAIT_TEXT = message.text.replace("/set_wait", "").strip() or WAIT_TEXT
        await message.reply("✅ تم تحديث رسالة الانتظار!")

@dp.message(F.text.startswith("http"))
async def handle_download(message: types.Message):
    url = message.text
    status_msg = await message.reply(f"{WAIT_TEXT}\n{BOT_USERNAME}")
    
    # إعدادات متطورة لتجاوز حماية المحتوى الحساس
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f'media_{message.from_user.id}_%(id)s.%(ext)s',
        'noplaylist': False,
        'extract_flat': False,
        'quiet': True,
        # إضافة User-Agent قوي جداً لتجاوز حظر X
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'headers': {
            'Referer': 'https://twitter.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            entries = info.get('entries', [info])

            for entry in entries:
                filename = ydl.prepare_filename(entry)
                if not os.path.exists(filename): continue
                
                filesize = os.path.getsize(filename) / (1024 * 1024)
                # إرسال كـ Document للملفات الكبيرة لضمان النجاح
                if filesize > 45:
                    await bot.send_document(message.chat.id, FSInputFile(filename), caption=f"📦 ملف كبير: {filesize:.1f}MB\n{BOT_USERNAME}")
                else:
                    await bot.send_video(message.chat.id, FSInputFile(filename), caption=f"🎬 {BOT_USERNAME}")
                
                if os.path.exists(filename): os.remove(filename)

        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text("❌ فشل التحميل. قد يكون الرابط خاصاً جداً أو هناك ضغط على السيرفر.")

async def main():
    await set_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
