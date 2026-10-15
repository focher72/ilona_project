# ilona_project — книга жалоб и предложений команды веба

Одностраничный сайт на Vercel с БД.

## Стэк

- **Frontend**: `index.html` (SPA, работает напрямую в браузере)
- **Бэкенд**: FastAPI (`app.py`), разворачивается на Vercel автоматически (Python runtime)
- **База данных**: Supabase (PostgreSQL, бесплатный тариф) — см. `schema.sql`

## Развёртывание на Vercel

1. Создайте бесплатный проект Supabase: https://supabase.com — таблицу `tickets` из файла `schema.sql` (включая политики доступа).
2. В настройках Vercel (проект → Settings → Environment Variables) добавьте:
   - `SUPABASE_URL` — URL проекта Supabase
   - `SUPABASE_KEY` — anon ключ из Settings → API
3. Подключите репозиторий `focher72/ilona_project` к Vercel через **Projects → Add Git Repository** (автоматический деплой при пуше).
4. Готово: сайт доступен по URL, данные хранятся в Supabase.

> Внимание: локальный SQLite-файл не работает в serverless-окружении Vercel (нет постоянного диска). Поэтому мы используем Supabase. Если нужно именно SQLite-совместимое хранилище, замените в `index.html` Supabase на драйвер `turso-serverless` (планируется).
