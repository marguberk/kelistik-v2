from flask import g
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError, Email, Regexp, NumberRange
from validators import validate_iin_bin, validate_phone, validate_iban
from datetime import date, datetime

class PhoneNumberValidator:
    def __call__(self, form, field):
        number = ''.join(c for c in field.data if c.isdigit() or c == '+')
        
        if not number.startswith('+7'):
            raise ValidationError(g.translations['validation_phone_start'])
            
        if len(number) != 12:
            raise ValidationError(g.translations['validation_phone_length'])
        
        if not number[2:].isdigit():
            raise ValidationError(g.translations['validation_phone_digits'])

    def validate_deadline(self, field):
        if field.data < datetime.now().date():
            raise ValidationError(g.translations['validation_date'])
        return True

class ContractForm(FlaskForm):
    # Данные исполнителя
    contractor_name = StringField(
        validators=[
            DataRequired(),
            Length(min=2, max=100)
        ])
    
    contractor_iin = StringField(
        validators=[
            DataRequired(message=''),
            Length(min=12, max=12, message=''),
            Regexp(r'^\d{12}$', message='')
        ])
    
    def validate_contractor_iin(form, field):
        is_valid, _ = validate_iin_bin(field.data)
        if not is_valid or len(field.data) != 12:
            if g.lang == 'ru':
                raise ValidationError('ИИН должен содержать 12 цифр')
            else:
                raise ValidationError('ЖСН 12 саннан тұруы керек')
    
    contractor_phone = StringField('Телефон Исполнителя', 
        render_kw={"type": "tel"},
        validators=[
            DataRequired(),
            PhoneNumberValidator()
        ])
    
    contractor_address = StringField(
        validators=[
            DataRequired(),
            Length(min=10, max=200)
        ])
    
    contractor_bank = StringField(
        validators=[
            DataRequired()
        ])
    
    contractor_iban = StringField(
        validators=[
            DataRequired(message=''),
            Length(min=20, max=20, message=''),
            Regexp(r'^[A-Z]{2}\d{18}$', message='')
        ])
    
    def validate_contractor_iban(form, field):
        is_valid, _ = validate_iban(field.data)
        if not is_valid or not field.data.startswith('KZ') or len(field.data) != 20:
            if g.lang == 'ru':
                raise ValidationError('Формат: KZXXXXXXXXXXXXXXXXXX')
            else:
                raise ValidationError('IBAN форматы: KZXXXXXXXXXXXXXXXXXX')
    
    # Данные заказчика
    client_name = StringField(
        validators=[
            DataRequired(),
            Length(min=2, max=100)
        ])
    
    def validate_client_iin(form, field):
        is_valid, message = validate_iin_bin(field.data)
        if not is_valid:
            raise ValidationError(message)
    
    client_iin = StringField(
        validators=[
            DataRequired(),
            Length(min=12, max=12),
            Regexp(r'^\d{12}$')
        ])
    
    client_phone = StringField('Телефон Заказчика', 
        render_kw={"type": "tel"},
        validators=[
            DataRequired(),
            PhoneNumberValidator()
        ])
    
    client_address = StringField(
        validators=[
            DataRequired(),
            Length(min=10, max=200)
        ])
    
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
        validators=[
            DataRequired(),
            Length(min=10, max=1000)
        ],
        render_kw={
            "rows": "6",
            "class": "whitespace-pre-wrap"
        }
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(g, 'translations'):
            # Плейсхолдер для описания услуг
            self.service_description.render_kw["placeholder"] = g.translations['service_description_placeholder']
            
            # Дата - формат в зависимости от языка
            date_format = "дд.мм.гггг" if g.lang == 'ru' else "кк.аа.жжжж"
            self.deadline.render_kw = {
                "type": "date",
                "placeholder": date_format
            }
            
            # Устанавливаем сообщения валидации только для полей, которые не имеют custom validators
            for field in self._fields.values():
                for validator in field.validators:
                    if isinstance(validator, DataRequired):
                        validator.message = g.translations['validation_required']
                    elif isinstance(validator, Length):
                        if field.name == 'contractor_name' or field.name == 'client_name':
                            validator.message = g.translations['validation_name_length']
                        elif field.name == 'service_description':
                            validator.message = g.translations['validation_description_length']
    
    # Условия договора
    price = DecimalField(
        validators=[
            DataRequired(),
            NumberRange(min=0)
        ])
    prepayment_percent = SelectField('Процент предоплаты', choices=get_prepayment_choices, validators=[DataRequired()])
    deadline = DateField(
        validators=[
            DataRequired(),
        ])
    
    def validate_deadline(self, field):
        if field.data < datetime.now().date():
            raise ValidationError(g.translations['validation_date'])
        return True
    
    # Дополнительные условия
    revisions_count = SelectField('Количество правок', choices=get_revisions_choices, validators=[DataRequired()])
    intellectual_rights = SelectField('Права на результаты работ', choices=get_rights_choices, validators=[DataRequired()])
    portfolio_rights = SelectField('Использование в портфолио', choices=get_portfolio_choices, validators=[DataRequired()])
    client_delay_days = SelectField('Допустимая задержка', choices=get_delay_choices)

    # Удаляем остальные поля задержек и штрафов
    # contractor_delay_penalty и contractor_max_penalty больше не нужны 

    # ... остальные методы ... 