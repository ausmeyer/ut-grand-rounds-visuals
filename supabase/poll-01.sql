-- Run in this project's Supabase SQL Editor as the project administrator.
-- Creates only Poll 1 objects. No existing responses or sessions are deleted.
begin;

create schema if not exists polling;
revoke all on schema polling from public, anon, authenticated;

create table if not exists polling.presenters (
  user_id uuid primary key references auth.users(id) on delete cascade
);
create table if not exists polling.sessions (
  id uuid primary key default gen_random_uuid(),
  name text not null check (length(btrim(name)) between 1 and 80),
  state text not null default 'ready' check (state in ('ready', 'open', 'closed', 'revealed')),
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now()
);
create table if not exists polling.responses (
  session_id uuid not null references polling.sessions(id),
  user_id uuid not null references auth.users(id),
  week integer,
  unsure boolean not null,
  submitted_at timestamptz not null default now(),
  primary key (session_id, user_id),
  check ((unsure and week is null) or
         (not unsure and week is not null and (week between 44 and 52 or week between 1 and 20)))
);

alter table polling.presenters enable row level security;
alter table polling.sessions enable row level security;
alter table polling.responses enable row level security;
revoke all on polling.presenters, polling.sessions, polling.responses from public, anon, authenticated;

-- Private tables have no client-facing policies or grants. Only these narrowly
-- scoped functions expose operations. The owning administrator bypasses RLS;
-- each function must therefore perform its own authorization and state checks.
create or replace function public.poll1_is_presenter()
returns boolean language sql stable security definer set search_path = '' as $$
  select coalesce((auth.jwt()->>'is_anonymous')::boolean, true) = false
    and exists (select 1 from polling.presenters p where p.user_id = auth.uid());
$$;

create or replace function public.poll1_create_session(p_name text)
returns uuid language plpgsql security definer set search_path = '' as $$
declare v_id uuid;
begin
  if not public.poll1_is_presenter() then
    raise exception 'Presenter access required' using errcode = '42501';
  end if;
  insert into polling.sessions (name, created_by) values (btrim(p_name), auth.uid()) returning id into v_id;
  return v_id;
end;
$$;

create or replace function public.poll1_list_sessions()
returns jsonb language plpgsql security definer set search_path = '' as $$
begin
  if not public.poll1_is_presenter() then
    raise exception 'Presenter access required' using errcode = '42501';
  end if;
  return coalesce((select jsonb_agg(to_jsonb(s) order by s.created_at desc) from
    (select id, name, state, created_at from polling.sessions order by created_at desc limit 100) s), '[]'::jsonb);
end;
$$;

create or replace function public.poll1_status(p_session uuid)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare s polling.sessions; v_count bigint;
begin
  select * into s from polling.sessions where id = p_session;
  if not found then raise exception 'Poll session not found' using errcode = 'P0002'; end if;
  if public.poll1_is_presenter() or s.state = 'revealed' then
    select count(*) into v_count from polling.responses where session_id = p_session;
  end if;
  return jsonb_build_object('id', s.id, 'name', s.name, 'state', s.state, 'response_count', v_count);
end;
$$;

create or replace function public.poll1_transition(p_session uuid, p_action text)
returns text language plpgsql security definer set search_path = '' as $$
declare v_state text; v_next text;
begin
  if not public.poll1_is_presenter() then
    raise exception 'Presenter access required' using errcode = '42501';
  end if;
  -- Uses the same row lock as submission. Once close commits, subsequent
  -- submissions cannot enter the frozen set, including requests already queued.
  select state into v_state from polling.sessions where id = p_session for update;
  if not found then raise exception 'Poll session not found' using errcode = 'P0002'; end if;
  v_next := case p_action when 'open' then 'open' when 'close' then 'closed' when 'reveal' then 'revealed' end;
  if v_next is null then raise exception 'Unknown poll action'; end if;
  if v_state = v_next then return v_state; end if; -- retry of an acknowledged transition
  if not ((v_state = 'ready' and p_action = 'open') or
          (v_state = 'open' and p_action = 'close') or
          (v_state = 'closed' and p_action = 'reveal')) then
    raise exception 'Invalid poll transition';
  end if;
  update polling.sessions set state = v_next where id = p_session;
  return v_next;
end;
$$;

create or replace function public.poll1_submit(p_session uuid, p_week integer, p_unsure boolean)
returns boolean language plpgsql security definer set search_path = '' as $$
declare v_state text;
begin
  if auth.uid() is null then raise exception 'Sign in to submit' using errcode = '42501'; end if;
  if p_unsure is null or
     (p_unsure and p_week is not null) or
     (not p_unsure and (p_week is null or not (p_week between 44 and 52 or p_week between 1 and 20))) then
    raise exception 'Choose a valid week or Not sure' using errcode = '22023';
  end if;
  select state into v_state from polling.sessions where id = p_session for update;
  if not found then raise exception 'Poll session not found' using errcode = 'P0002'; end if;
  if v_state <> 'open' then raise exception 'Voting is not open' using errcode = '42501'; end if;
  insert into polling.responses (session_id, user_id, week, unsure)
    values (p_session, auth.uid(), p_week, p_unsure)
    on conflict (session_id, user_id) do update
      set week = excluded.week, unsure = excluded.unsure, submitted_at = now();
  return true;
end;
$$;

create or replace function public.poll1_results(p_session uuid)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare v_state text; v_bins jsonb; v_unsure bigint;
begin
  select state into v_state from polling.sessions where id = p_session;
  if not found then raise exception 'Poll session not found' using errcode = 'P0002'; end if;
  if v_state <> 'revealed' then raise exception 'Results have not been revealed' using errcode = '42501'; end if;
  select jsonb_agg(jsonb_build_object('week', w.week, 'count',
    (select count(*) from polling.responses r where r.session_id = p_session and r.week = w.week)) order by w.i)
    into v_bins from (select i, ((43 + i) % 52) + 1 as week from generate_series(0, 28) i) w;
  select count(*) into v_unsure from polling.responses where session_id = p_session and unsure;
  return jsonb_build_object('bins', v_bins, 'unsure', v_unsure);
end;
$$;

create or replace function public.poll1_delete_session(p_session uuid)
returns boolean language plpgsql security definer set search_path = '' as $$
declare v_state text;
begin
  if not public.poll1_is_presenter() then
    raise exception 'Presenter access required' using errcode = '42501';
  end if;
  -- Share the submission/transition lock so an open poll cannot be deleted.
  select state into v_state from polling.sessions where id = p_session for update;
  if not found then return true; end if; -- safe retry after a completed deletion
  if v_state = 'open' then
    raise exception 'Close voting before deleting this session' using errcode = '42501';
  end if;
  delete from polling.responses where session_id = p_session;
  delete from polling.sessions where id = p_session;
  return true;
end;
$$;

-- PostgreSQL grants function execution to PUBLIC by default; remove that grant
-- explicitly for every function, including helpers, before exposing the API.
revoke all on function public.poll1_is_presenter() from public, anon, authenticated;
revoke all on function public.poll1_create_session(text) from public, anon, authenticated;
revoke all on function public.poll1_list_sessions() from public, anon, authenticated;
revoke all on function public.poll1_status(uuid) from public, anon, authenticated;
revoke all on function public.poll1_transition(uuid, text) from public, anon, authenticated;
revoke all on function public.poll1_submit(uuid, integer, boolean) from public, anon, authenticated;
revoke all on function public.poll1_results(uuid) from public, anon, authenticated;
revoke all on function public.poll1_delete_session(uuid) from public, anon, authenticated;
grant execute on function public.poll1_is_presenter(), public.poll1_create_session(text),
  public.poll1_list_sessions(), public.poll1_transition(uuid, text),
  public.poll1_submit(uuid, integer, boolean), public.poll1_delete_session(uuid) to authenticated;
grant execute on function public.poll1_status(uuid), public.poll1_results(uuid) to anon, authenticated;

notify pgrst, 'reload schema';
commit;
