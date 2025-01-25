# Kelistik - Генератор договоров

Веб-приложение для генерации договоров на русском и казахском языках.

## Развертывание на PythonAnywhere

1. Создайте аккаунт на PythonAnywhere

2. Откройте bash консоль и клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/kelistik.git
cd kelistik
```

3. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Создайте файл .env:
```bash
cp .env.example .env
# Отредактируйте .env и установите свой SECRET_KEY
```

6. Настройте веб-приложение в PythonAnywhere:
- Перейдите в раздел Web
- Создайте новое веб-приложение
- Выберите Flask и Python 3.10
- Укажите путь к файлу WSGI:
  ```python
  import sys
  path = '/home/yourusername/kelistik'
  if path not in sys.path:
      sys.path.append(path)
  
  from app import app as application
  ```

7. Настройте статические файлы:
- URL: /static/
- Directory: /home/yourusername/kelistik/static/

8. Перезапустите веб-приложение

## Структура проекта

- `app.py` - основной файл приложения
- `contract_generator.py` - генератор PDF документов
- `forms.py` - формы Flask-WTF
- `translations.py` - переводы интерфейса
- `static/` - статические файлы
- `templates/` - HTML шаблоны
- `.env` - настройки окружения
- `requirements.txt` - зависимости проекта

## Шрифты

Проект использует шрифты Roboto, которые автоматически загружаются при первом запуске. Шрифты кэшируются локально в директории `.fonts/`. 