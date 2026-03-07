import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import yt_dlp

# --- [ إعدادات الهوية والتحكم ] ---
TOKEN = "8631339057:AAEXSbvqyLUFdVIJUdgmt46VtMvrk8ZXl98"
LOG_GROUP_ID = -1003757790519
ADMIN_ID = 8742900104 
BOT_USERNAME = "@do1wnload_bot"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

START_TEXT = "🎬 مرحباً بك في بوت التحميل الذكي..\nأرسل الرابط وسأهتم بالباقي ✨"
WAIT_TEXT = "⏳ جاري تحضير الميديا لك بكل حب.."

# --- [ تعديل القائمة لتظهر /start فقط للجميع ] ---
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="تشغيل البوت 🚀")
    ]
    await bot.set_my_commands(commands)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply(START_TEXT)

# --- [ أوامر المالك (ستظل تعمل ولكنها مخفية من القائمة) ] ---
@dp.message(Command("set_start"))
async def set_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        global START_TEXT
        text = message.text.replace("/set_start", "").strip()
        if text:
            START_TEXT = text
            await message.reply("✅ تم تحديث رسالة الترحيب!")

@dp.message(Command("set_wait"))
async def set_wait(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        global WAIT_TEXT
        text = message.text.replace("/set_wait", "").strip()
        if text:
            WAIT_TEXT = text
            await message.reply("✅ تم تحديث رسالة الانتظار!")

# --- [ محرك التحميل الشامل ] ---
@dp.message(F.text.startswith("http"))
async def handle_download(message: types.Message):
    url = message.text
    status_msg = await message.reply(f"{WAIT_TEXT}\n{BOT_USERNAME}")
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f'media_{message.from_user.id}_%(id)s.%(ext)s',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            if not info: raise Exception("Fail")
            
            entries = info.get('entries', [info])
            for entry in entries:
                if not entry: continue
                filename = ydl.prepare_filename(entry)
                if os.path.exists(filename):
                    filesize = os.path.getsize(filename) / (1024 * 1024)
                    if filesize > 45:
                        await bot.send_document(message.chat.id, FSInputFile(filename), caption=f"📦 {BOT_USERNAME}")
                    else:
                        await bot.send_video(message.chat.id, FSInputFile(filename), caption=f"🎬 {BOT_USERNAME}")
                    if os.path.exists(filename): os.remove(filename)

        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text("❌ فشل التحميل. قد يكون الرابط خاصاً أو السيرفر محظور حالياً.")

async def main():
    await set_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
