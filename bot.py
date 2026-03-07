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
# ------------------------------------

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# الرسائل الافتراضية (الكيوت)
START_TEXT = "🎬 مرحباً بك في بوت التحميل الذكي..\nأرسل الرابط وسأهتم بالباقي ✨"
WAIT_TEXT = "⏳ جاري تحضير الميديا لك بكل حب.."

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="تشغيل البوت 🚀"),
        BotCommand(command="set_start", description="تغيير رسالة الترحيب ⚙️"),
        BotCommand(command="set_wait", description="تغيير رسالة الانتظار ⏳"),
        BotCommand(command="help", description="مساعدة ❓")
    ]
    await bot.set_my_commands(commands)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply(START_TEXT)

# --- [ أوامر التحكم للمالك فقط ] ---
@dp.message(Command("set_start"))
async def set_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        global START_TEXT
        new_text = message.text.replace("/set_start", "").strip()
        if new_text:
            START_TEXT = new_text
            await message.reply("✅ تم تحديث رسالة الترحيب!")

@dp.message(Command("set_wait"))
async def set_wait(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        global WAIT_TEXT
        new_text = message.text.replace("/set_wait", "").strip()
        if new_text:
            WAIT_TEXT = new_text
            await message.reply("✅ تم تحديث رسالة الانتظار بنجاح!")

# --- [ نظام التحميل ] ---
@dp.message(F.text.startswith("http"))
async def handle_download(message: types.Message):
    url = message.text
    # هنا نستخدم الرسالة التي قمت بتغييرها
    status_msg = await message.reply(f"{WAIT_TEXT}\n{BOT_USERNAME}")
    
    ydl_opts = {'format': 'best', 'outtmpl': f'media_{message.from_user.id}.%(ext)s'}
    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            filesize = os.path.getsize(filename) / (1024 * 1024)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 شارك الميديا ✨", switch_inline_query=url)]])
            
            async def send_media(chat_id, caption):
                if filesize > 48:
                    await bot.send_document(chat_id, FSInputFile(filename), caption=caption, reply_markup=keyboard)
                else:
                    await bot.send_video(chat_id, FSInputFile(filename), caption=caption, reply_markup=keyboard)

            await send_media(message.chat.id, f"- {BOT_USERNAME}")
            await send_media(LOG_GROUP_ID, f"📥 تحميل جديد من: @{message.from_user.username}")
            
            if os.path.exists(filename): os.remove(filename)
            await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text("❌ عذراً، لم أستطع تحميل هذا الرابط.")

async def main():
    await set_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
