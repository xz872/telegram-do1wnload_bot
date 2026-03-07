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

# رسائل التحكم المرنة
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

# --- [ أوامر التحكم للمالك فقط من داخل الشات ] ---
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

# --- [ نظام التحميل الخارق للألبومات والمساحات الكبيرة ] ---
@dp.message(F.text.startswith("http"))
async def handle_download(message: types.Message):
    url = message.text
    status_msg = await message.reply(f"{WAIT_TEXT}\n{BOT_USERNAME}")
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'media_{message.from_user.id}_%(id)s.%(ext)s',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # استخراج المعلومات (دعم الألبومات والفيديوهات المتعددة)
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            entries = info.get('entries', [info])

            for entry in entries:
                filename = ydl.prepare_filename(entry)
                if not os.path.exists(filename): continue
                
                filesize = os.path.getsize(filename) / (1024 * 1024)
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 شارك الميديا ✨", switch_inline_query=url)]])

                # تجاوز قيود الحجم عبر الإرسال كـ Document إذا لزم الأمر
                if filesize > 48:
                    await bot.send_document(message.chat.id, FSInputFile(filename), caption=f"📦 ملف كبير: {filesize:.1f}MB\n{BOT_USERNAME}", reply_markup=keyboard)
                else:
                    await bot.send_video(message.chat.id, FSInputFile(filename), caption=f"🎬 {BOT_USERNAME}", reply_markup=keyboard)
                
                # إرسال نسخة للوجات لمراقبة النشاط
                await bot.send_message(LOG_GROUP_ID, f"📥 تحميل جديد من: @{message.from_user.username or 'بدون_يوزر'}\n🆔: `{message.from_user.id}`\n🔗: {url}")
                
                if os.path.exists(filename): os.remove(filename)

        await status_msg.delete()
    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text("❌ عذراً، لم أستطع تحميل هذا الرابط (قد يكون محمياً أو كبيراً جداً).")

async def main():
    await set_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
