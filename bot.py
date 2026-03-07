import os
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, BotCommand
import yt_dlp

# --- [ الإعدادات الأمنية والتحكم ] ---
TOKEN = "8631339057:AAEXSbvqyLUFdVIJUdgmt46VtMvrk8ZXl98"
LOG_GROUP_ID = -1003757790519
ADMIN_ID = 8742900104 
BOT_USERNAME = "@do1wnload_bot"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# رسائل متغيرة لكسر روتين السيرفر
START_TEXT = "🎬 البوت الخارق جاهز للعمل.. أرسل أي رابط بدون قيود ✨"
WAIT_TEXT = "⏳ جاري كسر الحماية وتحضير الملف.."

# قائمة User-Agents متنوعة للمراوغة
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]

async def set_bot_commands(bot: Bot):
    # إظهار /start فقط للجمهور لضمان الخصوصية
    await bot.set_my_commands([BotCommand(command="start", description="تشغيل البوت 🚀")])

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply(START_TEXT)

# --- [ أوامر الإدارة السرية ] ---
@dp.message(Command("set_start"))
async def set_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        global START_TEXT
        START_TEXT = message.text.replace("/set_start", "").strip() or START_TEXT
        await message.reply("✅ تم تحديث الترحيب!")

@dp.message(Command("set_wait"))
async def set_wait(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        global WAIT_TEXT
        WAIT_TEXT = message.text.replace("/set_wait", "").strip() or WAIT_TEXT
        await message.reply("✅ تم تحديث الانتظار!")

# --- [ المحرك النووي للتحميل ] ---
@dp.message(F.text.startswith("http"))
async def handle_download(message: types.Message):
    url = message.text
    status_msg = await message.reply(f"{WAIT_TEXT}\n{BOT_USERNAME}")
    
    # إعدادات معقدة لتجاوز حجب المحتوى الحساس والألبومات
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'final_{message.from_user.id}_%(id)s.%(ext)s',
        'noplaylist': False,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'user_agent': random.choice(USER_AGENTS),
        'referer': 'https://www.google.com/',
        'http_headers': {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'cookiefile': None, # يمكن إضافة ملف كوكيز هنا لاحقاً إذا لزم الأمر
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # محاولة استخراج المعلومات مع نظام إعادة المحاولة
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            if not info: raise Exception("No Media")
            
            entries = info.get('entries', [info])
            found = False

            for entry in entries:
                if not entry: continue
                filename = ydl.prepare_filename(entry)
                
                # التحقق من وجود الملف بأي صيغة نتجت
                if not os.path.exists(filename):
                    base = os.path.splitext(filename)[0]
                    for ext in ['.mp4', '.mkv', '.webm', '.bin']:
                        if os.path.exists(base + ext):
                            filename = base + ext
                            break

                if os.path.exists(filename):
                    found = True
                    filesize = os.path.getsize(filename) / (1024 * 1024)
                    
                    # إرسال كملف للأحجام الكبيرة لضمان العبور
                    if filesize > 45:
                        await bot.send_document(message.chat.id, FSInputFile(filename), caption=f"📦 {BOT_USERNAME}")
                    else:
                        await bot.send_video(message.chat.id, FSInputFile(filename), caption=f"🎬 {BOT_USERNAME}")
                    
                    if os.path.exists(filename): os.remove(filename)

            if not found: raise Exception("Not Found")
        
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text("❌ السيرفر يواجه حماية مشددة حالياً، جرب رابطاً آخر أو انتظر قليلاً.")

async def main():
    await set_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
