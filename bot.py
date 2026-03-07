import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# --- [ إعدادات الهوية - بياناتك الحالية ] ---
TOKEN = "8631339057:AAEXSbvqyLUFdVIJUdgmt46VtMvrk8ZXl98"
LOG_GROUP_ID = -1003757790519
BOT_USERNAME = "@do1wnload_bot"
# ------------------------------------

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    # النص الجديد الذي أرسلته أنت
    start_text = (
        "🎬 مرحباً بك في بوت تحميل السوشيال ميديا\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📥 أرسل رابط الفيديو أو الصوت الذي تريد تحميله\n"
        "وسيتم تنزيله لك فوراً بأفضل جودة.\n"
        "━━━━━━━━━━━━━━━\n\n"
        "🌍 يدعم التحميل من المنصات التالية:\n\n"
        "✦ TikTok\n"
        "✦ Instagram\n"
        "✦ X (Twitter)\n"
        "✦ YouTube\n"
        "✦ Facebook\n"
        "✦ Snapchat\n"
        "✦ Threads\n"
        "✦ Pinterest\n\n"
        "━━━━━━━━━━━━━━━\n"
        "⚡ تحميل سريع\n"
        "🎥 جودة عالية\n"
        "🔗 بدون علامة مائية\n\n"
        "📎 فقط أرسل الرابط الآن وسيتم التحميل مباشرة."
    )
    await message.reply(start_text)

@dp.message(F.text.startswith("http"))
async def handle_download(message: types.Message):
    url = message.text
    status_msg = await message.reply(f"⏳ **جاري التحليل وكسر القيود...**\n{BOT_USERNAME}")

    ydl_opts = {
        'format': 'best',
        'cookiefile': 'cookies.txt',
        'outtmpl': f'media_{message.from_user.id}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        # تقوية الكوكيز لكسر حظر المحتوى
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            filesize = os.path.getsize(filename) / (1024 * 1024)

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 شارك الميديا مع أصدقائك ✨", switch_inline_query=url)]
            ])

            # دالة الإرسال الذكية (تدعم الملفات الكبيرة لتجاوز الخطأ)
            async def send_media(chat_id, caption=None, reply_markup=None):
                if filesize > 48: 
                    await bot.send_document(chat_id, FSInputFile(filename), caption=caption, reply_markup=reply_markup)
                else:
                    if info.get('ext') in ['mp3', 'm4a', 'wav'] or 'soundcloud' in url:
                        await bot.send_audio(chat_id, FSInputFile(filename), caption=caption, reply_markup=reply_markup)
                    else:
                        await bot.send_video(chat_id, FSInputFile(filename), caption=caption, reply_markup=reply_markup)

            # 1. إرسال للمستخدم
            await send_media(message.chat.id, caption=f"- {BOT_USERNAME}", reply_markup=keyboard)

            # 2. إرسال لجروب اللوجات (الفيديو + البيانات)
            log_caption = f"📥 تحميل جديد: @{message.from_user.username or 'بدون_يوزر'}\n🆔 ID: `{message.from_user.id}`\n🔗 {url}"
            await send_media(LOG_GROUP_ID, caption=log_caption)

            if os.path.exists(filename): os.remove(filename)
            await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ فشل التحميل. قد يكون الرابط خاصاً أو الحجم غير مدعوم حالياً.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
