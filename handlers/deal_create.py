from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import database as db
from keyboards.inline import currency_kb
from keyboards.main_menu import main_menu_kb
from locales import all_variants, t
from states.states import DealCreate
from utils.helpers import format_amount, generate_deal_number, is_menu_command

router = Router()


@router.message(F.text.in_(all_variants("menu_create_deal")))
async def start_deal_creation(message: Message, state: FSMContext) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]
    await state.set_state(DealCreate.choosing_currency)
    await message.answer(t(lang, "choose_currency"), reply_markup=currency_kb(lang))


@router.callback_query(DealCreate.choosing_currency, F.data.startswith("currency:"))
async def choose_currency(callback: CallbackQuery, state: FSMContext) -> None:
    currency = callback.data.split(":")[1]
    user = await db.get_or_create_user(callback.from_user)
    lang = user["language"]

    await state.update_data(currency=currency)
    await state.set_state(DealCreate.entering_amount)
    await callback.message.edit_text(t(lang, "enter_amount"))
    await callback.answer()


@router.message(DealCreate.entering_amount)
async def enter_amount(message: Message, state: FSMContext) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]

    if is_menu_command(message.text):
        await state.clear()
        await message.answer(t(lang, "action_cancelled"), reply_markup=main_menu_kb(lang))
        return

    raw = (message.text or "").replace(",", ".").strip()
    try:
        amount = float(raw)
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(t(lang, "invalid_amount"))
        return

    await state.update_data(amount=amount)
    await state.set_state(DealCreate.entering_description)
    await message.answer(t(lang, "enter_description"))


@router.message(DealCreate.entering_description)
async def enter_description(message: Message, state: FSMContext) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]

    if is_menu_command(message.text):
        await state.clear()
        await message.answer(t(lang, "action_cancelled"), reply_markup=main_menu_kb(lang))
        return

    description = (message.text or "").strip()[:500]
    if not description:
        await message.answer(t(lang, "enter_description"))
        return

    data = await state.get_data()
    deal_number = generate_deal_number()

    await db.create_deal(
        deal_number=deal_number,
        seller_id=message.from_user.id,
        currency=data["currency"],
        amount=data["amount"],
        description=description,
    )
    await state.clear()

    link = f"https://t.me/{config.BOT_USERNAME}?start={deal_number}"
    amount_str = format_amount(data["amount"], data["currency"], lang)

    await message.answer(
        t(
            lang,
            "deal_created",
            deal_number=deal_number,
            amount=amount_str,
            description=description,
            link=link,
        ),
        reply_markup=main_menu_kb(lang),
        disable_web_page_preview=True,
    )
