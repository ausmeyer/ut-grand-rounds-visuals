import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { PGlite } from '@electric-sql/pglite';
import { WEEKS, weekAt, isWeek, isSession, normalizeResults } from '../docs/assets/poll-01/model.js';

test('slider and histogram preserve all 29 seasonal weeks',()=>{
  assert.deepEqual(WEEKS,[44,45,46,47,48,49,50,51,52,...Array.from({length:20},(_,i)=>i+1)]);
  assert.deepEqual([0,8,9,28].map(weekAt),[44,52,1,20]);
  for(const x of [-1,29,1.5,NaN])assert.throws(()=>weekAt(x));
  for(const x of [0,21,43,53,1.5,'1',null])assert.equal(isWeek(x),false);
  assert.equal(isSession('not-a-session'),false);
  const data={bins:WEEKS.map(week=>({week,count:week===1?2:0})),unsure:3};
  assert.equal(normalizeResults(data).numericCount,2);
  assert.throws(()=>normalizeResults({...data,bins:[...data.bins].reverse()}));
  assert.throws(()=>normalizeResults({...data,unsure:-1}));
});

test('database permissions, transitions, submission validation, and result isolation',async t=>{
  const db=new PGlite();
  const admin='00000000-0000-4000-8000-000000000001';
  const voter='00000000-0000-4000-8000-000000000002';
  const other='00000000-0000-4000-8000-000000000003';
  // Supabase supplies these roles and auth helpers in production. Only this
  // isolated local test creates a minimal equivalent for exercising real SQL.
  await db.exec(`create role anon; create role authenticated;
    create schema auth;
    create table auth.users(id uuid primary key,email text,email_confirmed_at timestamptz,is_anonymous boolean);
    create function auth.jwt() returns jsonb language sql as $$
      select coalesce(nullif(current_setting('request.jwt.claims',true),''),'{}')::jsonb $$;
    create function auth.uid() returns uuid language sql as $$ select (auth.jwt()->>'sub')::uuid $$;
    insert into auth.users values
    ('${admin}','austin.g.meyer@gmail.com',now(),false),('${voter}',null,null,true),('${other}',null,null,true);`);
  const migration=await readFile(new URL('../supabase/poll-01.sql',import.meta.url),'utf8');
  await db.exec(migration);
  await db.exec(await readFile(new URL('../supabase/authorize-presenter.sql',import.meta.url),'utf8'));
  async function as(role,uid=null,isAnonymous=true){
    await db.exec('reset role');
    await db.query("select set_config('request.jwt.claims',$1,false)",[JSON.stringify(uid?{sub:uid,is_anonymous:isAnonymous}:{})]);
    await db.exec(`set role ${role}`);
  }
  async function call(name,args=[]){
    const placeholders=args.map((_,i)=>`$${i+1}`).join(',');
    return (await db.query(`select public.poll1_${name}(${placeholders}) as result`,args)).rows[0].result;
  }
  let session,second;
  try {
    await t.test('only allowlisted permanent users can manage sessions',async()=>{
      await as('authenticated',voter);
      assert.equal(await call('is_presenter'),false);
      await assert.rejects(call('create_session',['attack']),/Presenter access/);
      await assert.rejects(call('list_sessions'),/Presenter access/);
      await assert.rejects(db.query('select * from polling.responses'),/permission denied/);
      await as('authenticated',admin,true);
      assert.equal(await call('is_presenter'),false);
      await as('authenticated',admin,false);
      assert.equal(await call('is_presenter'),true);
      session=await call('create_session',['Test session']);
      assert.ok(isSession(session));
      await assert.rejects(call('create_session',['']),/check constraint/);
    });
    await t.test('public status hides counts and all unrevealed results',async()=>{
      await as('anon');
      assert.equal((await call('status',[session])).response_count,null);
      await assert.rejects(call('results',[session]),/not been revealed/);
      await assert.rejects(call('submit',[session,1,false]),/permission denied/);
      await assert.rejects(db.query('select * from polling.sessions'),/permission denied/);
      await assert.rejects(db.query('insert into polling.presenters values ($1)',[voter]),/permission denied/);
    });
    await t.test('votes before opening and premature reveal are rejected',async()=>{
      await as('authenticated',voter);
      await assert.rejects(call('submit',[session,1,false]),/not open/);
      await assert.rejects(call('transition',[session,'open']),/Presenter access/);
      await as('authenticated',admin,false);
      await assert.rejects(call('transition',[session,'reveal']),/Invalid poll transition/);
      assert.equal(await call('transition',[session,'open']),'open');
      assert.equal(await call('transition',[session,'open']),'open');
    });
    await t.test('every allowed week round trips, with one response per user',async()=>{
      await as('authenticated',voter);
      for(const week of WEEKS) assert.equal(await call('submit',[session,week,false]),true);
      await call('submit',[session,52,false]);
      await call('submit',[session,52,false]);
      await as('authenticated',admin,false);
      assert.equal((await call('status',[session])).response_count,1);
      await assert.rejects(call('results',[session]),/not been revealed/);
    });
    await t.test('invalid values cannot bypass the form',async()=>{
      await as('authenticated',voter);
      for(const [week,unsure] of [[0,false],[21,false],[43,false],[53,false],[null,false],[1,true],[1,null]])
        await assert.rejects(call('submit',[session,week,unsure]),/valid week/);
      await assert.rejects(call('submit',[session,1.5,false]),/invalid input syntax/);
      await assert.rejects(call('submit',['00000000-0000-4000-8000-999999999999',1,false]),/not found/);
      await as('authenticated',other);
      await call('submit',[session,null,true]);
      assert.equal((await call('status',[session])).response_count,null);
    });
    await t.test('closing freezes submissions, and reveal is a separate step',async()=>{
      await as('authenticated',admin,false);
      assert.equal(await call('transition',[session,'close']),'closed');
      assert.equal(await call('transition',[session,'close']),'closed');
      await assert.rejects(call('transition',[session,'open']),/Invalid poll transition/);
      await assert.rejects(call('results',[session]),/not been revealed/);
      await as('authenticated',voter);
      await assert.rejects(call('submit',[session,1,false]),/not open/);
      await as('authenticated',admin,false);
      await call('transition',[session,'reveal']);
    });
    await t.test('public results include zero bins, calendar rollover, and separate unsure count',async()=>{
      await as('anon');
      const result=normalizeResults(await call('results',[session]));
      assert.equal(result.numericCount,1);
      assert.equal(result.unsure,1);
      assert.equal(result.bins[8].count,1);
      assert.equal(result.bins[9].count,0);
      assert.equal((await call('status',[session])).response_count,2);
      assert.deepEqual(Object.keys(await call('results',[session])).sort(),['bins','unsure']);
    });
    await t.test('new sessions stay separate from old links and late votes',async()=>{
      await as('authenticated',admin,false);
      second=await call('create_session',['Second session']);
      assert.notEqual(session,second);
      assert.equal((await call('status',[second])).response_count,0);
      await call('transition',[second,'open']);
      await as('authenticated',voter);
      await assert.rejects(call('submit',[session,1,false]),/not open/);
      await call('submit',[second,1,false]);
      assert.equal(normalizeResults(await call('results',[session])).bins[8].count,1);
    });
    await t.test('reapplying setup preserves rows and restrictions',async()=>{
      await db.exec('reset role');await db.exec(migration);
      await as('authenticated',admin,false);
      assert.equal((await call('list_sessions')).length,2);
      assert.equal((await call('status',[second])).response_count,1);
      await as('anon');await assert.rejects(call('create_session',['attack']),/permission denied/);
      await assert.rejects(db.query('select * from polling.responses'),/permission denied/);
    });
  }finally{await db.close();}
});
