-- Схема таблицы для доски жалоб и предложений (Supabase / PostgreSQL)

create table if not exists tickets (
    id              integer generated always as identity primary key,
    type            text not null check (type in ('problems', 'ideas', 'good', 'progress')),
    status          text not null,
    comment         text not null,
    author          text,
    created_at      timestamptz not null default now(),
    resolution_comment text,
    resolution_author text
);

-- Политики доступа: анонимные пользователи (anon) могут читать, создавать,
-- редактировать и удалять тикеты (аналог работающей для них БД в浏览器 с локальным хранилищем).
create policy "Public read tickets" on tickets
    for select to anon
    using (true);

create policy "Public insert tickets" on tickets
    for insert to anon
    with check (true);

create policy "Public update tickets" on tickets
    for update to anon
    using (true) with check (true);

create policy "Public delete tickets" on tickets
    for delete to anon
    using (true);

-- Индексы для скорости (опционально)
create index if not exists idx_tickets_status on tickets (status);
create index if not exists idx_tickets_type on tickets (type);
