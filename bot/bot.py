import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, IP_DATA
from database import init_db, add_client, get_client_by_iin, search_clients, get_all_clients, save_document
from generator import create_receipt, create_guarantee_letter, create_contract
from utils import clean_iin, validate_iin, format_amount, number_to_words

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


class DocForm(StatesGroup):
    choosing_type = State()
    choosing_client = State()
    entering_name = State()
    entering_iin = State()
    entering_product = State()
    entering_amount = State()
    entering_date = State()
    installment_question = State()
    entering_pay_from = State()
    entering_pay_to = State()
    confirm = State()


def main_menu():
    kb = [
        [InlineKeyboardButton(text="📄 Создать документ", callback_data="create_doc")],
        [InlineKeyboardButton(text="👥 Клиенты", callback_data="clients_menu")],
        [InlineKeyboardButton(text="⚙️ Настройки ИП", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def doc_types_kb():
    kb = [
        [InlineKeyboardButton(text="🧾 Расписка", callback_data="type_receipt")],
        [InlineKeyboardButton(text="📜 Гарантийное письмо", callback_data="type_guarantee")],
        [InlineKeyboardButton(text="📋 Договор", callback_data="type_contract")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def yes_no_kb(yes_data: str, no_data: str):
    kb = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data=yes_data),
            InlineKeyboardButton(text="❌ Нет", callback_data=no_data),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def confirm_kb():
    kb = [
        [InlineKeyboardButton(text="✅ Сгенерировать", callback_data="generate")],
        [InlineKeyboardButton(text="✏️ Изменить", callback_data="edit")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"👋 Привет! Я бот для быстрой генерации документов.\n\n"
        f"Ваш ИП: <b>{IP_DATA['name']}</b>\n\n"
        f"Выберите действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        f"👋 Главное меню\n\nВаш ИП: <b>{IP_DATA['name']}</b>",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "create_doc")
async def create_doc_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DocForm.choosing_type)
    await callback.message.edit_text(
        "Выберите тип документа:",
        reply_markup=doc_types_kb()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("type_"))
async def choose_type(callback: CallbackQuery, state: FSMContext):
    doc_type = callback.data.replace("type_", "")
    await state.update_data(doc_type=doc_type)
    await state.set_state(DocForm.choosing_client)
    await callback.message.edit_text(
        "Введите <b>ИИН</b> клиента или часть ФИО для поиска.\n"
        "Или напишите <b>новый</b>, чтобы создать нового клиента.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(DocForm.choosing_client)
async def process_client_search(message: Message, state: FSMContext):
    text = message.text.strip()

    if text.lower() == "новый":
        await state.set_state(DocForm.entering_name)
        await message.answer("Введите <b>ФИО клиента</b> полностью:", parse_mode="HTML")
        return

    clients = await search_clients(text)
    if not clients:
        await message.answer(
            "Клиент не найден.\nВведите ИИН/ФИО ещё раз или напишите <b>новый</b>.",
            parse_mode="HTML"
        )
        return

    if len(clients) == 1:
        client = clients[0]
        await state.update_data(
            client_id=client["id"],
            client_name=client["full_name"],
            client_iin=client["iin"]
        )
        await state.set_state(DocForm.entering_product)
        await message.answer(
            f"✅ Клиент: <b>{client['full_name']}</b>\nИИН: {client['iin']}\n\n"
            f"Введите <b>название товара / услуги</b>:",
            parse_mode="HTML"
        )
    else:
        buttons = []
        for c in clients[:8]:
            buttons.append([InlineKeyboardButton(
                text=f"{c['full_name']} ({c['iin']})",
                callback_data=f"select_client_{c['id']}"
            )])
        buttons.append([InlineKeyboardButton(text="➕ Новый клиент", callback_data="new_client")])
        await message.answer(
            "Найдено несколько клиентов. Выберите:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@router.callback_query(F.data.startswith("select_client_"))
async def select_client(callback: CallbackQuery, state: FSMContext):
    client_id = int(callback.data.replace("select_client_", ""))
    clients = await get_all_clients(200)
    client = next((c for c in clients if c["id"] == client_id), None)
    if not client:
        await callback.answer("Клиент не найден", show_alert=True)
        return

    await state.update_data(
        client_id=client["id"],
        client_name=client["full_name"],
        client_iin=client["iin"]
    )
    await state.set_state(DocForm.entering_product)
    await callback.message.edit_text(
        f"✅ Клиент: <b>{client['full_name']}</b>\nИИН: {client['iin']}\n\n"
        f"Введите <b>название товара / услуги</b>:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "new_client")
async def new_client_cb(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DocForm.entering_name)
    await callback.message.edit_text("Введите <b>ФИО клиента</b> полностью:", parse_mode="HTML")
    await callback.answer()


@router.message(DocForm.entering_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 5:
        await message.answer("ФИО слишком короткое. Введите полностью:")
        return
    await state.update_data(client_name=name)
    await state.set_state(DocForm.entering_iin)
    await message.answer("Введите <b>ИИН клиента</b> (12 цифр):", parse_mode="HTML")


@router.message(DocForm.entering_iin)
async def process_iin(message: Message, state: FSMContext):
    iin = clean_iin(message.text)
    if not validate_iin(iin):
        await message.answer("ИИН должен содержать 12 цифр. Попробуйте ещё раз:")
        return

    existing = await get_client_by_iin(iin)
    data = await state.get_data()
    name = data["client_name"]

    if existing:
        await state.update_data(client_id=existing["id"], client_iin=iin)
        await message.answer(f"Клиент с таким ИИН уже есть: {existing['full_name']}")
    else:
        client_id = await add_client(name, iin)
        await state.update_data(client_id=client_id, client_iin=iin)

    await state.set_state(DocForm.entering_product)
    await message.answer("Введите <b>название товара / услуги</b>:", parse_mode="HTML")


@router.message(DocForm.entering_product)
async def process_product(message: Message, state: FSMContext):
    product = message.text.strip()
    if len(product) < 2:
        await message.answer("Название слишком короткое:")
        return
    await state.update_data(product=product)
    await state.set_state(DocForm.entering_amount)
    await message.answer("Введите <b>сумму</b> цифрами (например: 150000):", parse_mode="HTML")


@router.message(DocForm.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    text = message.text.replace(" ", "").replace(",", ".")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму (только цифры):")
        return

    await state.update_data(amount=amount)
    await state.set_state(DocForm.entering_date)
    await message.answer(
        "Введите <b>дату</b> документа в формате ДД.ММ.ГГГГ\n"
        "Или напишите <b>сегодня</b>:",
        parse_mode="HTML"
    )


@router.message(DocForm.entering_date)
async def process_date(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    if text in ("сегодня", "today", "сейчас"):
        date_str = None
    else:
        date_str = text

    await state.update_data(date=date_str)

    data = await state.get_data()
    if data["doc_type"] in ("receipt", "contract"):
        await state.set_state(DocForm.installment_question)
        await message.answer(
            "Это оплата в <b>рассрочку</b>?",
            reply_markup=yes_no_kb("installment_yes", "installment_no"),
            parse_mode="HTML"
        )
    else:
        await state.update_data(installment=False)
        await show_confirm(message, state)


@router.callback_query(F.data == "installment_yes")
async def installment_yes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(installment=True)
    await state.set_state(DocForm.entering_pay_from)
    await callback.message.edit_text("Введите дату начала оплаты (например: 01.12.2026):")
    await callback.answer()


@router.callback_query(F.data == "installment_no")
async def installment_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(installment=False)
    await show_confirm(callback.message, state)
    await callback.answer()


@router.message(DocForm.entering_pay_from)
async def process_pay_from(message: Message, state: FSMContext):
    await state.update_data(pay_from=message.text.strip())
    await state.set_state(DocForm.entering_pay_to)
    await message.answer("Введите дату окончания оплаты (например: 01.06.2027):")


@router.message(DocForm.entering_pay_to)
async def process_pay_to(message: Message, state: FSMContext):
    await state.update_data(pay_to=message.text.strip())
    await show_confirm(message, state)


async def show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data["amount"]
    text = (
        f"<b>Проверьте данные:</b>\n\n"
        f"📄 Тип: { {'receipt': 'Расписка', 'guarantee': 'Гарантийное письмо', 'contract': 'Договор'}[data['doc_type']] }\n"
        f"👤 Клиент: {data['client_name']}\n"
        f"🆔 ИИН: {data['client_iin']}\n"
        f"📦 Товар: {data['product']}\n"
        f"💰 Сумма: {format_amount(amount)} ({number_to_words(amount)})\n"
    )
    if data.get("installment"):
        text += f"📅 Рассрочка: с {data.get('pay_from')} по {data.get('pay_to')}\n"

    await state.set_state(DocForm.confirm)
    await message.answer(text, reply_markup=confirm_kb(), parse_mode="HTML")


@router.callback_query(F.data == "generate")
async def generate_doc(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("⏳ Генерирую документ...")

    try:
        if data["doc_type"] == "receipt":
            path = create_receipt(data)
        elif data["doc_type"] == "guarantee":
            path = create_guarantee_letter(data)
        else:
            path = create_contract(data)

        await save_document(
            data.get("client_id"),
            data["doc_type"],
            data["amount"],
            data["product"]
        )

        file = FSInputFile(path)
        await callback.message.answer_document(
            file,
            caption=f"✅ Документ готов!\n{data['client_name']} — {format_amount(data['amount'])} ₸"
        )

        try:
            os.remove(path)
        except Exception:
            pass

        await callback.message.answer("Что дальше?", reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.exception("Ошибка генерации")
        await callback.message.answer(f"❌ Ошибка: {e}\nПопробуйте ещё раз.", reply_markup=main_menu())
        await state.clear()

    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_form(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Отменено.", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "edit")
async def edit_form(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DocForm.choosing_type)
    await callback.message.edit_text("Выберите тип документа заново:", reply_markup=doc_types_kb())
    await callback.answer()


@router.callback_query(F.data == "clients_menu")
async def clients_menu(callback: CallbackQuery):
    clients = await get_all_clients(20)
    if not clients:
        text = "Клиентов пока нет."
    else:
        text = "<b>Последние клиенты:</b>\n\n"
        for c in clients:
            text += f"• {c['full_name']} — {c['iin']}\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад", callback_data="back_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "settings")
async def settings(callback: CallbackQuery):
    text = (
        f"<b>Текущие данные ИП:</b>\n\n"
        f"Название: {IP_DATA['name']}\n"
        f"ИИН: {IP_DATA['iin']}\n"
        f"Адрес: {IP_DATA['address']}\n"
        f"Телефон: {IP_DATA['phone']}\n"
        f"Банк: {IP_DATA['bank']}\n"
        f"ИИК: {IP_DATA['iik']}\n"
        f"БИК: {IP_DATA['bik']}\n\n"
        f"<i>Чтобы изменить — отредактируйте файл config.py и перезапустите бота.</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад", callback_data="back_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


async def main():
    if not BOT_TOKEN:
        print("❌ Укажите BOT_TOKEN в .env файле!")
        return

    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    print("✅ Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())