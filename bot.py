import os
import re
import asyncio
import shutil
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatAction

# =========================
# CONFIG & ANTI-SPAM
# =========================
TOKEN = "8631339057:AAEXSbvqyLUFdVIJUdgmt46VtMvrk8ZXl98"
LOG_GROUP_ID = -1003757790519 

# نظام منع السبام الاحترافي لحماية Railway
user_calls = defaultdict(list)
SPAM_LIMIT = 3
SPAM_WINDOW = 30

BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

# محرك معالجة بـ 50 خيط (الأمثل لـ Railway)
EXECUTOR = ThreadPoolExecutor(max_workers=50) 
bot = Bot(TOKEN)
dp = Dispatcher()

# =========================
# CORE (محرك كسر القيود والسماح)
# =========================
def get_ydl_opts(output_template):
    return {
        "outtmpl": output_template,
        "format": "bestvideo+bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
        "retries": 10,
        "concurrent_fragment_downloads": 20, 
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "Referer": "https://www.google.com/",
        },
    }

async def download_media(url, folder):
    output_template = str(folder / f"{uuid.uuid4().hex[:8]}.%(ext)s")
    ydl_opts = get_ydl_opts(output_template)
    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)
    return await asyncio.get_event_loop().run_in_executor(EXECUTOR, extract)

# =========================
# HANDLERS (التطابق البصري النهائي)
# =========================
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("أهلاً بك! أرسل الرابط للتحميل الفوري ⚡")

@dp.message()
async def message_handler(message: Message):
    user_id = message.from_user.id
    now = asyncio.get_event_loop().time()
    
    # حماية من السبام
    user_calls[user_id] = [t for t in user_calls[user_id] if now - t < SPAM_WINDOW]
    if len(user_calls[user_id]) >= SPAM_LIMIT:
        return await message.reply("⚠️ اهدأ قليلاً! أنت ترسل الكثير من الطلبات.")
    
    urls = re.findall(r"https?://\S+", message.text or "")
    if not urls: return
    
    user_calls[user_id].append(now)
    for url in urls:
        asyncio.create_task(process_video(message, url))

async def process_video(message: Message, url: str):
    user = message.from_user
    
    # 🎨 التنسيق البصري المتطابق مع صورك
    status_text = (
        f"الحالة: جاري التحليل 🔍\n"
        f"الرابط: {url[:25]}... 🔗\n"
        f"المهمة: سحب الفيديو بجودته الأصلية 📡"
    )
    # تعطيل المعاينة لجعل الشكل لطيفاً كما طلبت
    status_msg = await message.answer(status_text, disable_web_page_preview=True)
    
    job_folder = DOWNLOADS_DIR / str(user.id) / uuid.uuid4().hex
    job_folder.mkdir(parents=True, exist_ok=True)
    
    try:
        await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
        
        info = await download_media(url, job_folder)
        file_path = next(job_folder.iterdir())
        
        # كابشن وزر مشاركة متطابق
        bot_info = await bot.get_me()
        caption = f"- @{bot_info.username}"
        kb_share = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ شارك الفيديو مع أصدقائك 🔗", url=f"https://t.me/share/url?url={url}")]
        ])

        await message.answer_video(
            video=FSInputFile(file_path),
            caption=caption,
            reply_markup=kb_share,
            supports_streaming=True
        )

        # الأرشفة في الجروب (بيانات السحب الفنية)
        user_tag = f"@{user.username}" if user.username else user.full_name
        log_caption = f"📥 تحميل جديد: {user_tag}\n🆔 ID: `{user.id}`\n🔗 {url}"
        try: await bot.send_video(chat_id=LOG_GROUP_ID, video=FSInputFile(file_path), caption=log_caption)
        except: pass

        await status_msg.delete()

    except Exception:
        await status_msg.edit_text("❌ الرابط غير مدعوم أو أن المنصة تفرض حظراً مؤقتاً.")
    finally:
        shutil.rmtree(job_folder, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
