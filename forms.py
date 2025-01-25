from flask import g
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError, Email, Regexp
from validators import validate_iin_bin, validate_phone, validate_iban

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
    
    def validate_contractor_phone(form, field):
        is_valid, message = validate_phone(field.data)
        if not is_valid:
            raise ValidationError(message)
    
    contractor_phone = StringField(
        validators=[
            DataRequired(),
            Regexp(r'^\+7\d{10}$', message=lambda: g.translations['validation_phone'])
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
    
    def validate_client_phone(form, field):
        is_valid, message = validate_phone(field.data)
        if not is_valid:
            raise ValidationError(message)
    
    client_phone = StringField(
        validators=[
            DataRequired(),
            Regexp(r'^\+7\d{10}$', message=lambda: g.translations['validation_phone'])
        ])
    
    client_address = StringField('Адрес Заказчика',
        validators=[DataRequired(), Length(min=10, max=200)])
    
    # Данные услуги
    def get_service_choices():
        return [
            ('web_design', g.translations['service_type_web']),
            ('ui_ux', g.translations['service_type_ui']),
            ('graphic_design', g.translations['service_type_graphic'])
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