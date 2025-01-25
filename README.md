# Contract Generator

Веб-приложение для генерации договоров на русском и казахском языках.

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/marguberk/contract-generator.git
cd contract-generator
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Запустите приложение:
```bash
python app.py
```

## Использование

1. Откройте браузер и перейдите по адресу `http://localhost:5000`
2. Заполните форму договора
3. Скачайте сгенерированный PDF файл

## Структура проекта

- `app.py` - основной файл приложения
- `contract_generator.py` - генератор PDF документов
- `forms.py` - формы Flask-WTF
- `translations.py` - переводы интерфейса
- `validators.py` - пользовательские валидаторы
- `templates/` - HTML шаблоны
- `static/` - статические файлы 