from flask import Flask, render_template, request, send_file, send_from_directory, flash, redirect, url_for, g
from forms import ContractForm
from contract_generator import generate_contract, generate_bilingual_contract
import os
from datetime import datetime
import mimetypes
from translations import translations

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Возвращаем случайный ключ
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/contracts')

# Создаем папку для контрактов, если её нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
            print("Начинаем генерацию договора...")
            data = {
                'contractor_name': form.contractor_name.data,
                'contractor_iin': form.contractor_iin.data,
                'contractor_address': form.contractor_address.data,
                'contractor_phone': form.contractor_phone.data,
                'contractor_bank': form.contractor_bank.data,
                'contractor_iban': form.contractor_iban.data,
                'client_name': form.client_name.data,
                'client_iin': form.client_iin.data,
                'client_address': form.client_address.data,
                'client_phone': form.client_phone.data,
                'service_type': form.service_type.data,
                'service_description': form.service_description.data,
                'price': form.price.data,
                'prepayment_percent': form.prepayment_percent.data,
                'deadline': form.deadline.data,
                'revisions_count': form.revisions_count.data,
                'intellectual_rights': form.intellectual_rights.data,
                'portfolio_rights': form.portfolio_rights.data,
                'client_delay_days': form.client_delay_days.data,
            }
            print(f"Данные формы собраны: {data}")
            
            # Генерируем договор только на выбранном языке
            pdf_path = generate_contract(data, g.lang)
            
            return render_template('download.html', 
                                 pdf_path=pdf_path,  # Теперь передаем один путь
                                 t=g.translations, 
                                 lang=g.lang)
            
        except Exception as e:
            print(f"Ошибка при генерации договора: \n{str(e)}")
            flash(g.translations['error_generating_contract'], 'error')
            return render_template('form.html', form=form, t=g.translations, lang=g.lang)
    
    return render_template('form.html', form=form, t=g.translations, lang=g.lang)

@app.route('/download/<path:path>')
def download_file(path):
    try:
        # Определяем тип файла
        mime_type = mimetypes.guess_type(path)[0]
        
        # Если запрос из iframe (предпросмотр), отправляем файл для отображения
        if request.headers.get('Sec-Fetch-Dest') == 'iframe':
            return send_from_directory('static/contracts', 
                                     path.split('/')[-1], 
                                     mimetype=mime_type)
        
        # Иначе отправляем файл для скачивания
        return send_from_directory('static/contracts', 
                                 path.split('/')[-1], 
                                 as_attachment=True,
                                 mimetype=mime_type)
    except Exception as e:
        flash('Файл не найден или произошла ошибка при скачивании.', 'error')
        return redirect(url_for('index'))

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

if __name__ == '__main__':
    app.run(debug=True) 