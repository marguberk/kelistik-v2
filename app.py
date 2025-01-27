from flask import Flask, render_template, request, send_file, send_from_directory, flash, redirect, url_for, g
from flask_wtf import FlaskForm
from contract_generator import generate_contract, generate_bilingual_contract
from forms import ContractForm
import os
from datetime import datetime, timedelta
import mimetypes
from translations import CONTRACT_TRANSLATIONS as translations
import logging
from flask_cors import CORS
from functools import lru_cache
from werkzeug.middleware.shared_data import SharedDataMiddleware
import threading
from queue import Queue

# Настраиваем логирование
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Отключаем сообщения о разработческом сервере Flask, кроме INFO о запуске
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

# Создаем свой логгер для вывода адреса сервера
server_logger = logging.getLogger('server')
server_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('* Running on %(message)s'))
server_logger.addHandler(handler)

app = Flask(__name__)
CORS(app)  # Добавляем поддержку CORS
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/contracts')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['WTF_CSRF_TIME_LIMIT'] = 1800  # 30 минут

# Создаем папку для контрактов, если её нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Отключаем логи о загрузке шрифтов
logging.getLogger('weasyprint').setLevel(logging.ERROR)

# Добавляем поддержку статических файлов
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/static': os.path.join(os.path.dirname(__file__), 'static')
})

# Очередь для асинхронной генерации PDF
pdf_queue = Queue()

@app.before_request
def before_request():
    g.lang = request.args.get('lang', 'ru')
    # Создаем объект с методом gettext и get
    class Translations:
        def __init__(self, translations_dict):
            self.translations = translations_dict
        
        def gettext(self, text):
            return self.translations.get(text, text)
        
        def get(self, text):  # Добавляем метод get
            return self.translations.get(text, text)
        
        def __getitem__(self, key):
            return self.translations.get(key, key)
    
    g.translations = Translations(translations[g.lang])

@app.route('/')
def index():
    return render_template('index.html', t=g.translations, lang=g.lang)

# Кэшируем создание PDF
@lru_cache(maxsize=32)
def generate_cached_contract(data_tuple, lang):
    return generate_contract(dict(data_tuple), lang)

def process_pdf_generation(data, lang, result_queue):
    try:
        pdf_path = generate_contract(data, lang)
        result_queue.put(('success', pdf_path))
    except Exception as e:
        result_queue.put(('error', str(e)))

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    form = ContractForm()
    
    if form.validate_on_submit():
        try:
            data = {
                'contractor_name': form.contractor_name.data,
                'contractor_iin': form.contractor_iin.data,
                'contractor_phone': form.contractor_phone.data,
                'contractor_address': form.contractor_address.data,
                'contractor_bank': form.contractor_bank.data,
                'contractor_iban': form.contractor_iban.data,
                
                'client_name': form.client_name.data,
                'client_iin': form.client_iin.data,
                'client_phone': form.client_phone.data,
                'client_address': form.client_address.data,
                
                'service_type': form.service_type.data,
                'service_description': form.service_description.data,
                'price': form.price.data,
                'prepayment_percent': form.prepayment_percent.data,
                'deadline': form.deadline.data,
                'revisions_count': form.revisions_count.data,
                
                'intellectual_rights': form.intellectual_rights.data,
                'portfolio_rights': form.portfolio_rights.data,
                'client_delay_days': form.client_delay_days.data
            }

            # Создаем очередь для результата
            result_queue = Queue()
            
            # Запускаем генерацию PDF в отдельном потоке
            thread = threading.Thread(
                target=process_pdf_generation,
                args=(data, g.lang, result_queue)
            )
            thread.start()
            
            # Ждем результат не более 10 секунд
            thread.join(timeout=10)
            
            if thread.is_alive():
                # Если генерация занимает слишком много времени
                flash(g.translations.gettext('generation_taking_long'), 'info')
                return render_template('generating.html', t=g.translations, lang=g.lang)
            
            status, result = result_queue.get()
            if status == 'error':
                raise Exception(result)
                
            return render_template('download.html', 
                                pdf_path=result,
                                t=g.translations, 
                                lang=g.lang)
            
        except Exception as e:
            flash(g.translations.gettext('error_generating_contract'), 'error')
            return render_template('form.html', form=form, t=g.translations, lang=g.lang)
    
    if form.errors:
        first_error = next(iter(form.errors.values()))[0]
        flash(first_error, 'error')
    
    return render_template('form.html', form=form, t=g.translations, lang=g.lang)

@app.route('/download/<path:path>')
def download_file(path):
    try:
        # Получаем язык из URL параметра
        current_lang = request.args.get('lang', 'ru')
        
        # Название файла зависит от языка в URL
        filename = 'Келісімшарт.pdf' if current_lang == 'kk' else 'Договор.pdf'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], path.split('/')[-1])
        
        # Если запрос для скачивания
        if request.args.get('download'):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        
        # Если запрос для просмотра
        return send_file(
            file_path,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(g.translations.gettext('error_downloading'), 'error')
        return redirect(url_for('index'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', t=g.translations, lang=g.lang), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', t=g.translations, lang=g.lang), 500

if __name__ == '__main__':
    app.config['DEBUG'] = True  # Включаем отладку
    server_logger.info('http://127.0.0.1:5000')
    app.run(debug=True) 