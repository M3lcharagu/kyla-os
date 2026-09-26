-- KYLA core schema for Supabase (free tier friendly).
-- Run once in the Supabase SQL editor, or with `supabase db push`.
-- Safe to re-run: uses IF NOT EXISTS / CREATE OR REPLACE / DROP POLICY IF EXISTS.
--
-- Security model
--   * Row Level Security is ON for every table.
--   * Signed-in users (magic link) only see and change their own rows: auth.uid() = user_id.
--   * GitHub Actions and the online bridge write with the service_role / secret key,
--     which bypasses RLS. Those "system" rows have user_id = NULL.
--   * The KYLA owner (the first account that signs in, flagged profiles.is_owner)
--     can also READ system rows (user_id IS NULL), e.g. daily briefs and bridge runs.
--   * The service_role / secret key must never ship in web code.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------- profiles
create table if not exists public.profiles (
  id           uuid primary key references auth.users (id) on delete cascade,
  email        text,
  display_name text,
  is_owner     boolean not null default false,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- Auto-create a profile for every new auth user. The very first user becomes the owner.
create or replace function public.kyla_handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email, display_name, is_owner)
  values (
    new.id,
    new.email,
    split_part(coalesce(new.email, ''), '@', 1),
    not exists (select 1 from public.profiles where is_owner)
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists kyla_on_auth_user_created on auth.users;
create trigger kyla_on_auth_user_created
  after insert on auth.users
  for each row execute function public.kyla_handle_new_user();

-- Backfill profiles for users that signed up before this migration ran.
insert into public.profiles (id, email, display_name)
select u.id, u.email, split_part(coalesce(u.email, ''), '@', 1)
from auth.users u
on conflict (id) do nothing;
update public.profiles p set is_owner = true
where not exists (select 1 from public.profiles where is_owner)
  and p.id = (select id from public.profiles order by created_at asc limit 1);

-- Owner check used by read policies on system rows (SECURITY DEFINER avoids RLS recursion).
create or replace function public.kyla_is_owner()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select coalesce((select is_owner from public.profiles where id = auth.uid()), false);
$$;

-- Keep updated_at fresh.
create or replace function public.kyla_touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ---------------------------------------------------------------- agent_runs
create table if not exists public.agent_runs (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users (id) on delete cascade default auth.uid(),
  agent       text not null,
  room        text,
  status      text not null default 'ok'
              check (status in ('queued', 'running', 'ok', 'error', 'skipped')),
  input       text,
  output      text,
  source      text not null default 'web',   -- web | bridge | actions
  meta        jsonb not null default '{}'::jsonb,
  started_at  timestamptz not null default now(),
  finished_at timestamptz,
  created_at  timestamptz not null default now()
);
create index if not exists agent_runs_user_created_idx on public.agent_runs (user_id, created_at desc);

-- ---------------------------------------------------------------- chat_messages
create table if not exists public.chat_messages (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users (id) on delete cascade default auth.uid(),
  room       text,
  agent      text,
  role       text not null default 'user' check (role in ('user', 'assistant', 'system')),
  content    text not null,
  created_at timestamptz not null default now()
);
create index if not exists chat_messages_user_created_idx on public.chat_messages (user_id, created_at desc);

-- ---------------------------------------------------------------- tasks (tasks + notes)
create table if not exists public.tasks (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users (id) on delete cascade default auth.uid(),
  kind       text not null default 'task' check (kind in ('task', 'note')),
  title      text not null,
  body       text,
  status     text not null default 'todo' check (status in ('todo', 'doing', 'done')),
  room       text,
  due_at     timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists tasks_user_status_idx on public.tasks (user_id, status, created_at desc);
drop trigger if exists tasks_touch on public.tasks;
create trigger tasks_touch before update on public.tasks
  for each row execute function public.kyla_touch_updated_at();

-- ---------------------------------------------------------------- memories (key / value)
create table if not exists public.memories (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users (id) on delete cascade default auth.uid(),
  key        text not null,
  value      jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, key)
);
drop trigger if exists memories_touch on public.memories;
create trigger memories_touch before update on public.memories
  for each row execute function public.kyla_touch_updated_at();

-- ---------------------------------------------------------------- store_leads (KYLA store orders / leads)
create table if not exists public.store_leads (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid references auth.users (id) on delete cascade default auth.uid(),
  product    text not null,
  price      numeric(12, 2),
  currency   text not null default 'KES',
  contact    text,                           -- phone / email / WhatsApp handle
  source     text not null default 'manual', -- manual | whatsapp | gumroad | store
  status     text not null default 'new'
             check (status in ('new', 'contacted', 'paid', 'delivered', 'cancelled')),
  note       text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists store_leads_user_created_idx on public.store_leads (user_id, created_at desc);
drop trigger if exists store_leads_touch on public.store_leads;
create trigger store_leads_touch before update on public.store_leads
  for each row execute function public.kyla_touch_updated_at();

-- ---------------------------------------------------------------- news_briefs
create table if not exists public.news_briefs (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid references auth.users (id) on delete cascade default auth.uid(),
  brief_date date not null,
  kind       text not null default 'daily',  -- daily | repo-digest | stack-health
  title      text,
  body_md    text not null,
  source     text not null default 'actions',
  created_at timestamptz not null default now(),
  unique (brief_date, kind)
);

-- ---------------------------------------------------------------- grants (Data API)
grant usage on schema public to anon, authenticated, service_role;
-- profiles: users may read their row and edit display_name only (never is_owner).
revoke all on public.profiles from anon, authenticated;
grant select on public.profiles to authenticated;
grant update (display_name) on public.profiles to authenticated;
grant select, insert, update, delete on
  public.agent_runs, public.chat_messages, public.tasks,
  public.memories, public.store_leads, public.news_briefs
  to authenticated;
grant all on
  public.profiles, public.agent_runs, public.chat_messages, public.tasks,
  public.memories, public.store_leads, public.news_briefs
  to service_role;
grant execute on function public.kyla_is_owner() to authenticated;

-- ---------------------------------------------------------------- Row Level Security
alter table public.profiles      enable row level security;
alter table public.agent_runs    enable row level security;
alter table public.chat_messages enable row level security;
alter table public.tasks         enable row level security;
alter table public.memories      enable row level security;
alter table public.store_leads   enable row level security;
alter table public.news_briefs   enable row level security;

-- profiles: you can read / update only your own row (column grants keep is_owner read-only).
drop policy if exists profiles_select_own on public.profiles;
create policy profiles_select_own on public.profiles
  for select to authenticated using (auth.uid() = id);
drop policy if exists profiles_update_own on public.profiles;
create policy profiles_update_own on public.profiles
  for update to authenticated using (auth.uid() = id) with check (auth.uid() = id);

-- Owner-only CRUD on user tables: auth.uid() = user_id.
do $$
declare t text;
begin
  foreach t in array array['agent_runs', 'chat_messages', 'tasks', 'memories', 'store_leads', 'news_briefs']
  loop
    execute format('drop policy if exists %I on public.%I', t || '_select_own', t);
    execute format('create policy %I on public.%I for select to authenticated using (auth.uid() = user_id)', t || '_select_own', t);
    execute format('drop policy if exists %I on public.%I', t || '_insert_own', t);
    execute format('create policy %I on public.%I for insert to authenticated with check (auth.uid() = user_id)', t || '_insert_own', t);
    execute format('drop policy if exists %I on public.%I', t || '_update_own', t);
    execute format('create policy %I on public.%I for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id)', t || '_update_own', t);
    execute format('drop policy if exists %I on public.%I', t || '_delete_own', t);
    execute format('create policy %I on public.%I for delete to authenticated using (auth.uid() = user_id)', t || '_delete_own', t);
  end loop;
end $$;

-- The owner can READ system rows written by Actions / bridge (user_id IS NULL).
do $$
declare t text;
begin
  foreach t in array array['agent_runs', 'store_leads', 'news_briefs']
  loop
    execute format('drop policy if exists %I on public.%I', t || '_select_system_owner', t);
    execute format('create policy %I on public.%I for select to authenticated using (user_id is null and public.kyla_is_owner())', t || '_select_system_owner', t);
  end loop;
end $$;

-- No anon policies: logged-out visitors cannot read or write anything.
