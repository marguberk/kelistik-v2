import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm, mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from num2words import num2words

# Регистрируем системный шрифт с поддержкой кириллицы
FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
pdfmetrics.registerFont(TTFont('Arial', FONT_PATH))

# Добавим словарь с переводами текста договора
CONTRACT_TRANSLATIONS = {
    'ru': {
        'title': 'ДОГОВОР ОКАЗАНИЯ УСЛУГ',
        'city': 'г. Алматы',
        'client_intro': 'именуемый в дальнейшем «Заказчик»',
        'contractor_intro': 'именуемый в дальнейшем «Исполнитель»',
        'agreement_intro': 'заключили настоящий договор о нижеследующем:',
        'terms_title': 'ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ',
        'terms_intro': 'В настоящем Договоре используются следующие термины:',
        'terms': {
            'services': ('Услуги', 'работы по созданию дизайна, выполняемые Исполнителем по заданию Заказчика.'),
            'result': ('Результат работ', 'созданные Исполнителем дизайн-макеты, изображения, файлы и иные материалы.'),
            'revisions': ('Правки', 'изменения, вносимые в Результат работ по запросу Заказчика в рамках согласованного количества итераций.'),
            'stage': ('Этап работ', 'часть работ, после выполнения которой требуется согласование с Заказчиком.'),
            'delay': ('Задержка', 'нарушение сроков выполнения обязательств любой из сторон.'),
            'workday': ('Рабочий день', 'календарный день с понедельника по пятницу с 9:00 до 18:00, за исключением праздничных дней.')
        },
        'sections': {
            'subject': '1. ПРЕДМЕТ ДОГОВОРА',
            'payment': '2. СТОИМОСТЬ УСЛУГ И ПОРЯДОК РАСЧЕТОВ',
            'rights': '3. ПРАВА И ОБЯЗАННОСТИ СТОРОН',
            'delays': 'ЗАДЕРЖКИ',
            'acceptance': '4. ПОРЯДОК СДАЧИ-ПРИЕМКИ РАБОТ',
            'responsibility': '5. ОТВЕТСТВЕННОСТЬ СТОРОН',
            'force_majeure': '6. ФОРС-МАЖОР',
            'confidentiality': '7. КОНФИДЕНЦИАЛЬНОСТЬ',
            'disputes': '8. РАЗРЕШЕНИЕ СПОРОВ',
            'duration': '9. СРОК ДЕЙСТВИЯ ДОГОВОРА',
            'ip_rights': '10. ПРАВА НА РЕЗУЛЬТАТЫ РАБОТ',
            'details': '11. РЕКВИЗИТЫ И ПОДПИСИ СТОРОН'
        },
        'contract_text': {
            'subject_1': '1.1. Исполнитель обязуется оказать услуги {service_type}: {description}',
            'subject_2': '1.2. Срок выполнения работ: до {deadline}',
            'subject_3': '1.3. Количество возможных правок: {revisions}',
            
            'payment_1': '2.1. Стоимость услуг составляет {price} ({price_in_words}).',
            'payment_2': '2.2. Оплата производится в следующем порядке:',
            'payment_3': '     - {percent}% предоплата ({amount} ({amount_in_words}))',
            
            'rights_contractor': '3.1. Исполнитель обязуется:',
            'rights_contractor_1': '     - Выполнить работы качественно и в срок;',
            'rights_contractor_2': '     - Внести правки в соответствии с согласованным количеством итераций;',
            'rights_contractor_3': '     - Сохранять конфиденциальность информации, полученной от Заказчика.',
            'rights_client': '3.2. Заказчик обязуется:',
            'rights_client_1': '     - Предоставить необходимые материалы и информацию для выполнения работ;',
            'rights_client_2': '     - Оплатить работы в соответствии с условиями договора;',
            'rights_client_3': '     - Принять работы при их соответствии требованиям.',
            
            'delays_1': '1.1. Допустимая задержка для обеих сторон составляет {days} рабочих дней.',
            'delays_2': '1.2. В случае превышения допустимой задержки:',
            'delays_3': '- Сторона, допустившая задержку, обязана уведомить другую сторону;',
            'delays_4': '- Стороны согласовывают новые сроки выполнения обязательств;',
            'delays_5': '- При отсутствии согласования новых сроков, другая сторона вправе расторгнуть договор.',
            
            'acceptance_1': '4.1. По завершении работ Исполнитель направляет результаты Заказчику.',
            'acceptance_2': '4.2. Заказчик в течение 3 рабочих дней принимает работы или направляет мотивированный отказ.',
            'acceptance_3': '4.3. В случае мотивированного отказа стороны составляют двусторонний акт с перечнем необходимых доработок.',
            
            'responsibility_1': '5.1. Стороны освобождаются от ответственности за частичное или полное неисполнение обязательств по договору, если это неисполнение явилось следствием обстоятельств непреодолимой силы.',
            
            'force_majeure_1': '6.1. Стороны освобождаются от ответственности за неисполнение обязательств при возникновении форс-мажорных обстоятельств (войны, стихийные бедствия, изменения в законодательстве).',
            'force_majeure_2': '6.2. Сторона, для которой создалась невозможность исполнения обязательств, обязана уведомить другую сторону в письменной форме в течение 5 дней.',
            
            'confidentiality_1': '7.1. Стороны обязуются сохранять конфиденциальность информации, полученной в ходе исполнения договора.',
            'confidentiality_2': '7.2. Передача конфиденциальной информации третьим лицам возможна только с письменного согласия другой стороны.',
            
            'disputes_1': '8.1. Все споры решаются путем переговоров между сторонами.',
            'disputes_2': '8.2. В случае невозможности разрешения споров путем переговоров, они подлежат рассмотрению в судебном порядке согласно законодательству РК.',
            
            'duration_1': '9.1. Договор вступает в силу с момента подписания и действует до полного исполнения сторонами своих обязательств.',
            'duration_2': '9.2. Договор может быть расторгнут по соглашению сторон либо по основаниям, предусмотренным законодательством РК.',
            
            'details_contractor': 'ИСПОЛНИТЕЛЬ:',
            'details_client': 'ЗАКАЗЧИК:',
            'details_signature': '________________ (подпись)',
            'details_iin': 'ИИН:',
            'details_address': 'Адрес:',
            'details_phone': 'Телефон:',
            'details_bank': 'Банк:',
            'details_iban': 'IBAN:',
        },
        'service_type_web': 'веб-дизайна',
        'service_type_ui': 'UI/UX дизайна',
        'service_type_graphic': 'графического дизайна',
        'revisions_2': '2 правки',
        'revisions_3': '3 правки',
        'revisions_5': '5 правок',
        'revisions_unlimited': 'без ограничений',
        'from_one_side': 'с одной стороны',
        'from_other_side': 'с другой стороны',
    },
    'kk': {
        'title': 'ҚЫЗМЕТ КӨРСЕТУ ШАРТЫ',
        'city': 'Алматы қ.',
        'client_intro': 'бұдан әрі «Тапсырыс беруші» деп аталатын',
        'contractor_intro': 'бұдан әрі «Орындаушы» деп аталатын',
        'agreement_intro': 'төмендегілер туралы осы шартты жасасты:',
        'terms_title': 'ТЕРМИНДЕР ЖӘНЕ АНЫҚТАМАЛАР',
        'terms_intro': 'Осы Шартта келесі терминдер қолданылады:',
        'terms': {
            'services': ('Қызметтер', 'Тапсырыс берушінің тапсырмасы бойынша Орындаушы жасайтын дизайн жұмыстары.'),
            'result': ('Жұмыс нәтижесі', 'Орындаушы жасаған дизайн-макеттер, суреттер, файлдар және басқа материалдар.'),
            'revisions': ('Түзетулер', 'Келісілген итерациялар саны шеңберінде Тапсырыс берушінің сұрауы бойынша Жұмыс нәтижесіне енгізілетін өзгерістер.'),
            'stage': ('Жұмыс кезеңі', 'орындалғаннан кейін Тапсырыс берушімен келісуді қажет ететін жұмыстың бір бөлігі.'),
            'delay': ('Кешігу', 'тараптардың кез келгенінің міндеттемелерді орындау мерзімдерін бұзуы.'),
            'workday': ('Жұмыс күні', 'мереке күндерін қоспағанда, дүйсенбіден жұмаға дейін сағат 9:00-ден 18:00-ге дейінгі күнтізбелік күн.')
        },
        'sections': {
            'subject': '1. ШАРТТЫҢ МӘНІ',
            'payment': '2. ҚЫЗМЕТТЕРДІҢ ҚҰНЫ ЖӘНЕ ЕСЕП АЙЫРЫСУ ТӘРТІБІ',
            'rights': '3. ТАРАПТАРДЫҢ ҚҰҚЫҚТАРЫ МЕН МІNДЕТТЕРІ',
            'delays': 'КЕШІГУЛЕР',
            'acceptance': '4. ЖҰМЫСТЫ ТАПСЫРУ-ҚАБЫЛДАУ ТӘРТІБІ',
            'responsibility': '5. ТАРАПТАРДЫҢ ЖАУАПКЕРШІЛІГІ',
            'force_majeure': '6. ФОРС-МАЖОР',
            'confidentiality': '7. ҚҰПИЯЛЫЛЫҚ',
            'disputes': '8. ДАУЛАРДЫ ШЕШУ',
            'duration': '9. ШАРТТЫҢ ҚОЛДАНЫЛУ МЕРЗІМІ',
            'ip_rights': '10. ЖҰМЫС НӘТИЖЕЛЕРІНЕ ҚҰҚЫҚТАР',
            'details': '11. ТАРАПТАРДЫҢ ДЕРЕКТЕМЕЛЕРІ ЖӘНЕ ҚОЛДАРЫ'
        },
        'contract_text': {
            'subject_1': '1.1. Орындаушы {service_type} қызметтерін көрсетуге міндеттенеді: {description}',
            'subject_2': '1.2. Жұмысты орындау мерзімі: {deadline} дейін',
            'subject_3': '1.3. Мүмкін түзетулер саны: {revisions}',
            
            'payment_1': '2.1. Қызметтердің құны {price} ({price_in_words}) құрайды.',
            'payment_2': '2.2. Төлем келесі тәртіппен жүргізіледі:',
            'payment_3': '     - {percent}% алдын ала төлем ({amount} ({amount_in_words}))',
            
            'rights_contractor': '3.1. Орындаушы міндеттенеді:',
            'rights_contractor_1': '     - Жұмысты сапалы және уақытылы орындау;',
            'rights_contractor_2': '     - Келісілген итерациялар санына сәйкес түзетулер енгізу;',
            'rights_contractor_3': '     - Тапсырыс берушіден алынған ақпараттың құпиялылығын сақтау.',
            'rights_client': '3.2. Тапсырыс беруші міндеттенеді:',
            'rights_client_1': '     - Жұмысты орындау үшін қажетті материалдар мен ақпаратты ұсыну;',
            'rights_client_2': '     - Шарт талаптарына сәйкес жұмыс үшін төлем жасау;',
            'rights_client_3': '     - Талаптарға сәйкес келген жағдайда жұмысты қабылдау.',
            
            'delays_1': '1.1. Екі тарап үшін де рұқсат етілген кешігу {days} жұмыс күнін құрайды.',
            'delays_2': '1.2. Рұқсат етілген кешігуден асып кеткен жағдайда:',
            'delays_3': '- Кешігуге жол берген тарап екінші тарапқа хабарлауға міндетті;',
            'delays_4': '- Тараптар міндеттемелерді орындаудың жаңа мерзімдерін келіседі;',
            'delays_5': '- Жаңа мерзімдер келісілмеген жағдайда, екінші тарап шартты бұзуға құқылы.',
            
            'acceptance_1': '4.1. Жұмыс аяқталғаннан кейін Орындаушы нәтижелерді Тапсырыс берушіге жібереді.',
            'acceptance_2': '4.2. Тапсырыс беруші 3 жұмыс күні ішінде жұмысты қабылдайды немесе дәлелді бас тартуды жібереді.',
            'acceptance_3': '4.3. Дәлелді бас тарту жағдайында тараптар қажетті пысықтаулар тізімі бар екіжақты акт жасайды.',
            
            'responsibility_1': '5.1. Тараптар шарт бойынша міндеттемелерді ішінара немесе толық орындамағаны үшін жауапкершіліктен босатылады, егер бұл орындамау еңсерілмейтін күш жағдайларының салдары болса.',
            
            'force_majeure_1': '6.1. Тараптар форс-мажорлық жағдайлар (соғыс, табиғи апаттар, заңнамадағы өзгерістер) туындаған кезде міндеттемелерді орындамағаны үшін жауапкершіліктен босатылады.',
            'force_majeure_2': '6.2. Міндеттемелерді орындау мүмкін болмаған тарап екінші тарапқа 5 күн ішінде жазбаша түрде хабарлауға міндетті.',
            
            'confidentiality_1': '7.1. Тараптар шартты орындау барысында алынған ақпараттың құпиялылығын сақтауға міндеттенеді.',
            'confidentiality_2': '7.2. Құпия ақпаратты үшінші тұлғаларға беру екінші тараптың жазбаша келісімімен ғана мүмкін.',
            
            'disputes_1': '8.1. Барлық даулар тараптар арасындағы келіссөздер арқылы шешіледі.',
            'disputes_2': '8.2. Дауларды келіссөздер арқылы шешу мүмкін болмаған жағдайда, олар ҚР заңнамасына сәйкес сот тәртібімен қаралуға жатады.',
            
            'duration_1': '9.1. Шарт қол қойылған сәттен бастап күшіне енеді және тараптар өз міндеттемелерін толық орындағанға дейін қолданылады.',
            'duration_2': '9.2. Шарт тараптардың келісімі бойынша немесе ҚР заңнамасында көзделген негіздер бойынша бұзылуы мүмкін.',
            
            'details_contractor': 'ОРЫНДАУШЫ:',
            'details_client': 'ТАПСЫРЫС БЕРУШІ:',
            'details_signature': '________________ (қолы)',
            'details_iin': 'ЖСН:',
            'details_address': 'Мекенжайы:',
            'details_phone': 'Телефон:',
            'details_bank': 'Банк:',
            'details_iban': 'IBAN:',
        },
        'service_type_web': 'веб-дизайн қызметтері',
        'service_type_ui': 'UI/UX дизайн қызметтері',
        'service_type_graphic': 'графикалық дизайн қызметтері',
        'revisions_2': '2 түзету',
        'revisions_3': '3 түзету',
        'revisions_5': '5 түзету',
        'revisions_unlimited': 'шектеусіз',
        'from_one_side': 'бір жағынан',
        'from_other_side': 'екінші жағынан',
    }
}

def generate_contract(data, lang='ru'):
    """
    Генерирует договор в формате PDF на указанном языке
    """
    translations = CONTRACT_TRANSLATIONS[lang]
    
    filename = f'Договор_{datetime.now().strftime("%Y%m%d%H%M")}_{lang}'
    if lang == 'kk':
        filename = f'Келісімшарт_{datetime.now().strftime("%Y%m%d%H%M")}'
    
    pdf_path = f'static/contracts/{filename}.pdf'
    
    # Создаем PDF документ
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=3*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Добавляем язык в объект doc для использования в add_page_number
    doc.lang = lang
    
    # Регистрируем шрифты
    pdfmetrics.registerFont(TTFont('Arial', FONT_PATH))
    pdfmetrics.registerFont(TTFont('Arial-Bold', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
    
    # Создаем стили с указанием шрифта и поддержкой HTML
    styles = getSampleStyleSheet()
    
    # Добавляем стиль для заголовка
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontName='Arial-Bold',  # Используем жирный шрифт для заголовка
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=30,
        spaceBefore=30,
        leading=24,  # Межстрочный интервал
    ))
    
    # Обновляем стиль для основного текста с поддержкой HTML
    styles.add(ParagraphStyle(
        name='CustomText',
        parent=styles['Normal'],
        fontName='Arial',
        alignment=TA_JUSTIFY,
        fontSize=12,
        spaceAfter=12,
        leading=18,  # Межстрочный интервал
        firstLineIndent=20,  # Отступ первой строки
        allowWidows=0,  # Запрет висячих строк
        allowOrphans=0,
        wordWrap='CJK',  # Улучшенный перенос слов
        spaceBefore=6,  # Добавляем отступ перед параграфом
    ))

    # Добавляем стиль для жирного текста
    styles.add(ParagraphStyle(
        name='TermStyle',
        parent=styles['CustomText'],
        fontName='Arial-Bold',  # Используем жирный шрифт
        firstLineIndent=0,  # Убираем отступ первой строки для терминов
        spaceBefore=12,  # Увеличиваем отступ перед термином
    ))

    # Стиль для жирного текста
    styles.add(ParagraphStyle(
        name='CustomBold',
        parent=styles['CustomText'],
        fontName='Arial-Bold',  # Нужно зарегистрировать жирный шрифт
    ))

    # Регистрируем жирный и курсивный шрифты
    pdfmetrics.registerFont(TTFont('Arial-Italic', '/System/Library/Fonts/Supplemental/Arial Italic.ttf'))
    
    styles.add(ParagraphStyle(
        name='CustomHeading',
        parent=styles['Heading2'],
        fontName='Arial',
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        leading=20,
        textColor=colors.black,
        backColor=colors.white
    ))
    
    # Добавляем стиль для даты
    styles.add(ParagraphStyle(
        name='DateStyle',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER
    ))
    
    # Формируем содержимое
    story = []
    
    # Заголовок
    story.append(Paragraph(
        f'{translations["title"]} № {datetime.now().strftime("%Y%m%d%H%M")}',
        styles['CustomTitle']
    ))
    
    # Создаем таблицу для даты и города
    date_data = [[
        Paragraph(translations['city'], styles['CustomText']),
        Paragraph(datetime.now().strftime("%d.%m.%Y"), styles['CustomText'])
    ]]
    
    date_table = Table(date_data, colWidths=[doc.width/2, doc.width/2])
    date_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(date_table)
    story.append(Spacer(1, 12))
    
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
            service_type=get_service_type_name(data["service_type"], lang),
            description=data["service_description"]
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
            revisions=get_revisions_text(data["revisions_count"], lang)
        ),
        styles['CustomText']
    ))
    
    story.append(Paragraph(translations['sections']['payment'], styles['CustomHeading']))
    story.append(Paragraph(
        translations['contract_text']['payment_1'].format(
            price=data["price"],
            price_in_words=number_to_words_ru(data["price"], lang)
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

    # Создаем PDF с передачей языка через doc
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    
    return pdf_path

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

def add_page_number(canvas, doc):
    """
    Добавляет номер страницы
    """
    canvas.saveState()
    canvas.setFont('Arial', 9)
    # Используем doc.lang для определения языка
    page_text = "Бет" if doc.lang == 'kk' else "Страница"
    canvas.drawRightString(
        doc.pagesize[0] - doc.rightMargin,
        doc.bottomMargin/2,
        f"{page_text} {doc.page}"
    )
    canvas.restoreState()

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