from num2words import num2words
from datetime import datetime
import re


def number_to_words(amount: float) -> str:
    """Преобразует сумму в тенге прописью (русский)."""
    try:
        whole = int(amount)
        words = num2words(whole, lang='ru')
        words = words.capitalize()
        return f"{words} тенге"
    except Exception:
        return str(amount)


def format_amount(amount: float) -> str:
    """Форматирует сумму: 1 250 000"""
    return f"{amount:,.0f}".replace(",", " ")


def format_date(date_str: str = None) -> str:
    """Форматирует дату в вид «09 ноября 2026 г.»"""
    if not date_str:
        dt = datetime.now()
    else:
        for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %m %Y"):
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            dt = datetime.now()

    months = [
        "", "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return f"{dt.day} {months[dt.month]} {dt.year} г."


def clean_iin(iin: str) -> str:
    """Оставляет только цифры ИИН."""
    return re.sub(r"\D", "", iin)[:12]


def validate_iin(iin: str) -> bool:
    """Простая проверка ИИН (12 цифр)."""
    cleaned = clean_iin(iin)
    return len(cleaned) == 12 and cleaned.isdigit()