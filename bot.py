import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# --- [ إعدادات الهوية - البيانات الحالية ] ---
TOKEN = "8631339057:AAEXSbvqyLUFdVIJUdgmt46VtMvrk8ZXl98"
LOG_GROUP_ID = -1003757790519
BOT_USERNAME = "@do1wnload_bot"
# ------------------------------------

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    start_text = (
        "🎬 مرحباً بك في بوت تحميل السوشيال ميديا\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📥 أرسل رابط الفيديو الذي تريد تحميله\n"
        "وسيتم تنزيله لك فوراً.\n"
        "━━━━━━━━━━━━━━━\n\n"
        "🌍 يدعم المنصات التالية:\n"
        "✦ TikTok\n"
        "✦ Instagram\n"
        "✦ X (Twitter)\n"
        "✦ YouTube\n"
        "✦ Facebook\n\n"
        "⚡ تحميل سريع\n"
        "🎥 جودة عالية\n\n"
        "📎 فقط أرسل الرابط الآن."
    )
    await message.reply(start_text)

@dp.message(F.text.startswith("http"))
async def handle_download(message: types.Message):
    url = message.text
    # رسالة الحالة التفاعلية (تختفي لاحقاً)
    status_msg = await message.reply(
        f"⏳ **الحالة: جاري التحليل**\n"
        f"🔗 **الرابط:** `{url[:20]}...`\n"
        f"⚙️ **المهمة:** الحصول على معلومات الـ..\n"
        f"📊 **الخطوة:** 181/2\n\n"
        f"{BOT_USERNAME}"
    )

    ydl_opts = {
        'format': 'best',
        'cookiefile': 'cookies.txt', 
        'outtmpl': f'video_{message.from_user.id}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 شارك الفيديو مع أصدقائك ✨", switch_inline_query=url)]
            ])

            # 1. إرسال الفيديو للمستخدم (الكود القديم)
            await bot.send_video(
                chat_id=message.chat.id,
                video=FSInputFile(filename),
                caption=f"- {BOT_USERNAME}",
                reply_markup=keyboard
            )

            # 2. التعديل الجديد: إرسال نفس الفيديو لجروب اللوجات
            log_caption = (
                f"📥 تحميل جديد: @{message.from_user.username or 'بدون_يوزر'}\n"
                f"🆔 ID: `{message.from_user.id}`\n"
                f"🔗 {url}"
            )
            await bot.send_video(
                chat_id=LOG_GROUP_ID,
                video=FSInputFile(filename),
                caption=log_caption
            )

            # التنظيف النهائي
            if os.path.exists(filename):
                os.remove(filename)
            await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ فشل التحميل أو المنصة تفرض حظراً.\nالخطأ: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
