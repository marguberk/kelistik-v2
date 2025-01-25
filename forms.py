from flask import g
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError, Email, Regexp
from validators import validate_iin_bin, validate_phone, validate_iban

class PhoneNumberValidator:
    def __call__(self, form, field):
        # Очищаем номер от всех символов кроме цифр и +
        number = ''.join(c for c in field.data if c.isdigit() or c == '+')
        
        if not number.startswith('+7'):
            raise ValidationError('Номер должен начинаться с +7')
            
        # Проверяем длину (должно быть 12 символов включая +7)
        if len(number) != 12:
            raise ValidationError('Номер должен содержать 11 цифр')
        
        # Проверяем что все символы после +7 - цифры
        if not number[2:].isdigit():
            raise ValidationError('Номер должен содержать только цифры после +7')

class ContractForm(FlaskForm):
    # Данные исполнителя
    contractor_name = StringField(
        validators=[
            DataRequired(message=lambda: g.translations.get('validation_required')),
            Length(min=2, max=100)
        ])
    
    def validate_contractor_iin(form, field):
        is_valid, message = validate_iin_bin(field.data)
        if not is_valid:
            raise ValidationError(message)
    
    contractor_iin = StringField(
        validators=[
            DataRequired(),
            Length(min=12, max=12),
            Regexp(r'^\d{12}$', message=lambda: g.translations['validation_iin'])
        ])
    
    contractor_phone = StringField('Телефон Исполнителя', 
        render_kw={"type": "tel", "placeholder": "+7 (___) ___-__-__"},
        validators=[
            DataRequired(message='Это поле обязательно'),
            PhoneNumberValidator()
        ])
    
    contractor_address = StringField('Адрес Исполнителя',
        validators=[DataRequired(), Length(min=10, max=200)])
    
    contractor_bank = StringField('Банк Исполнителя',
        validators=[DataRequired()])
    
    def validate_contractor_iban(form, field):
        is_valid, message = validate_iban(field.data)
        if not is_valid:
            raise ValidationError(message)
    
    contractor_iban = StringField(
        validators=[
            DataRequired(),
            Length(min=20, max=20),
            Regexp(r'^[A-Z]{2}\d{18}$', message=lambda: g.translations['validation_iban'])
        ])
    
    # Данные заказчика
    client_name = StringField('ФИО Заказчика', 
        validators=[DataRequired(), Length(min=2, max=100)])
    
    def validate_client_iin(form, field):
        is_valid, message = validate_iin_bin(field.data)
        if not is_valid:
            raise ValidationError(message)
    
    client_iin = StringField(
        validators=[
            DataRequired(),
            Length(min=12, max=12),
            Regexp(r'^\d{12}$', message=lambda: g.translations['validation_iin'])
        ])
    
    client_phone = StringField('Телефон Заказчика', 
        render_kw={"type": "tel", "placeholder": "+7 (___) ___-__-__"},
        validators=[
            DataRequired(message='Это поле обязательно'),
            PhoneNumberValidator()
        ])
    
    client_address = StringField('Адрес Заказчика',
        validators=[DataRequired(), Length(min=10, max=200)])
    
    # Данные услуги
    def get_service_choices():
        return [
            ('web_design', g.translations.get('service_type_web')),
            ('ui_ux', g.translations.get('service_type_ui')),
            ('graphic_design', g.translations.get('service_type_graphic')),
            ('programming', g.translations.get('service_type_programming')),
            ('mobile_dev', g.translations.get('service_type_mobile')),
            ('targeting', g.translations.get('service_type_targeting')),
            ('seo', g.translations.get('service_type_seo')),
            ('smm', g.translations.get('service_type_smm')),
            ('copywriting', g.translations.get('service_type_copywriting')),
            ('consulting', g.translations.get('service_type_consulting'))
        ]

    def get_prepayment_choices():
        return [
            ('30%', '30%'),
            ('50%', '50%'),
            ('70%', '70%'),
            ('100%', '100%')
        ]

    def get_revisions_choices():
        return [
            ('2', g.translations['revisions_2']),
            ('3', g.translations['revisions_3']),
            ('5', g.translations['revisions_5']),
            ('unlimited', g.translations['revisions_unlimited'])
        ]

    def get_rights_choices():
        return [
            ('full', g.translations['rights_full']),
            ('partial', g.translations['rights_partial']),
            ('license', g.translations['rights_license'])
        ]

    def get_portfolio_choices():
        return [
            ('yes', g.translations['portfolio_yes']),
            ('no', g.translations['portfolio_no'])
        ]

    def get_delay_choices():
        return [
            ('3', g.translations['delay_3']),
            ('5', g.translations['delay_5']),
            ('7', g.translations['delay_7']),
            ('10', g.translations['delay_10'])
        ]

    service_type = SelectField('Тип услуги', choices=get_service_choices, validators=[DataRequired()])
    service_description = TextAreaField(
        render_kw={
            "placeholder": "Подробно опишите, что будет сделано в рамках услуги. Например:\n" +
                         "- Конкретные работы и их объем\n" +
                         "- Технические требования и особенности\n" +
                         "- Ожидаемые результаты\n" +
                         "- Формат сдачи работ",
            "rows": "6"
        },
        validators=[
            DataRequired(message=lambda: g.translations['validation_required']),
            Length(
                min=10, max=1000,
                message=lambda: g.translations['validation_description_length']
            )
        ])
    
    # Условия договора
    price = DecimalField('Стоимость услуг', 
        validators=[DataRequired()])
    prepayment_percent = SelectField('Процент предоплаты', choices=get_prepayment_choices, validators=[DataRequired()])
    deadline = DateField('Срок выполнения', 
        validators=[DataRequired()])
    
    # Дополнительные условия
    revisions_count = SelectField('Количество правок', choices=get_revisions_choices, validators=[DataRequired()])
    intellectual_rights = SelectField('Права на результаты работ', choices=get_rights_choices, validators=[DataRequired()])
    portfolio_rights = SelectField('Использование в портфолио', choices=get_portfolio_choices, validators=[DataRequired()])
    client_delay_days = SelectField('Допустимая задержка', choices=get_delay_choices)

    # Удаляем остальные поля задержек и штрафов
    # contractor_delay_penalty и contractor_max_penalty больше не нужны 