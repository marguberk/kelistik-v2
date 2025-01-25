import re
from datetime import datetime
from flask import g

def validate_iin_bin(iin):
    """
    Упрощенная валидация ИИН/БИН
    """
    if not iin.isdigit():
        return False, g.translations['validation_iin']
    if len(iin) != 12:
        return False, g.translations['validation_iin']
    return True, ""

def validate_phone(phone):
    """
    Проверяет корректность номера телефона
    """
    if not phone.startswith('+7'):
        return False, g.translations['validation_phone']
    if len(phone) != 12:
        return False, g.translations['validation_phone']
    if not phone[2:].isdigit():
        return False, g.translations['validation_phone']
    return True, ""

def validate_iban(iban):
    """
    Проверяет корректность IBAN Казахстана
    """
    if not iban.startswith('KZ'):
        return False, g.translations['validation_iban']
    if len(iban) != 20:
        return False, g.translations['validation_iban']
    if not iban[2:].isdigit():
        return False, g.translations['validation_iban']
    return True, "" 