-- Unified backend for all three audience polls. Run this entire file in the
-- existing project's Supabase SQL Editor when no poll is actively collecting.
-- Supports a fresh install, Poll 1 alone, or both earlier setup scripts.
-- Preserves presenter authorization, session IDs, states, votes and timestamps.
-- Legacy tables move to a private archive once; all APIs then use the live tables.
begin;
set local lock_timeout='5s';

create schema if not exists polling;
create schema if not exists polling_archive;
revoke all on schema polling,polling_archive from public,anon,authenticated;
create table if not exists polling.schema_migrations (
  version integer primary key,
  applied_at timestamptz not null default now()
);
create table if not exists polling.presenters (
  user_id uuid primary key references auth.users(id) on delete cascade
);
alter table polling.schema_migrations enable row level security;
alter table polling.presenters enable row level security;
revoke all on polling.schema_migrations,polling.presenters from public,anon,authenticated;

-- Transactional DDL prevents a half-completed migration. A lock timeout or UUID
-- collision aborts the transaction instead of silently omitting any records.
do $$
begin
  if not exists(select 1 from polling.schema_migrations where version=1) then
    if to_regclass('polling.sessions') is not null then
      lock table polling.sessions,polling.responses in access exclusive mode;
      alter table polling.sessions set schema polling_archive;
      alter table polling.responses set schema polling_archive;
    end if;
    if to_regclass('polling.section_sessions') is not null then
      lock table polling.section_sessions,polling.section_responses in access exclusive mode;
      alter table polling.section_sessions set schema polling_archive;
      alter table polling.section_responses set schema polling_archive;
    end if;
  end if;
end;
$$;
revoke all on all tables in schema polling_archive from public,anon,authenticated;

create or replace function public.poll_is_presenter()
returns boolean language sql stable security definer set search_path='' as $$
  select coalesce((auth.jwt()->>'is_anonymous')::boolean,true)=false
    and exists(select 1 from polling.presenters p where p.user_id=auth.uid());
$$;

create table if not exists polling.sessions (
  id uuid primary key default gen_random_uuid(),
  poll_number integer not null check (poll_number in (1,2,3)),
  name text not null check (length(btrim(name)) between 1 and 80),
  state text not null default 'ready' check (state in ('ready','open','closed','revealed')),
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  unique (id,poll_number)
);
create table if not exists polling.responses (
  session_id uuid not null,
  poll_number integer not null,
  user_id uuid not null references auth.users(id),
  answer_kind text not null,
  value_start integer,
  value_end integer,
  submitted_at timestamptz not null default now(),
  primary key (session_id,user_id),
  foreign key (session_id,poll_number) references polling.sessions(id,poll_number),
  check (
    (poll_number in (1,3) and answer_kind='not_sure' and value_start is null and value_end is null) or
    (poll_number=1 and answer_kind='week' and value_start is not null
      and (value_start between 44 and 52 or value_start between 1 and 20) and value_end is null) or
    (poll_number=2 and answer_kind='weeks' and value_start is not null and value_start between 0 and 4 and value_end is null) or
    (poll_number=3 and answer_kind='window' and value_start is not null and value_end is not null
      and value_start between 1 and 52 and value_end between 1 and 52)
  )
);
alter table polling.sessions enable row level security;
alter table polling.responses enable row level security;
revoke all on polling.sessions,polling.responses from public,anon,authenticated;

create or replace function public.poll_create_session(p_poll integer,p_name text)
returns uuid language plpgsql security definer set search_path='' as $$
declare v_id uuid;
begin
  if not public.poll_is_presenter() then raise exception 'Presenter access required' using errcode='42501'; end if;
  if p_poll is null or p_poll not in (1,2,3) then raise exception 'Unknown poll' using errcode='22023'; end if;
  insert into polling.sessions(poll_number,name,created_by)
    values(p_poll,btrim(p_name),auth.uid()) returning id into v_id;
  return v_id;
end;
$$;

create or replace function public.poll_list_sessions(p_poll integer)
returns jsonb language plpgsql security definer set search_path='' as $$
begin
  if not public.poll_is_presenter() then raise exception 'Presenter access required' using errcode='42501'; end if;
  return coalesce((select jsonb_agg(to_jsonb(s) order by s.created_at desc) from
    (select id,name,state,poll_number,created_at from polling.sessions
     where poll_number=p_poll order by created_at desc limit 100) s),'[]'::jsonb);
end;
$$;

create or replace function public.poll_status(p_poll integer,p_session uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare s polling.sessions; v_count bigint;
begin
  select * into s from polling.sessions where id=p_session and poll_number=p_poll;
  if not found then raise exception 'Poll session not found' using errcode='P0002'; end if;
  if public.poll_is_presenter() or s.state='revealed' then
    select count(*) into v_count from polling.responses where session_id=p_session;
  end if;
  return jsonb_build_object('id',s.id,'name',s.name,'poll_number',s.poll_number,'state',s.state,'response_count',v_count);
end;
$$;

create or replace function public.poll_transition(p_poll integer,p_session uuid,p_action text)
returns text language plpgsql security definer set search_path='' as $$
declare v_state text; v_next text;
begin
  if not public.poll_is_presenter() then raise exception 'Presenter access required' using errcode='42501'; end if;
  select state into v_state from polling.sessions where id=p_session and poll_number=p_poll for update;
  if not found then raise exception 'Poll session not found' using errcode='P0002'; end if;
  v_next:=case p_action when 'open' then 'open' when 'close' then 'closed' when 'reveal' then 'revealed' end;
  if v_next is null then raise exception 'Unknown poll action'; end if;
  if v_state=v_next then return v_state; end if;
  if not ((v_state='ready' and p_action='open') or (v_state='open' and p_action='close') or
          (v_state='closed' and p_action='reveal')) then raise exception 'Invalid poll transition'; end if;
  update polling.sessions set state=v_next where id=p_session;
  return v_next;
end;
$$;

create or replace function public.poll_submit(p_poll integer,p_session uuid,p_kind text,p_start integer,p_end integer)
returns boolean language plpgsql security definer set search_path='' as $$
declare v_state text;
begin
  if auth.uid() is null then raise exception 'Sign in to submit' using errcode='42501'; end if;
  select state into v_state from polling.sessions where id=p_session and poll_number=p_poll for update;
  if not found then raise exception 'Poll session not found' using errcode='P0002'; end if;
  if v_state<>'open' then raise exception 'Voting is not open' using errcode='42501'; end if;
  begin
    insert into polling.responses(session_id,poll_number,user_id,answer_kind,value_start,value_end)
      values(p_session,p_poll,auth.uid(),p_kind,p_start,p_end)
      on conflict (session_id,user_id) do update set answer_kind=excluded.answer_kind,
        value_start=excluded.value_start,value_end=excluded.value_end,submitted_at=now();
  exception when check_violation or not_null_violation then
    raise exception 'Choose a valid response for this poll' using errcode='22023';
  end;
  return true;
end;
$$;

create or replace function public.poll_results(p_poll integer,p_session uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_state text; v_bins jsonb; v_numeric bigint; v_unsure bigint;
begin
  select state into v_state from polling.sessions where id=p_session and poll_number=p_poll;
  if not found then raise exception 'Poll session not found' using errcode='P0002'; end if;
  if v_state<>'revealed' then raise exception 'Results have not been revealed' using errcode='42501'; end if;
  if p_poll=1 then
    select jsonb_agg(jsonb_build_object('value',w.value,'count',
      (select count(*) from polling.responses r where r.session_id=p_session
       and r.answer_kind='week' and r.value_start=w.value)) order by w.position)
      into v_bins from (select i as position,((43+i)%52)+1 as value from generate_series(0,28) i) w;
  elsif p_poll=2 then
    select jsonb_agg(jsonb_build_object('value',w.value,'count',
      (select count(*) from polling.responses r where r.session_id=p_session
       and r.answer_kind='weeks' and r.value_start=w.value)) order by w.value)
      into v_bins from generate_series(0,4) w(value);
  else
    -- Inclusive windows. A last week before the first week crosses New Year.
    select jsonb_agg(jsonb_build_object('value',w.value,'count',
      (select count(*) from polling.responses r where r.session_id=p_session and r.answer_kind='window'
       and case when r.value_start<=r.value_end then w.value between r.value_start and r.value_end
         else w.value>=r.value_start or w.value<=r.value_end end)) order by w.value)
      into v_bins from generate_series(1,52) w(value);
  end if;
  select count(*) filter (where answer_kind in ('week','weeks','window')),
    count(*) filter (where answer_kind='not_sure')
    into v_numeric,v_unsure from polling.responses where session_id=p_session;
  return jsonb_build_object('bins',v_bins,'numeric_count',v_numeric,'unsure',v_unsure);
end;
$$;

create or replace function public.poll_delete_session(p_poll integer,p_session uuid)
returns boolean language plpgsql security definer set search_path='' as $$
declare v_state text;
begin
  if not public.poll_is_presenter() then raise exception 'Presenter access required' using errcode='42501'; end if;
  select state into v_state from polling.sessions where id=p_session and poll_number=p_poll for update;
  if not found then return true; end if;
  if v_state='open' then raise exception 'Close voting before deleting this session' using errcode='42501'; end if;
  delete from polling.responses where session_id=p_session;
  delete from polling.sessions where id=p_session;
  return true;
end;
$$;

revoke all on function public.poll_create_session(integer,text) from public,anon,authenticated;
revoke all on function public.poll_list_sessions(integer) from public,anon,authenticated;
revoke all on function public.poll_status(integer,uuid) from public,anon,authenticated;
revoke all on function public.poll_transition(integer,uuid,text) from public,anon,authenticated;
revoke all on function public.poll_submit(integer,uuid,text,integer,integer) from public,anon,authenticated;
revoke all on function public.poll_results(integer,uuid) from public,anon,authenticated;
revoke all on function public.poll_delete_session(integer,uuid) from public,anon,authenticated;
grant execute on function public.poll_create_session(integer,text),public.poll_list_sessions(integer),
  public.poll_transition(integer,uuid,text),public.poll_submit(integer,uuid,text,integer,integer),
  public.poll_delete_session(integer,uuid) to authenticated;
grant execute on function public.poll_status(integer,uuid),public.poll_results(integer,uuid) to anon,authenticated;

-- Import only once. Re-running setup must not resurrect subsequently deleted
-- sessions or replace newer votes with the archived pre-migration answers.
do $$
begin
  if not exists(select 1 from polling.schema_migrations where version=1) then
    if to_regclass('polling_archive.sessions') is not null then
      insert into polling.sessions(id,poll_number,name,state,created_by,created_at)
        select id,1,name,state,created_by,created_at from polling_archive.sessions;
      insert into polling.responses(session_id,poll_number,user_id,answer_kind,value_start,value_end,submitted_at)
        select session_id,1,user_id,case when unsure then 'not_sure' else 'week' end,week,null,submitted_at
        from polling_archive.responses;
    end if;
    if to_regclass('polling_archive.section_sessions') is not null then
      insert into polling.sessions(id,poll_number,name,state,created_by,created_at)
        select id,poll_number,name,state,created_by,created_at from polling_archive.section_sessions;
      insert into polling.responses(session_id,poll_number,user_id,answer_kind,value_start,value_end,submitted_at)
        select session_id,poll_number,user_id,answer_kind,value_start,value_end,submitted_at
        from polling_archive.section_responses;
    end if;
    insert into polling.schema_migrations(version) values(1);
  end if;
end;
$$;
revoke all on function public.poll_is_presenter() from public,anon,authenticated;
grant execute on function public.poll_is_presenter() to authenticated;

-- Compatibility adapters for cached pages. They contain no separate lifecycle,
-- authorization or storage implementation; every operation reaches the same API.
create or replace function public.poll1_is_presenter()
returns boolean language sql set search_path='' as $$ select public.poll_is_presenter(); $$;
create or replace function public.poll1_submit(p_session uuid,p_week integer,p_unsure boolean)
returns boolean language plpgsql set search_path='' as $$
begin
  if p_unsure is null or (p_unsure and p_week is not null) or
    (not p_unsure and (p_week is null or not(p_week between 44 and 52 or p_week between 1 and 20))) then
    raise exception 'Choose a valid week or Not sure' using errcode='22023';
  end if;
  return public.poll_submit(1,p_session,case when p_unsure then 'not_sure' else 'week' end,p_week,null);
end;
$$;
create or replace function public.poll1_results(p_session uuid)
returns jsonb language sql set search_path='' as $$
  with result as (select public.poll_results(1,p_session) as data)
  select jsonb_build_object('bins',
    (select jsonb_agg(jsonb_build_object('week',bin->'value','count',bin->'count') order by position)
     from jsonb_array_elements(data->'bins') with ordinality as b(bin,position)),
    'unsure',data->'unsure') from result;
$$;
create or replace function public.poll1_create_session(p_name text)
returns uuid language sql set search_path='' as $$ select public.poll_create_session(1,p_name); $$;
create or replace function public.poll1_list_sessions()
returns jsonb language sql set search_path='' as $$ select public.poll_list_sessions(1); $$;
create or replace function public.poll1_status(p_session uuid)
returns jsonb language sql set search_path='' as $$ select public.poll_status(1,p_session); $$;
create or replace function public.poll1_transition(p_session uuid,p_action text)
returns text language sql set search_path='' as $$ select public.poll_transition(1,p_session,p_action); $$;
create or replace function public.poll1_delete_session(p_session uuid)
returns boolean language sql set search_path='' as $$ select public.poll_delete_session(1,p_session); $$;
create or replace function public.poll23_create_session(p_poll integer,p_name text)
returns uuid language sql set search_path='' as $$ select public.poll_create_session(case when p_poll in (2,3) then p_poll end,p_name); $$;
create or replace function public.poll23_list_sessions(p_poll integer)
returns jsonb language sql set search_path='' as $$ select public.poll_list_sessions(case when p_poll in (2,3) then p_poll end); $$;
create or replace function public.poll23_status(p_poll integer,p_session uuid)
returns jsonb language sql set search_path='' as $$ select public.poll_status(case when p_poll in (2,3) then p_poll end,p_session); $$;
create or replace function public.poll23_transition(p_poll integer,p_session uuid,p_action text)
returns text language sql set search_path='' as $$ select public.poll_transition(case when p_poll in (2,3) then p_poll end,p_session,p_action); $$;
create or replace function public.poll23_delete_session(p_poll integer,p_session uuid)
returns boolean language sql set search_path='' as $$ select public.poll_delete_session(case when p_poll in (2,3) then p_poll end,p_session); $$;
create or replace function public.poll23_submit(p_poll integer,p_session uuid,p_kind text,p_start integer,p_end integer)
returns boolean language sql set search_path='' as $$ select public.poll_submit(case when p_poll in (2,3) then p_poll end,p_session,p_kind,p_start,p_end); $$;
create or replace function public.poll23_results(p_poll integer,p_session uuid)
returns jsonb language sql set search_path='' as $$ select public.poll_results(case when p_poll in (2,3) then p_poll end,p_session); $$;
alter function public.poll1_is_presenter() security invoker;
revoke all on function public.poll1_is_presenter() from public,anon,authenticated;
grant execute on function public.poll1_is_presenter() to authenticated;
alter function public.poll1_create_session(text) security invoker;
revoke all on function public.poll1_create_session(text) from public,anon,authenticated;
grant execute on function public.poll1_create_session(text) to authenticated;
alter function public.poll1_list_sessions() security invoker;
revoke all on function public.poll1_list_sessions() from public,anon,authenticated;
grant execute on function public.poll1_list_sessions() to authenticated;
alter function public.poll1_status(uuid) security invoker;
revoke all on function public.poll1_status(uuid) from public,anon,authenticated;
grant execute on function public.poll1_status(uuid) to anon,authenticated;
alter function public.poll1_transition(uuid,text) security invoker;
revoke all on function public.poll1_transition(uuid,text) from public,anon,authenticated;
grant execute on function public.poll1_transition(uuid,text) to authenticated;
alter function public.poll1_delete_session(uuid) security invoker;
revoke all on function public.poll1_delete_session(uuid) from public,anon,authenticated;
grant execute on function public.poll1_delete_session(uuid) to authenticated;
alter function public.poll1_submit(uuid,integer,boolean) security invoker;
revoke all on function public.poll1_submit(uuid,integer,boolean) from public,anon,authenticated;
grant execute on function public.poll1_submit(uuid,integer,boolean) to authenticated;
alter function public.poll1_results(uuid) security invoker;
revoke all on function public.poll1_results(uuid) from public,anon,authenticated;
grant execute on function public.poll1_results(uuid) to anon,authenticated;
alter function public.poll23_create_session(integer,text) security invoker;
revoke all on function public.poll23_create_session(integer,text) from public,anon,authenticated;
grant execute on function public.poll23_create_session(integer,text) to authenticated;
alter function public.poll23_list_sessions(integer) security invoker;
revoke all on function public.poll23_list_sessions(integer) from public,anon,authenticated;
grant execute on function public.poll23_list_sessions(integer) to authenticated;
alter function public.poll23_status(integer,uuid) security invoker;
revoke all on function public.poll23_status(integer,uuid) from public,anon,authenticated;
grant execute on function public.poll23_status(integer,uuid) to anon,authenticated;
alter function public.poll23_transition(integer,uuid,text) security invoker;
revoke all on function public.poll23_transition(integer,uuid,text) from public,anon,authenticated;
grant execute on function public.poll23_transition(integer,uuid,text) to authenticated;
alter function public.poll23_delete_session(integer,uuid) security invoker;
revoke all on function public.poll23_delete_session(integer,uuid) from public,anon,authenticated;
grant execute on function public.poll23_delete_session(integer,uuid) to authenticated;
alter function public.poll23_submit(integer,uuid,text,integer,integer) security invoker;
revoke all on function public.poll23_submit(integer,uuid,text,integer,integer) from public,anon,authenticated;
grant execute on function public.poll23_submit(integer,uuid,text,integer,integer) to authenticated;
alter function public.poll23_results(integer,uuid) security invoker;
revoke all on function public.poll23_results(integer,uuid) from public,anon,authenticated;
grant execute on function public.poll23_results(integer,uuid) to anon,authenticated;

notify pgrst,'reload schema';
commit;
