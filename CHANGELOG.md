# Changelog

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/).
Проект следует [Semantic Versioning](https://semver.org/lang/ru/).

## [1.0.0] — 2026-06-06

### Добавлено

- ETL-пайплайн: извлечение данных из CSV и MS SQL Server
- Расчёт метрик прибыльности: маржа, burn rate, revenue/hour, overtime ratio
- Детекция аномалий (z-score, IQR): убыточные проекты, перерасход часов, reopens
- AI-анализ: интеграция с OpenAI и Anthropic, fallback на rule-based анализ
- Веб-дашборд: 5 страниц (главная, проекты, стеки, задачи, разработчики)
- REST API: `/api/summary`, `/api/anomalies`, `/api/ai-analysis`, `/api/etl/run`
- Планировщик: автоматический запуск ETL по расписанию (APScheduler)
- Интеграция с Google Sheets: автоматический экспорт отчётов
- Health-check endpoint: `/health`
- Dockerfile для контейнерного деплоя
- 13 юнит-тестов
- Полная документация (README.md)

### Безопасность

- CORS middleware с настраиваемыми origins
- Безопасные дефолты (debug=false, обязательный secret_key в production)
- Non-root пользователь в Docker
- Глобальный обработчик ошибок (без утечки стектрейсов)
