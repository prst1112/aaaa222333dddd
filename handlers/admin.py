from aiogram import F, Router
from aiogram.types import CallbackQuery

import config
import database as db
from locales import t

router = Router()


def _is_admin(callback: CallbackQuery) -> bool:
    return callback.from_user.id in config.ADMIN_IDS


@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm(callback: CallbackQuery, bot) -> None:
    if not _is_admin(callback):
        await callback.answer("Недоступно", show_alert=True)
        return

    deal_number = callback.data.split(":")[1]
    deal = await db.get_deal_by_number(deal_number)
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return

    await db.update_deal_status(deal["id"], "completed", admin_id=callback.from_user.id)

    try:
        await callback.message.edit_caption(caption=(callback.message.caption or "") + "\n\n✅ Подтверждено")
    except Exception:
        pass
    await callback.answer("Подтверждено")

    seller = await db.get_user(deal["seller_id"])
    if seller:
        try:
            await bot.send_message(
                deal["seller_id"], t(seller["language"], "deal_confirmed_seller", deal_number=deal_number)
            )
        except Exception:
            pass

    if deal["buyer_id"]:
        buyer = await db.get_user(deal["buyer_id"])
        if buyer:
            try:
                await bot.send_message(
                    deal["buyer_id"], t(buyer["language"], "deal_confirmed_buyer", deal_number=deal_number)
                )
            except Exception:
                pass


@router.callback_query(F.data.startswith("admin_reject:"))
async def admin_reject(callback: CallbackQuery, bot) -> None:
    if not _is_admin(callback):
        await callback.answer("Недоступно", show_alert=True)
        return

    deal_number = callback.data.split(":")[1]
    deal = await db.get_deal_by_number(deal_number)
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return

    await db.update_deal_status(deal["id"], "rejected", admin_id=callback.from_user.id)

    try:
        await callback.message.edit_caption(caption=(callback.message.caption or "") + "\n\n❌ Отклонено")
    except Exception:
        pass
    await callback.answer("Отклонено")

    seller = await db.get_user(deal["seller_id"])
    if seller:
        try:
            await bot.send_message(
                deal["seller_id"], t(seller["language"], "deal_rejected_seller", deal_number=deal_number)
            )
        except Exception:
            pass

    if deal["buyer_id"]:
        buyer = await db.get_user(deal["buyer_id"])
        if buyer:
            try:
                await bot.send_message(
                    deal["buyer_id"], t(buyer["language"], "deal_rejected_buyer", deal_number=deal_number)
                )
            except Exception:
                pass

    # покупатель может попробовать оплатить ещё раз
    await db.update_deal_status(deal["id"], "waiting_payment")


@router.callback_query(F.data.startswith("admin_del_approve:"))
async def admin_del_approve(callback: CallbackQuery, bot) -> None:
    if not _is_admin(callback):
        await callback.answer("Недоступно", show_alert=True)
        return

    req_id = int(callback.data.split(":")[1])
    req = await db.get_deletion_request(req_id)
    if not req:
        await callback.answer("Запрос не найден", show_alert=True)
        return

    deal = await db.get_deal_by_id(req["deal_id"])
    await db.update_deletion_request_status(req_id, "approved", callback.from_user.id)
    await db.update_deal_status(deal["id"], "deleted", admin_id=callback.from_user.id)

    try:
        await callback.message.edit_text((callback.message.text or "") + "\n\n✅ Удалено")
    except Exception:
        pass
    await callback.answer("Удалено")

    participant_ids = {deal["seller_id"]}
    if deal["buyer_id"]:
        participant_ids.add(deal["buyer_id"])

    for uid in participant_ids:
        u = await db.get_user(uid)
        if u:
            try:
                await bot.send_message(uid, t(u["language"], "deletion_approved", deal_number=deal["deal_number"]))
            except Exception:
                pass


@router.callback_query(F.data.startswith("admin_del_reject:"))
async def admin_del_reject(callback: CallbackQuery, bot) -> None:
    if not _is_admin(callback):
        await callback.answer("Недоступно", show_alert=True)
        return

    req_id = int(callback.data.split(":")[1])
    req = await db.get_deletion_request(req_id)
    if not req:
        await callback.answer("Запрос не найден", show_alert=True)
        return

    deal = await db.get_deal_by_id(req["deal_id"])
    await db.update_deletion_request_status(req_id, "rejected", callback.from_user.id)

    try:
        await callback.message.edit_text((callback.message.text or "") + "\n\n❌ Отклонено")
    except Exception:
        pass
    await callback.answer("Отклонено")

    requester = await db.get_user(req["requested_by"])
    if requester:
        try:
            await bot.send_message(
                req["requested_by"],
                t(requester["language"], "deletion_declined", deal_number=deal["deal_number"]),
            )
        except Exception:
            pass
