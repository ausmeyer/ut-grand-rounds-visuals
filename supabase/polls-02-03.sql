-- Run in Supabase SQL Editor after poll-01.sql and presenter authorization.
-- Adds Polls 2 and 3. Does not alter or delete Poll 1 sessions or responses.
begin;

create table if not exists polling.section_sessions (
  id uuid primary key default gen_random_uuid(),
  poll_number integer not null check (poll_number in (2,3)),
  name text not null check (length(btrim(name)) between 1 and 80),
  state text not null default 'ready' check (state in ('ready','open','closed','revealed')),
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  unique (id,poll_number)
);
create table if not exists polling.section_responses (
  session_id uuid not null,
  poll_number integer not null,
  user_id uuid not null references auth.users(id),
  answer_kind text not null,
  value_start integer,
  value_end integer,
  submitted_at timestamptz not null default now(),
  primary key (session_id,user_id),
  foreign key (session_id,poll_number) references polling.section_sessions(id,poll_number),
  check (
    (poll_number=3 and answer_kind='not_sure' and value_start is null and value_end is null) or
    (poll_number=2 and answer_kind='weeks' and value_start is not null and value_start between 0 and 4 and value_end is null) or
    (poll_number=3 and answer_kind='window' and value_start is not null and value_end is not null
      and value_start between 1 and 52 and value_end between 1 and 52)
  )
);
alter table polling.section_sessions enable row level security;
alter table polling.section_responses enable row level security;
revoke all on polling.section_sessions,polling.section_responses from public,anon,authenticated;

create or replace function public.poll23_create_session(p_poll integer,p_name text)
returns uuid language plpgsql security definer set search_path='' as $$
declare v_id uuid;
begin
  if not public.poll1_is_presenter() then raise exception 'Presenter access required' using errcode='42501'; end if;
  if p_poll is null or p_poll not in (2,3) then raise exception 'Unknown poll' using errcode='22023'; end if;
  insert into polling.section_sessions(poll_number,name,created_by)
    values(p_poll,btrim(p_name),auth.uid()) returning id into v_id;
  return v_id;
end;
$$;

create or replace function public.poll23_list_sessions(p_poll integer)
returns jsonb language plpgsql security definer set search_path='' as $$
begin
  if not public.poll1_is_presenter() then raise exception 'Presenter access required' using errcode='42501'; end if;
  return coalesce((select jsonb_agg(to_jsonb(s) order by s.created_at desc) from
    (select id,name,state,poll_number,created_at from polling.section_sessions
     where poll_number=p_poll order by created_at desc limit 100) s),'[]'::jsonb);
end;
$$;

create or replace function public.poll23_status(p_poll integer,p_session uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare s polling.section_sessions; v_count bigint;
begin
  select * into s from polling.section_sessions where id=p_session and poll_number=p_poll;
  if not found then raise exception 'Poll session not found' using errcode='P0002'; end if;
  if public.poll1_is_presenter() or s.state='revealed' then
    select count(*) into v_count from polling.section_responses where session_id=p_session;
  end if;
  return jsonb_build_object('id',s.id,'name',s.name,'poll_number',s.poll_number,'state',s.state,'response_count',v_count);
end;
$$;

create or replace function public.poll23_transition(p_poll integer,p_session uuid,p_action text)
returns text language plpgsql security definer set search_path='' as $$
declare v_state text; v_next text;
begin
  if not public.poll1_is_presenter() then raise exception 'Presenter access required' using errcode='42501'; end if;
  select state into v_state from polling.section_sessions where id=p_session and poll_number=p_poll for update;
  if not found then raise exception 'Poll session not found' using errcode='P0002'; end if;
  v_next:=case p_action when 'open' then 'open' when 'close' then 'closed' when 'reveal' then 'revealed' end;
  if v_next is null then raise exception 'Unknown poll action'; end if;
  if v_state=v_next then return v_state; end if;
  if not ((v_state='ready' and p_action='open') or (v_state='open' and p_action='close') or
          (v_state='closed' and p_action='reveal')) then raise exception 'Invalid poll transition'; end if;
  update polling.section_sessions set state=v_next where id=p_session;
  return v_next;
end;
$$;

create or replace function public.poll23_submit(p_poll integer,p_session uuid,p_kind text,p_start integer,p_end integer)
returns boolean language plpgsql security definer set search_path='' as $$
declare v_state text;
begin
  if auth.uid() is null then raise exception 'Sign in to submit' using errcode='42501'; end if;
  select state into v_state from polling.section_sessions where id=p_session and poll_number=p_poll for update;
  if not found then raise exception 'Poll session not found' using errcode='P0002'; end if;
  if v_state<>'open' then raise exception 'Voting is not open' using errcode='42501'; end if;
  begin
    insert into polling.section_responses(session_id,poll_number,user_id,answer_kind,value_start,value_end)
      values(p_session,p_poll,auth.uid(),p_kind,p_start,p_end)
      on conflict (session_id,user_id) do update set answer_kind=excluded.answer_kind,
        value_start=excluded.value_start,value_end=excluded.value_end,submitted_at=now();
  exception when check_violation or not_null_violation then
    raise exception 'Choose a valid response for this poll' using errcode='22023';
  end;
  return true;
end;
$$;

create or replace function public.poll23_results(p_poll integer,p_session uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_state text; v_bins jsonb; v_numeric bigint; v_unsure bigint;
begin
  select state into v_state from polling.section_sessions where id=p_session and poll_number=p_poll;
  if not found then raise exception 'Poll session not found' using errcode='P0002'; end if;
  if v_state<>'revealed' then raise exception 'Results have not been revealed' using errcode='42501'; end if;
  if p_poll=2 then
    select jsonb_agg(jsonb_build_object('value',w.value,'count',
      (select count(*) from polling.section_responses r where r.session_id=p_session
       and r.answer_kind='weeks' and r.value_start=w.value)) order by w.value)
      into v_bins from generate_series(0,4) w(value);
  else
    -- Inclusive windows. A last week before the first week crosses New Year.
    select jsonb_agg(jsonb_build_object('value',w.value,'count',
      (select count(*) from polling.section_responses r where r.session_id=p_session and r.answer_kind='window'
       and case when r.value_start<=r.value_end then w.value between r.value_start and r.value_end
         else w.value>=r.value_start or w.value<=r.value_end end)) order by w.value)
      into v_bins from generate_series(1,52) w(value);
  end if;
  select count(*) filter (where answer_kind in ('weeks','window')),
    count(*) filter (where answer_kind='not_sure')
    into v_numeric,v_unsure from polling.section_responses where session_id=p_session;
  return jsonb_build_object('bins',v_bins,'numeric_count',v_numeric,'unsure',v_unsure);
end;
$$;

create or replace function public.poll23_delete_session(p_poll integer,p_session uuid)
returns boolean language plpgsql security definer set search_path='' as $$
declare v_state text;
begin
  if not public.poll1_is_presenter() then raise exception 'Presenter access required' using errcode='42501'; end if;
  select state into v_state from polling.section_sessions where id=p_session and poll_number=p_poll for update;
  if not found then return true; end if;
  if v_state='open' then raise exception 'Close voting before deleting this session' using errcode='42501'; end if;
  delete from polling.section_responses where session_id=p_session;
  delete from polling.section_sessions where id=p_session;
  return true;
end;
$$;

revoke all on function public.poll23_create_session(integer,text) from public,anon,authenticated;
revoke all on function public.poll23_list_sessions(integer) from public,anon,authenticated;
revoke all on function public.poll23_status(integer,uuid) from public,anon,authenticated;
revoke all on function public.poll23_transition(integer,uuid,text) from public,anon,authenticated;
revoke all on function public.poll23_submit(integer,uuid,text,integer,integer) from public,anon,authenticated;
revoke all on function public.poll23_results(integer,uuid) from public,anon,authenticated;
revoke all on function public.poll23_delete_session(integer,uuid) from public,anon,authenticated;
grant execute on function public.poll23_create_session(integer,text),public.poll23_list_sessions(integer),
  public.poll23_transition(integer,uuid,text),public.poll23_submit(integer,uuid,text,integer,integer),
  public.poll23_delete_session(integer,uuid) to authenticated;
grant execute on function public.poll23_status(integer,uuid),public.poll23_results(integer,uuid) to anon,authenticated;
notify pgrst,'reload schema';
commit;
