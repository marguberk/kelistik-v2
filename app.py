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

@app.before_request
def before_request():
    g.lang = request.args.get('lang', 'ru')
    g.translations = translations[g.lang]

@app.route('/')
def index():
    return render_template('index.html', t=g.translations, lang=g.lang)

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

            pdf_path = generate_contract(data, g.lang)
            return render_template('download.html', 
                                pdf_path=pdf_path,
                                t=g.translations, 
                                lang=g.lang)
            
        except Exception as e:
            flash(g.translations['error_generating_contract'], 'error')
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
        file_path = os.path.join('static/contracts', path.split('/')[-1])
        
        # Если запрос для скачивания
        if request.args.get('download'):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        
        # Если запрос для просмотра
        response = send_file(
            file_path,
            mimetype='application/pdf'
        )
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        flash(g.translations['error_downloading'], 'error')
        return redirect(url_for('index'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Функция для очистки старых файлов (можно вызывать периодически)
def cleanup_old_files():
    try:
        current_time = datetime.now()
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            if (current_time - file_modified).days > 1:  # Удаляем файлы старше 1 дня
                os.remove(file_path)
    except Exception as e:
        print(f"Error cleaning up files: {str(e)}")

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