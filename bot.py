import os
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, BotCommand
import yt_dlp

# --- [ الإعدادات ] ---
TOKEN = "8631339057:AAEXSbvqyLUFdVIJUdgmt46VtMvrk8ZXl98"
ADMIN_ID = 8742900104 
BOT_USERNAME = "@do1wnload_bot"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# رسائل متغيرة
START_TEXT = "🎬 البوت الخارق جاهز للعمل.. أرسل أي رابط ✨"
WAIT_TEXT = "⏳ جاري كسر الحماية وتحضير الملف.."

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply(START_TEXT)

# محرك التحميل الشامل - نسخة كسر الحظر
@dp.message(F.text.startswith("http"))
async def handle_download(message: types.Message):
    url = message.text
    status_msg = await message.reply(f"{WAIT_TEXT}\n{BOT_USERNAME}")
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f'final_{message.from_user.id}_%(id)s.%(ext)s',
        'noplaylist': False,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        # إضافة User-Agent لمتصفح حديث جداً
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'headers': {
            'Referer': 'https://twitter.com/',
        },
        # محرك الالتفاف عبر كوكيز عشوائية (Browser Emulation)
        'extractor_args': {'twitter': {'api': 'v1.1'}}, 
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            if not info: raise Exception("No Media")
            
            entries = info.get('entries', [info])
            for entry in entries:
                if not entry: continue
                filename = ydl.prepare_filename(entry)
                
                # البحث عن الملف إذا تغير امتداده
                base = os.path.splitext(filename)[0]
                for ext in ['.mp4', '.mkv', '.webm', '.bin']:
                    if os.path.exists(base + ext):
                        filename = base + ext
                        break

                if os.path.exists(filename):
                    filesize = os.path.getsize(filename) / (1024 * 1024)
                    if filesize > 45:
                        await bot.send_document(message.chat.id, FSInputFile(filename), caption=f"📦 {BOT_USERNAME}")
                    else:
                        await bot.send_video(message.chat.id, FSInputFile(filename), caption=f"🎬 {BOT_USERNAME}")
                    if os.path.exists(filename): os.remove(filename)

        await status_msg.delete()
    except Exception:
        await status_msg.edit_text("❌ فشل التحميل.. يبدو أن الخادم محظور حالياً من قبل الموقع، جرب بعد قليل.")

async def main():
    await bot.set_my_commands([BotCommand(command="start", description="🚀")])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
