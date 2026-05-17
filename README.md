# Text-to-SQL Agent

LLM-агент, который принимает вопросы на естественном языке, преобразует их в SQL-запросы и возвращает данные из Excel-файла. Интерфейс реализован на Streamlit.

## Возможности

- Чат-интерфейс: задавайте вопросы к данным на обычном языке
- Агент сам изучает схему таблицы, генерирует SQL и выполняет запрос
- Результаты отображаются в виде интерактивных таблиц прямо в чате
- Каждый SQL-запрос можно раскрыть и посмотреть
- Поддержка двух LLM-провайдеров: **Anthropic Claude** и **OpenAI GPT**
- Провайдер и модель настраиваются в `config.yaml` без изменения кода

## Структура проекта

```
text-2-sql/
├── app.py                    # Streamlit-приложение
├── config.yaml               # Настройки LLM и источника данных
├── requirements.txt          # Зависимости Python
├── .env.example              # Шаблон файла с API-ключами
├── generate_sample_data.py   # Скрипт генерации тестового Excel
├── data/
│   └── sales_data.xlsx       # Excel-файл с данными (200 строк продаж)
├── skills/
│   ├── text_to_sql.py        # Системный промпт и форматирование схемы
│   └── pandas_query.py       # Загрузка Excel, выполнение SQL через DuckDB
└── agent/
    └── llm_agent.py          # LLM-агент с поддержкой Anthropic и OpenAI
```

## Быстрый старт

### 1. Установите зависимости

```bash
pip install -r requirements.txt
```

### 2. Настройте API-ключ

```bash
cp .env.example .env
```

Откройте `.env` и вставьте ключ нужного провайдера:

```env
# Для Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Для OpenAI
OPENAI_API_KEY=sk-...
```

### 3. Настройте провайдера в `config.yaml`

```yaml
llm:
  provider: anthropic   # anthropic | openai
  model: claude-sonnet-4-6
  api_key_env: ANTHROPIC_API_KEY
  max_tokens: 4096

data:
  excel_file: data/sales_data.xlsx
  sheet_name: null       # null = первый лист
  table_name: sales      # имя таблицы в SQL-запросах
```

Для OpenAI замените:

```yaml
llm:
  provider: openai
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
```

### 4. Запустите приложение

```bash
streamlit run app.py
```

Откройте браузер по адресу `http://localhost:8501`.

## Использование своего Excel-файла

1. Положите файл в папку `data/`
2. Укажите путь в `config.yaml`:
   ```yaml
   data:
     excel_file: data/your_file.xlsx
     table_name: my_table
   ```
3. Перезапустите приложение

## Как это работает

```
Пользователь → вопрос
    ↓
LLM-агент → вызов инструмента get_data_schema
    ↓
Агент получает схему таблицы (колонки, типы, примеры)
    ↓
LLM-агент → вызов инструмента execute_sql_query(sql=...)
    ↓
DuckDB выполняет SQL на pandas DataFrame
    ↓
Агент формулирует ответ + возвращает таблицу результатов
```

Инструменты реализованы в папке `skills/`:
- `get_data_schema` — возвращает структуру загруженного DataFrame
- `execute_sql_query` — выполняет произвольный DuckDB SQL и возвращает результат

## Тестовые данные

Файл `data/sales_data.xlsx` содержит 200 строк данных о продажах:

| Колонка | Тип | Описание |
|---|---|---|
| order_id | VARCHAR | Номер заказа |
| date | DATE | Дата заказа |
| product | VARCHAR | Название товара |
| category | VARCHAR | Категория товара |
| quantity | INTEGER | Количество |
| unit_price | FLOAT | Цена за единицу |
| total_amount | FLOAT | Сумма заказа |
| region | VARCHAR | Регион |
| salesperson | VARCHAR | Менеджер по продажам |
| customer | VARCHAR | Клиент |
| status | VARCHAR | Статус заказа |

Примеры вопросов:
- *Какова общая выручка по регионам?*
- *Топ-5 товаров по количеству продаж*
- *Сколько заказов в статусе Pending?*
- *Средний чек по категориям товаров*

## Требования

- Python 3.10+
- API-ключ Anthropic или OpenAI
