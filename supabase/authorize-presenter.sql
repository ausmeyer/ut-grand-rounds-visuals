-- First create this user in Supabase Authentication > Users > Add user.
-- Use a private password and confirm the email. This account is for the poll
-- application; signing into the Supabase dashboard does not create it.
-- Run after poll-01.sql. No password or administrative secret belongs here.
do $$
declare v_id uuid;
begin
  select id into v_id from auth.users
  where lower(email) = 'austin.g.meyer@gmail.com'
    and email_confirmed_at is not null and coalesce(is_anonymous, false) = false;
  if v_id is null then
    raise exception 'Create and confirm the presenter user austin.g.meyer@gmail.com first';
  end if;
  insert into polling.presenters (user_id) values (v_id) on conflict do nothing;
end;
$$;
