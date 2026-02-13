import re

def validate_phone(phone: str) -> bool:
    pattern = r'^[\+]?[0-9]{10,15}$'
    return bool(re.match(pattern, phone))

def validate_rating(rating: int) -> bool:
    return 1 <= rating <= 5

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))