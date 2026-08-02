"""
utils/validators.py – Input validation helpers.
"""
import re


def validate_email(email: str) -> bool:
    pattern = r'^[\w\.\+\-]+@[\w\-]+(?:\.[\w\-]+)*\.[a-z]{2,}$'
    return bool(re.match(pattern, email.strip().lower()))


def validate_password(password: str) -> bool:
    return len(password) >= 8


def validate_phone(phone: str) -> bool:
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15


def validate_time_format(time_str: str) -> bool:
    pattern = r'^([01]\d|2[0-3]):([0-5]\d)$'
    return bool(re.match(pattern, time_str.strip()))


def sanitize_text(text: str, max_length: int = 1000) -> str:
    return text.strip()[:max_length]
