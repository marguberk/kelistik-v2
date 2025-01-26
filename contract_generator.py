import os
import requests
from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import cm, mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
from num2words import num2words
# Добавляем импорт переводов
from translations import CONTRACT_TRANSLATIONS
from reportlab.pdfbase.ttfonts import TTFont
import logging
import sys

# Настраиваем логирование
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('contract_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# URL для скачивания шрифтов Roboto
FONT_URLS = {
    'regular': 'https://raw.githubusercontent.com/googlefonts/roboto-2/main/src/hinted/Roboto-Regular.ttf',
    'bold': 'https://raw.githubusercontent.com/googlefonts/roboto-2/main/src/hinted/Roboto-Bold.ttf',
    'italic': 'https://raw.githubusercontent.com/googlefonts/roboto-2/main/src/hinted/Roboto-Italic.ttf',
    'bolditalic': 'https://raw.githubusercontent.com/googlefonts/roboto-2/main/src/hinted/Roboto-BoldItalic.ttf'
}

# Регистрация шрифтов
pdfmetrics.registerFont(TTFont('Roboto', BytesIO(requests.get(FONT_URLS['regular']).content)))
pdfmetrics.registerFont(TTFont('Roboto-Bold', BytesIO(requests.get(FONT_URLS['bold']).content)))
pdfmetrics.registerFont(TTFont('Roboto-Italic', BytesIO(requests.get(FONT_URLS['italic']).content)))
pdfmetrics.registerFont(TTFont('Roboto-BoldItalic', BytesIO(requests.get(FONT_URLS['bolditalic']).content)))

def download_and_register_fonts():
    """Скачивает и регистрирует шрифты Roboto"""
    logger.info("Начало загрузки и регистрации шрифтов")
    
    for style, url in FONT_URLS.items():
        logger.info(f"Обработка шрифта {style}")
        try:
            logger.info(f"Загрузка шрифта {style} с URL: {url}")
            response = requests.get(url)
            response.raise_for_status()
            font_data = BytesIO(response.content)
            logger.info(f"Шрифт {style} успешно загружен")
            
            # Регистрируем шрифт
            font_name = f'Roboto-{style}'
            pdfmetrics.registerFont(TTFont(font_name, font_data))
            logger.info(f"Шрифт {font_name} успешно зарегистрирован")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке шрифта {style}: {str(e)}")
            continue

# Скачиваем и регистрируем шрифты при запуске
download_and_register_fonts()

# Обновляем стили для использования Roboto
def create_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontName='Roboto-bold',
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=30,
        spaceBefore=30,
        leading=24,
    ))

    styles.add(ParagraphStyle(
        name='CustomText',
        parent=styles['Normal'],
        fontName='Roboto-regular',
        alignment=TA_JUSTIFY,
        fontSize=12,
        spaceBefore=6,
        spaceAfter=6,
        leading=14,
    ))

    styles.add(ParagraphStyle(
        name='TermStyle',
        parent=styles['CustomText'],
        fontName='Roboto-bold',
        firstLineIndent=0,
        spaceBefore=12,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name='CustomBold',
        parent=styles['CustomText'],
        fontName='Roboto-bold',
    ))

    styles.add(ParagraphStyle(
        name='CustomHeading',
        parent=styles['Heading2'],
        fontName='Roboto-bold',
        fontSize=14,
        spaceAfter=12,
        spaceBefore=12,
        leading=16,
    ))

    styles.add(ParagraphStyle(
        name='DateStyle',
        parent=styles['Normal'],
        fontName='Roboto-regular',
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER,
    ))

    return styles

# В функции add_page_number меняем шрифт
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Roboto-regular', 9)
    # Используем правильный текст в зависимости от языка
    page_text = "Бет" if hasattr(doc, 'lang') and doc.lang == 'kk' else "Страница"
    canvas.drawRightString(
        doc.pagesize[0] - doc.rightMargin,
        doc.bottomMargin/2,
        f"{page_text} {doc.page}"
    )
    canvas.restoreState()

def generate_contract(data, lang):
    try:
        # Получаем переводы для выбранного языка
        translations = CONTRACT_TRANSLATIONS[lang]
        
        # Форматируем данные
        service_type = get_service_type_name(data["service_type"], lang)
        current_date = datetime.now().strftime("%d.%m.%Y")
        contract_number = datetime.now().strftime("%Y%m%d%H%M%S")
        revisions_count = data.get('revisions_count', '3')
        price_text = number_to_words_ru(float(data["price"]), lang)
        
        # Создаем PDF
        filename = f'contract_{contract_number}.pdf'
        filepath = os.path.join('static/contracts', filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        # Добавляем язык в объект doc
        doc.lang = lang
        
        # Создаем стили
        styles = create_styles()
        story = []
        
        # Заголовок
        if lang == 'ru':
            title = f'ДОГОВОР ОКАЗАНИЯ УСЛУГ № {contract_number}'
        else:
            title = f'ҚЫЗМЕТ КӨРСЕТУ ШАРТЫ № {contract_number}'
            
        story.append(Paragraph(
            title,
            styles['CustomTitle']
        ))
        
        # Дата по правому краю
        story.append(Paragraph(
            current_date,
            ParagraphStyle(
                'Date',
                parent=styles['Normal'],
                fontName='Roboto-regular',
                fontSize=12,
                alignment=TA_RIGHT,
                spaceBefore=12,
                spaceAfter=24
            )
        ))
        
        # Преамбула
        preamble = (
            f'{data["client_name"]}, {translations["client_intro"]}, '
            f'{translations["contract_text"]["details_iin"]} {data["client_iin"]}, '
            f'{translations["contract_text"]["details_address"]} {data["client_address"]}, '
            f'{translations["contract_text"]["details_phone"]} {data["client_phone"]}, '
            f'{translations["from_one_side"]}, '
            f'{data["contractor_name"]}, {translations["contractor_intro"]}, '
            f'{translations["contract_text"]["details_iin"]} {data["contractor_iin"]}, '
            f'{translations["contract_text"]["details_address"]} {data["contractor_address"]}, '
            f'{translations["contract_text"]["details_phone"]} {data["contractor_phone"]}, '
            f'{translations["from_other_side"]}, '
            f'{translations["agreement_intro"]}'
        )
        story.append(Paragraph(preamble, styles['CustomText']))
        
        # Добавляем определения терминов с правильным форматированием
        story.append(Paragraph(translations['terms_title'], styles['CustomHeading']))
        story.append(Paragraph(translations['terms_intro'], styles['CustomText']))
        
        terms = [
            translations['terms']['services'],
            translations['terms']['result'],
            translations['terms']['revisions'],
            translations['terms']['stage'],
            translations['terms']['delay'],
            translations['terms']['workday']
        ]

        for term, definition in terms:
            story.append(Paragraph(
                f'<b>{term}</b> – {definition}',  # Только термин жирным
                styles['CustomText']  # Используем обычный стиль
            ))
            story.append(Spacer(1, 6))
        
        # Разделы договора с форматированием
        story.append(Paragraph(translations['sections']['subject'], styles['CustomHeading']))
        story.append(Paragraph(
            translations['contract_text']['subject_1'].format(
                service_type=service_type,
                description=data["service_description"],
                revisions=revisions_count
            ),
            styles['CustomText']
        ))
        story.append(Paragraph(
            translations['contract_text']['subject_2'].format(
                deadline=data["deadline"].strftime("%d.%m.%Y")
            ),
            styles['CustomText']
        ))
        story.append(Paragraph(
            translations['contract_text']['subject_3'].format(
                revisions=revisions_count
            ),
            styles['CustomText']
        ))
        
        story.append(Paragraph(translations['sections']['payment'], styles['CustomHeading']))
        story.append(Paragraph(
            translations['contract_text']['payment_1'].format(
                price=data["price"],
                price_in_words=price_text
            ),
            styles['CustomText']
        ))
        story.append(Paragraph(translations['contract_text']['payment_2'], styles['CustomText']))
        
        prepayment_amount = float(data["price"]) * float(data["prepayment_percent"].strip("%")) / 100
        story.append(Paragraph(
            translations['contract_text']['payment_3'].format(
                percent=data["prepayment_percent"].strip("%"),
                amount=prepayment_amount,
                amount_in_words=number_to_words_ru(prepayment_amount, lang)
            ),
            styles['CustomText']
        ))
        
        story.append(Paragraph(translations['sections']['rights'], styles['CustomHeading']))
        story.append(Paragraph(translations['contract_text']['rights_contractor'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['rights_contractor_1'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['rights_contractor_2'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['rights_contractor_3'], styles['CustomText']))
        
        story.append(Paragraph(translations['contract_text']['rights_client'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['rights_client_1'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['rights_client_2'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['rights_client_3'], styles['CustomText']))
        
        # Добавляем раздел про задержки
        story.append(Paragraph(translations['sections']['delays'], styles['CustomHeading']))
        story.append(Paragraph(
            translations['contract_text']['delays_1'].format(days=data["client_delay_days"]),
            styles['CustomText']
        ))
        story.append(Paragraph(translations['contract_text']['delays_2'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['delays_3'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['delays_4'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['delays_5'], styles['CustomText']))

        # Порядок сдачи-приемки работ
        story.append(Paragraph(translations['sections']['acceptance'], styles['CustomHeading']))
        story.append(Paragraph(translations['contract_text']['acceptance_1'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['acceptance_2'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['acceptance_3'], styles['CustomText']))
        
        # Ответственность сторон
        story.append(Paragraph(translations['sections']['responsibility'], styles['CustomHeading']))
        story.append(Paragraph(translations['contract_text']['responsibility_1'], styles['CustomText']))
        
        # Форс-мажор
        story.append(Paragraph(translations['sections']['force_majeure'], styles['CustomHeading']))
        story.append(Paragraph(translations['contract_text']['force_majeure_1'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['force_majeure_2'], styles['CustomText']))
        
        # Конфиденциальность
        story.append(Paragraph(translations['sections']['confidentiality'], styles['CustomHeading']))
        story.append(Paragraph(translations['contract_text']['confidentiality_1'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['confidentiality_2'], styles['CustomText']))
        
        # Разрешение споров
        story.append(Paragraph(translations['sections']['disputes'], styles['CustomHeading']))
        story.append(Paragraph(translations['contract_text']['disputes_1'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['disputes_2'], styles['CustomText']))
        
        # Срок действия договора
        story.append(Paragraph(translations['sections']['duration'], styles['CustomHeading']))
        story.append(Paragraph(translations['contract_text']['duration_1'], styles['CustomText']))
        story.append(Paragraph(translations['contract_text']['duration_2'], styles['CustomText']))
        
        story.append(Paragraph(translations['sections']['ip_rights'], styles['CustomHeading']))
        story.append(Paragraph(get_intellectual_rights_text(data["intellectual_rights"], data["portfolio_rights"], lang), styles['CustomText']))
        
        # Реквизиты и подписи
        story.append(Paragraph(translations['sections']['details'], styles['CustomHeading']))
        story.append(Spacer(1, 20))  # Увеличиваем отступ перед таблицей

        # Создаем таблицу для реквизитов
        contractor_data = [
            [Paragraph(translations['contract_text']['details_contractor'], styles['CustomText']), 
             Paragraph(translations['contract_text']['details_client'], styles['CustomText'])],
            [Paragraph(f'''<b>{data["contractor_name"]}</b><br/>
                          <b>{translations['contract_text']['details_iin']}</b> {data["contractor_iin"]}<br/>
                          <b>{translations['contract_text']['details_address']}</b> {data["contractor_address"]}<br/>
                          <b>{translations['contract_text']['details_phone']}</b> {data["contractor_phone"]}<br/>
                          <b>{translations['contract_text']['details_bank']}</b> {data["contractor_bank"]}<br/>
                          <b>{translations['contract_text']['details_iban']}</b> {data["contractor_iban"]}<br/><br/>
                          {translations['contract_text']['details_signature']}''', styles['CustomText']),
             Paragraph(f'''<b>{data["client_name"]}</b><br/>
                          <b>{translations['contract_text']['details_iin']}</b> {data["client_iin"]}<br/>
                          <b>{translations['contract_text']['details_address']}</b> {data["client_address"]}<br/>
                          <b>{translations['contract_text']['details_phone']}</b> {data["client_phone"]}<br/><br/><br/>
                          {translations['contract_text']['details_signature']}''', styles['CustomText'])]
        ]

        # Создаем таблицу с параметром keepTogether
        table = Table(contractor_data, colWidths=[doc.width/2-6*mm, doc.width/2-6*mm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ]))
        
        # Оборачиваем таблицу в KeepTogether
        from reportlab.platypus import KeepTogether
        story.append(KeepTogether(table))

        # Создаем PDF
        logger.info("Начало сборки PDF документа")
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        logger.info("PDF документ успешно создан")
        
        return filepath

    except Exception as e:
        logger.error(f"Contract generation error: {str(e)}", exc_info=True)
        raise

def get_service_type_name(service_type, lang='ru'):
    """Возвращает название типа услуги на нужном языке"""
    translations = CONTRACT_TRANSLATIONS[lang]
    service_types = {
        'web_design': translations['service_type_web'],
        'ui_ux': translations['service_type_ui'],
        'graphic_design': translations['service_type_graphic']
    }
    return service_types.get(service_type, service_type)

def get_revisions_text(revisions, lang='ru'):
    """Возвращает текст о количестве правок на нужном языке"""
    translations = CONTRACT_TRANSLATIONS[lang]
    revisions_text = {
        '2': translations['revisions_2'],
        '3': translations['revisions_3'],
        '5': translations['revisions_5'],
        'unlimited': translations['revisions_unlimited']
    }
    return revisions_text.get(revisions, revisions)

def get_intellectual_rights_text(rights_type, portfolio_rights, lang='ru'):
    """
    Возвращает текст о правах на результаты работ на нужном языке
    """
    if lang == 'kk':
        portfolio_text = "Орындаушы жұмыс нәтижелерін өзінің портфолиосында пайдалануға құқылы." if portfolio_rights == "yes" else "Орындаушы Тапсырыс берушінің жазбаша келісімінсіз жұмыс нәтижелерін өзінің портфолиосында пайдалануға құқығы жоқ."
        
        texts = {
            'full': f'Қызметтерді толық төлегеннен кейін Орындаушы Тапсырыс берушіге жұмыс нәтижелеріне айрықша құқықтарды толық көлемде береді. {portfolio_text}',
            'partial': f'Қызметтерді төлегеннен кейін Тапсырыс беруші жұмыс нәтижелерін келісілген мақсаттарда пайдалану құқығын алады. {portfolio_text}',
            'license': f'Тапсырыс беруші жұмыс нәтижелерін пайдалануға айрықша емес лицензия алады. {portfolio_text}'
        }
    else:
        portfolio_text = "Исполнитель имеет право использовать результаты работ в своем портфолио." if portfolio_rights == "yes" else "Исполнитель не имеет права использовать результаты работ в своем портфолио без письменного согласия Заказчика."
        
        texts = {
            'full': f'После полной оплаты услуг Исполнитель передает Заказчику исключительные права на результаты работ в полном объеме. {portfolio_text}',
            'partial': f'После оплаты услуг Заказчик получает права на использование результатов работ в оговоренных целях. {portfolio_text}',
            'license': f'Заказчик получает неисключительную лицензию на использование результатов работ. {portfolio_text}'
        }
    
    return texts.get(rights_type)

def number_to_words_ru(number, lang='ru'):
    """Преобразует число в текст на нужном языке"""
    try:
        whole = int(float(number))
        fraction = round((float(number) - whole) * 100)
        
        if lang == 'kk':
            whole_text = num2words(whole, lang='kz')
            result = f"{whole_text} теңге"
            if fraction > 0:
                fraction_text = num2words(fraction, lang='kz')
                result += f" {fraction_text} тиын"
        else:
            whole_text = num2words(whole, lang='ru')
            result = f"{whole_text} тенге"
            if fraction > 0:
                fraction_text = num2words(fraction, lang='ru')
                result += f" {fraction_text} тиын"
        
        return result.capitalize()
    except:
        return str(number)

def generate_bilingual_contract(data):
    """
    Генерирует две версии договора - на русском и казахском языках
    """
    ru_path = generate_contract(data, 'ru')
    kk_path = generate_contract(data, 'kk')
    return {'ru': ru_path, 'kk': kk_path} 