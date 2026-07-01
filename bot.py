import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from openai import AsyncOpenAI

# Konfiguratsiyani yuklash
try:
    from config import BOT_TOKEN, OPENAI_API_KEY
except ImportError:
    print("Xatolik: config.py fayli topilmadi!")
    sys.exit(1)

# Loggingni sozlash
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# API Kalitlarni tekshirish
if not BOT_TOKEN or BOT_TOKEN == "telegram_bot_tokeningiz":
    logger.error("XATOLIK: config.py faylida BOT_TOKEN ko'rsatilmagan!")
    sys.exit(1)

if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("YOUR_"):
    logger.error("XATOLIK: config.py faylida OPENAI_API_KEY ko'rsatilmagan!")
    sys.exit(1)

# OpenAI asinxron mijozini sozlash
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# AI modeli sozlamalari (Tizim ko'rsatmasi)
SYSTEM_INSTRUCTION = (
    "Siz faqatgina dasturlash, axborot texnologiyalari (IT) va kompyuter ilmlariga (Computer Science) oid savollarga javob beradigan yordamchisiz. "
    "Dasturlash tillari, algoritmlar, ma'lumotlar bazalari, dasturiy ta'minot arxitekturasi, veb-dasturlash, tarmoqlar va shunga o'xshash faqat AKT/IT mavzularidan tashqaridagi savollarga javob bermang. "
    "Agar foydalanuvchi boshqa mavzuda (masalan, ovqat pishirish, geografiya, tarix, musiqa, umumiy suhbatlar, siyosat va hokazo) savol bersa, "
    "muloyimlik bilan faqat dasturlash va IT sohasiga oid savollarga javob bera olishingizni aytib, savolga javob berishni rad eting. "
    "Sizga berilgan savol qaysi tilda yozilgan bo'lsa (o'zbek, rus, ingliz va hokazo), javobni ham o'sha tilda qaytaring. "
    "Javobingiz tushunarli, aniq va misollar (kod namunalari) bilan boyitilgan bo'lsin."
)

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
router = Router()
dp.include_router(router)

# /start komandasi uchun handler
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user_name = message.from_user.full_name
    welcome_text = (
        f"Salom, *{user_name}*!\n\n"
        "Men faqat dasturlash va IT sohasiga oid savollarga javob beradigan sun'iy intellekt botiman. 💻\n\n"
        "Menga dasturlash tillari, algoritmlar, xatoliklarni tuzatish (debugging) yoki IT sohasidagi istalgan mavzu bo'yicha savol yo'llashingiz mumkin."
    )
    await message.answer(welcome_text)

# Xabarlarni qabul qilish va OpenAI-ga yuborish handler-i
@router.message(F.text)
async def handle_message(message: types.Message):
    # Foydalanuvchiga bot "yozayotgani" haqida belgi yuborish
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # OpenAI API-ga asinxron so'rov yuborish
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": message.text}
            ],
            temperature=0.7
        )
        
        # Olingan javob matnini ajratib olish
        reply_text = response.choices[0].message.content
        
        # Javobni foydalanuvchiga yuborish
        await message.answer(reply_text)
        
    except Exception as e:
        logger.error(f"Xabarga javob berishda xatolik yuz berdi: {e}")
        await message.answer("Kechirasiz, savolingizga javob olishda xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring.")

# Botni ishga tushirish
async def main():
    logger.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
