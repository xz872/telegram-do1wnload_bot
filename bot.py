import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# --- [ إعدادات الهوية والتحكم ] ---
TOKEN = "8631339057:AAEXSbvqyLUFdVIJUdgmt46VtMvrk8ZXl98"
LOG_GROUP_ID = -1003757790519
# الآيدي الخاص بك المؤكد من اللوجات
ADMIN_ID = 8742900104 
BOT_USERNAME = "@do1wnload_bot"
# ------------------------------------

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# نص الترحيب الافتراضي (يمكنك تغييره من البوت)
START_TEXT = (
    "🎬 مرحباً بك في بوت تحميل السوشيال ميديا\n\n"
    "🌍 يدعم: TikTok, Instagram, X, YouTube, FB, Snapchat, Threads, Pinterest\n\n"
    "📥 أرسل الرابط وسيتم التحميل فوراً بأفضل جودة."
)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply(START_TEXT)

# --- [ لوحة التحكم المطورة بالتحقق اليدوي ] ---
@dp.message(Command("set_start"))
async def set_start(message: types.Message):
    # التحقق من أن المرسل هو صاحب البوت الفعلي
    if message.from_user.id == ADMIN_ID:
        global START_TEXT
        new_text = message.text.replace("/set_start", "").strip()
        if new_text:
            START_TEXT = new_text
            await message.reply("✅ تم تحديث رسالة الترحيب بنجاح!")
        else:
            await message.reply("⚠️ يرجى كتابة النص الجديد بعد الأمر، مثال:\n`/set_start نصك هنا`")
    else:
        # تجاهل الرسالة إذا لم يكن المرسل هو الآدمن
        pass

# --- [ نظام التحميل واللوجات المطور ] ---
@dp.message(F.text.startswith("http"))
async def handle_download(message: types.Message):
    url = message.text
    status_msg = await message.reply(f"⏳ **جاري التحليل وكسر القيود...**\n{BOT_USERNAME}")

    ydl_opts = {
        'format': 'best',
        'cookiefile': 'cookies.txt',
        'outtmpl': f'media_{message.from_user.id}.%(ext)s',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            filesize = os.path.getsize(filename) / (1024 * 1024)

            # زر المشاركة الشفاف المطور
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 شارك الميديا مع أصدقائك ✨", switch_inline_query=url)]
            ])

            # دالة الإرسال الذكية لتجاوز حدود تليجرام (أكبر من 50 ميجا ترسل كملف)
            async def send_media(chat_id, caption, reply_markup=None):
                if filesize > 48:
                    await bot.send_document(chat_id, FSInputFile(filename), caption=caption, reply_markup=reply_markup)
                else:
                    await bot.send_video(chat_id, FSInputFile(filename), caption=caption, reply_markup=reply_markup)

            # 1. إرسال الفيديو للمستخدم مع اليوزر والزر الشفاف
            await send_media(message.chat.id, f"- {BOT_USERNAME}", keyboard)

            # 2. إرسال اللوجات للجروب بالصيغة المطلوبة (ID + User + Link)
            log_text = (
                f"📥 تحميل جديد:\n"
                f"👤 المستخدم: @{message.from_user.username or 'بدون_يوزر'}\n"
                f"🆔 ID: `{message.from_user.id}`\n"
                f"🔗 الرابط: {url}"
            )
            await send_media(LOG_GROUP_ID, log_text)

            if os.path.exists(filename): os.remove(filename)
            await status_msg.delete()
    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text("❌ فشل التحميل. قد يكون الرابط خاصاً أو المنصة غير مدعومة حالياً.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
