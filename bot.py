import os
import re
import asyncio
import logging
import shutil
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import yt_dlp
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    FSInputFile,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.enums import ChatAction

# =========================
# CONFIG (إعدادات السيادة)
# =========================
TOKEN = "8631339057:AAEXSbvqyLUFdVIJUdgmt46VtMvrk8ZXl98"
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

# حد الإرسال في تليجرام (50 ميجا للبوتات العادية)
MAX_FILE_SIZE_BYTES = 48 * 1024 * 1024
MAX_WORKERS = 4
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("Hyper_Downloader")
EXECUTOR = ThreadPoolExecutor(max_workers=MAX_WORKERS)

bot = Bot(TOKEN)
dp = Dispatcher()

# تخزين مؤقت للرابط الذي أرسله المستخدم حتى يختار الجودة
PENDING_URLS: dict[int, str] = {}

# =========================
# CORE FUNCTIONS (محرر القيود)
# =========================
def build_ydl_opts(output_template: str, quality: str = "best") -> dict:
    """إعدادات التحميل"""
    if quality == "360":
        selected_format = (
            "bestvideo[height<=360]+bestaudio/"
            "best[height<=360]/best"
        )
    elif quality == "720":
        selected_format = (
            "bestvideo[height<=720]+bestaudio/"
            "best[height<=720]/best"
        )
    else:
        selected_format = "bestvideo+bestaudio/best"

    return {
        "outtmpl": output_template,
        "format": selected_format,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "continuedl": True,
        "retries": 15,
        "fragment_retries": 15,
        "file_access_retries": 10,
        "socket_timeout": 30,
        "concurrent_fragment_downloads": 4,
        "restrictfilenames": True,
        "http_chunk_size": 10485760,
        "external_downloader": "aria2c",
        "external_downloader_args": [
            "-x", "16",
            "-s", "16",
            "-k", "1M",
            "--summary-interval=0",
        ],
        # "cookiefile": "cookies.txt",
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }


def download_media(url: str, folder: Path, quality: str) -> tuple[Path, dict]:
    unique_prefix = uuid.uuid4().hex[:8]
    output_template = str(folder / f"{unique_prefix}.%(title).80s.%(ext)s")
    ydl_opts = build_ydl_opts(output_template, quality)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    files = [p for p in folder.iterdir() if p.is_file() and not p.name.endswith(".part")]
    if not files:
        raise FileNotFoundError("فشل استخراج الملف")

    files.sort(key=lambda p: p.stat().st_size, reverse=True)
    return files[0], info


def quality_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="360p", callback_data="q_360"),
                InlineKeyboardButton(text="720p", callback_data="q_720"),
            ],
            [
                InlineKeyboardButton(text="Best", callback_data="q_best"),
            ],
        ]
    )


# =========================
# HANDLERS (التنفيذ الصامت)
# =========================
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "✅ البوت جاهز.\n"
        "ابعت رابط الفيديو، وبعدها اختار الجودة."
    )


@dp.message()
async def message_handler(message: Message):
    url_match = URL_RE.search(message.text or "")
    if not url_match:
        await message.answer("ابعت رابط صحيح أولاً.")
        return

    url = url_match.group(0)
    user_id = message.from_user.id if message.from_user else 0
    PENDING_URLS[user_id] = url

    await message.answer(
        "اختر جودة التحميل:",
        reply_markup=quality_keyboard()
    )


@dp.callback_query(lambda c: c.data and c.data.startswith("q_"))
async def quality_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    url = PENDING_URLS.get(user_id)

    if not url:
        await callback.answer("ابعت الرابط مرة ثانية.", show_alert=True)
        return

    quality = callback.data.split("_", 1)[1]

    job_folder = DOWNLOADS_DIR / str(user_id) / uuid.uuid4().hex
    job_folder.mkdir(parents=True, exist_ok=True)

    await callback.message.edit_text(f"🚀 جاري التحميل بجودة {quality}...")
    await bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_VIDEO)

    try:
        loop = asyncio.get_running_loop()
        file_path, info = await loop.run_in_executor(
            EXECUTOR,
            download_media,
            url,
            job_folder,
            quality
        )

        file_size = file_path.stat().st_size
        file_size_mb = file_size // 1024 // 1024

        if file_size > MAX_FILE_SIZE_BYTES:
            await callback.message.edit_text(
                f"⚠️ الملف اتحمل لكن حجمه كبير للإرسال عبر البوت: {file_size_mb}MB"
            )
            return

        title = (info.get("title", "Video") or "Video")[:900]

        try:
            await callback.message.answer_video(
                video=FSInputFile(file_path),
                caption=f"🎬 {title}\n🔥 الجودة: {quality}",
                supports_streaming=True
            )
        except Exception:
            await callback.message.answer_document(
                document=FSInputFile(file_path),
                caption=f"🎬 {title}\n🔥 الجودة: {quality}"
            )

        await callback.message.delete()
        PENDING_URLS.pop(user_id, None)

    except Exception as e:
        await callback.message.edit_text("❌ حصل خطأ أثناء التحميل أو الإرسال.")
        logger.error(f"Error: {e}", exc_info=True)

    finally:
        shutil.rmtree(job_folder, ignore_errors=True)
        await callback.answer()


if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
