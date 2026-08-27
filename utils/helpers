import uuid

from locales import LOCALES

MENU_KEYS = [
    "menu_create_deal",
    "menu_profile",
    "menu_withdraw",
    "menu_requisites",
    "menu_language",
    "menu_support",
]

CURRENCY_ICONS = {
    "card": "💳",
    "gram": "💎",
    "stars": "⭐",
}


def generate_deal_number() -> str:
    """Короткий публичный номер сделки, например 37410e49."""
    return uuid.uuid4().hex[:8]


def format_amount(amount: float, currency: str, lang: str = "ru") -> str:
    if float(amount) == int(amount):
        amount_str = str(int(amount))
    else:
        amount_str = f"{amount:.2f}".rstrip("0").rstrip(".")
    icon = CURRENCY_ICONS.get(currency, "")
    return f"{amount_str} {icon}".strip()


def is_menu_command(text: str | None) -> bool:
    """Проверяет, не является ли текст нажатием одной из кнопок главного меню
    (на любом из языков) — используется, чтобы не "проглатывать" переключение
    меню, если юзер передумал посреди FSM-сценария (создание сделки и т.п.)."""
    if not text:
        return False
    for key in MENU_KEYS:
        for texts in LOCALES.values():
            if texts.get(key) == text:
                return True
    return False

