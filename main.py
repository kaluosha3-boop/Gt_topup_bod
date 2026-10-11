import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# إعدادات البوت وقاعدة البيانات
TOKEN = "8953457333:AAHKAisEWNziIWnnG15o_322GmJQ2dAiiRs"
# ضع توكن البوت الخاص بك هنا بين العلامتين
ADMIN_ID = 1332736076         # ضع الآي دي (ID) الخاص بك هنا كمسؤول

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# تهيئة قاعدة البيانات SQLite3 للمنتجات والطلبات
def init_db():
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            category TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_info TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# حالات المحادثة للطلب والشحن المباشر
class OrderState(StatesGroup):
    waiting_for_id = State()
    confirming_payment = State()

# القائمة الرئيسية للبوت
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 متجر الأكواد الرقمية", callback_data="shop_codes"))
    builder.row(types.InlineKeyboardButton(text="⚡ شحن الألعاب المباشر (ID)", callback_data="shop_topups"))
    builder.row(types.InlineKeyboardButton(text="📞 التواصل مع الدعم", callback_data="support"))

    await message.answer(
        f"أهلاً بك يا <b>{message.from_user.full_name}</b> في متجرك الرقمي الآمن!\nاختر ما يناسب طلبك من الأسفل:",
        reply_markup=builder.as_markup()
    )

# قسم عرض الأكواد الرقمية
@router.callback_query(F.data == "shop_codes")
async def show_codes(callback: types.CallbackQuery):
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price FROM products WHERE category='code'")
    products = cursor.fetchall()
    conn.close()

    builder = InlineKeyboardBuilder()
    if products:
        for p in products:
            builder.row(types.InlineKeyboardButton(text=f"{p[1]} - {p[2]} ج.م", callback_data=f"buy_code_{p[0]}"))
    else:
        builder.row(types.InlineKeyboardButton(text="لا توجد منتجات متاحة حالياً", callback_data="none"))

    builder.row(types.InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu"))
    await callback.message.edit_text("اختر المنتج الرقمي المطلوب:", reply_markup=builder.as_markup())
    await callback.answer()

# قسم شحن الألعاب المباشر
@router.callback_query(F.data == "shop_topups")
async def show_topups(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💎 شحن شدات ببجي (ID)", callback_data="topup_pubg"))
    builder.row(types.InlineKeyboardButton(text="🔥 شحن جواهر فري فاير (ID)", callback_data="topup_ff"))
    builder.row(types.InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu"))

    await callback.message.edit_text("اختر اللعبة المراد الشحن لها بالـ ID:", reply_markup=builder.as_markup())
    await callback.answer()

# زر التواصل مع الدعم
@router.callback_query(F.data == "support")
async def contact_support(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu"))

    await callback.message.edit_text("لأي استفسار أو مشكلة، يمكنك مراسلة الدعم الفني مباشرة عبر الإدارة.", reply_markup=builder.as_markup())
    await callback.answer()

# العودة للقائمة الرئيسية
@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 متجر الأكواد الرقمية", callback_data="shop_codes"))
    builder.row(types.InlineKeyboardButton(text="⚡ شحن الألعاب المباشر (ID)", callback_data="shop_topups"))
    builder.row(types.InlineKeyboardButton(text="📞 التواصل مع الدعم", callback_data="support"))

    await callback.message.edit_text("القائمة الرئيسية:", reply_markup=builder.as_markup())
    await callback.answer()

dp.include_router(router)

# تشغيل البوت
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
