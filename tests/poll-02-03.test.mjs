import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {PGlite} from '@electric-sql/pglite';
import {POLLS,validAnswer,includesWeek,normalizeResults,previewResults} from '../docs/assets/polls-02-03/model.js';

test('Poll 2 has exactly five choices and no default or alternative answer',()=>{
  const poll=POLLS[2];assert.deepEqual(poll.values,[0,1,2,3,4]);
  assert.equal(poll.question,'How far in advance can we accurately predict the inflection at the peak with quantitative forecasts?');
  for(const start of poll.values)assert.equal(validAnswer(poll,{kind:'weeks',start,end:null}),true);
  for(const start of [null,-1,5,26,1.5,'1'])assert.equal(validAnswer(poll,{kind:'weeks',start,end:null}),false);
  for(const kind of ['not_sure','not_predictable','window'])assert.equal(validAnswer(poll,{kind,start:null,end:null}),false);
  assert.equal(validAnswer(poll,{kind:'weeks',start:1,end:2}),false);
  assert.equal(normalizeResults(poll,previewResults(poll)).numericCount,11);
});
test('Poll 3 validates both endpoints and includes year-crossing windows',()=>{
  const poll=POLLS[3];assert.deepEqual(poll.values,Array.from({length:52},(_,i)=>i+1));
  for(const [start,end] of [[1,52],[50,3],[10,10]])assert.equal(validAnswer(poll,{kind:'window',start,end}),true);
  for(const [start,end] of [[null,1],[1,null],[0,2],[2,53],[1.5,2]])assert.equal(validAnswer(poll,{kind:'window',start,end}),false);
  assert.equal(validAnswer(poll,{kind:'not_sure',start:null,end:null}),true);
  assert.equal(validAnswer(poll,{kind:'not_sure',start:1,end:2}),false);
  assert.deepEqual(poll.values.filter(w=>includesWeek(50,3,w)),[1,2,3,50,51,52]);
  assert.deepEqual(poll.values.filter(w=>includesWeek(10,10,w)),[10]);
  assert.equal(poll.values.filter(w=>includesWeek(1,52,w)).length,52);
});
test('results distinguish response counts from weekly window coverage',()=>{
  for(const poll of Object.values(POLLS)) {
    const data=previewResults(poll);const result=normalizeResults(poll,data);
    assert.equal(result.bins.length,poll.values.length);
    assert.throws(()=>normalizeResults(poll,{...data,bins:[...data.bins].reverse()}));
    assert.throws(()=>normalizeResults(poll,{...data,numeric_count:0}));
    assert.throws(()=>normalizeResults(poll,{...data,unsure:-1}));
  }
  const windowData=previewResults(POLLS[3]);
  assert.ok(windowData.bins.reduce((sum,b)=>sum+b.count,0)>windowData.numeric_count);
  assert.throws(()=>normalizeResults(POLLS[2],{...previewResults(POLLS[2]),unsure:1}));
});

test('Polls 2 and 3 database isolation and lifecycle',async t=>{
  const db=new PGlite();
  const ids=Array.from({length:5},(_,i)=>`00000000-0000-4000-8000-${String(i+1).padStart(12,'0')}`);
  const [admin,voter,other,third,fourth]=ids;
  await db.exec(`create role anon; create role authenticated;
    create schema auth;
    create table auth.users(id uuid primary key,email text,email_confirmed_at timestamptz,is_anonymous boolean);
    create function auth.jwt() returns jsonb language sql as $$ select coalesce(nullif(current_setting('request.jwt.claims',true),''),'{}')::jsonb $$;
    create function auth.uid() returns uuid language sql as $$ select (auth.jwt()->>'sub')::uuid $$;`);
  for(const id of ids)await db.query('insert into auth.users values($1,$2,now(),$3)',[id,id===admin?'austin.g.meyer@gmail.com':null,id!==admin]);
  const sql=async name=>readFile(new URL(`../supabase/${name}`,import.meta.url),'utf8');
  await db.exec(await sql('poll-01.sql'));await db.exec(await sql('authorize-presenter.sql'));
  async function as(role,uid=null,isAnonymous=true) {
    await db.exec('reset role');
    await db.query("select set_config('request.jwt.claims',$1,false)",[JSON.stringify(uid?{sub:uid,is_anonymous:isAnonymous}:{})]);
    await db.exec(`set role ${role}`);
  }
  async function call(poll,name,args=[]) {
    const values=[poll,...args];
    return (await db.query(`select public.poll23_${name}(${values.map((_,i)=>`$${i+1}`).join(',')}) as result`,values)).rows[0].result;
  }
  await as('authenticated',admin,false);
  const legacy=(await db.query("select public.poll1_create_session('Existing Poll 1') as id")).rows[0].id;
  await db.query("select public.poll1_transition($1,'open')",[legacy]);
  await as('authenticated',voter);await db.query('select public.poll1_submit($1,1,false)',[legacy]);
  await db.exec('reset role');const migration=await sql('polls-02-03.sql');await db.exec(migration);
  let s2,s3;
  try {
    await t.test('existing presenter authorization is reused and Poll 1 remains intact',async()=>{
      await as('authenticated',admin,false);
      assert.equal((await db.query('select public.poll1_status($1) as s',[legacy])).rows[0].s.response_count,1);
      s2=await call(2,'create_session',['Forecast rehearsal']);s3=await call(3,'create_session',['Vaccination rehearsal']);
      assert.deepEqual((await call(2,'list_sessions')).map(s=>s.id),[s2]);
      assert.deepEqual((await call(3,'list_sessions')).map(s=>s.id),[s3]);
      await assert.rejects(call(1,'create_session',['wrong poll']),/Unknown poll/);
    });
    await t.test('anonymous and non-presenter users cannot manage sessions or read raw tables',async()=>{
      await as('anon');await assert.rejects(call(2,'create_session',['attack']),/permission denied/);
      await assert.rejects(call(2,'submit',[s2,'weeks',0,null]),/permission denied/);
      for(const [uid,anonymous] of [[voter,true],[other,false],[admin,true]]) {
        await as('authenticated',uid,anonymous);
        for(const poll of [2,3]) {
          const id=poll===2?s2:s3;
          await assert.rejects(call(poll,'create_session',['attack']),/Presenter access/);
          await assert.rejects(call(poll,'list_sessions'),/Presenter access/);
          await assert.rejects(call(poll,'transition',[id,'open']),/Presenter access/);
          await assert.rejects(call(poll,'delete_session',[id]),/Presenter access/);
        }
        for(const table of ['section_sessions','section_responses'])await assert.rejects(db.query(`select * from polling.${table}`),/permission denied/);
      }
    });
    await t.test('session IDs cannot be reused across poll questions',async()=>{
      await as('authenticated',admin,false);
      await assert.rejects(call(2,'status',[s3]),/not found/);
      await assert.rejects(call(3,'status',[s2]),/not found/);
      await assert.rejects(call(2,'transition',[s3,'open']),/not found/);
      await assert.rejects(call(2,'submit',[s3,'weeks',2,null]),/not found/);
      await assert.rejects(call(3,'results',[s2]),/not found/);
      await assert.rejects(call(2,'status',[legacy]),/not found/);
      assert.equal(await call(2,'delete_session',[s3]),true);
      assert.equal((await call(3,'list_sessions')).length,1);
    });
    await t.test('counts and results stay hidden until reveal; voting requires open state',async()=>{
      await as('anon');assert.equal((await call(2,'status',[s2])).response_count,null);
      for(const [poll,id] of [[2,s2],[3,s3]])await assert.rejects(call(poll,'results',[id]),/not been revealed/);
      await as('authenticated',voter);await assert.rejects(call(2,'submit',[s2,'weeks',1,null]),/not open/);
      await as('authenticated',admin,false);
      for(const [poll,id] of [[2,s2],[3,s3]]) {
        await assert.rejects(call(poll,'transition',[id,'reveal']),/Invalid poll transition/);
        await call(poll,'transition',[id,'open']);
        await assert.rejects(call(poll,'delete_session',[id]),/Close voting/);
      }
    });
    await t.test('all five forecast choices round trip and repeated votes replace, not add',async()=>{
      await as('authenticated',voter);
      for(const week of POLLS[2].values)assert.equal(await call(2,'submit',[s2,'weeks',week,null]),true);
      await call(2,'submit',[s2,'weeks',4,null]);
      await as('authenticated',other);await call(2,'submit',[s2,'weeks',0,null]);
      await as('authenticated',admin,false);assert.equal((await call(2,'status',[s2])).response_count,2);
    });
    await t.test('invalid answer types and bounds are rejected in the database',async()=>{
      await as('authenticated',voter);
      for(const args of [['weeks',-1,null],['weeks',5,null],['weeks',null,null],['weeks',1,2],['not_sure',null,null],['not_predictable',null,null],[null,1,null]])
        await assert.rejects(call(2,'submit',[s2,...args]),/valid response/);
      await assert.rejects(call(2,'submit',[s2,'weeks',1.5,null]),/invalid input syntax/);
      for(const args of [['window',0,1],['window',1,53],['window',1,null],['window',null,1],['not_sure',1,2],['weeks',1,null]])
        await assert.rejects(call(3,'submit',[s3,...args]),/valid response/);
    });
    await t.test('vaccination windows include full-year, single-week, and year-crossing responses',async()=>{
      for(const [id,start,end] of [[voter,50,3],[other,10,10],[third,1,52]]) {
        await as('authenticated',id);await call(3,'submit',[s3,'window',start,end]);
      }
      await as('authenticated',fourth);await call(3,'submit',[s3,'not_sure',null,null]);
      await call(3,'submit',[s3,'not_sure',null,null]);
      await as('authenticated',admin,false);assert.equal((await call(3,'status',[s3])).response_count,4);
    });
    await t.test('closing freezes answers, and revealed counts have the correct denominators',async()=>{
      for(const [poll,id] of [[2,s2],[3,s3]]) {
        await as('authenticated',admin,false);await call(poll,'transition',[id,'close']);
        await assert.rejects(call(poll,'results',[id]),/not been revealed/);
        await as('authenticated',voter);
        await assert.rejects(call(poll,'submit',[id,poll===2?'weeks':'window',1,poll===2?null:2]),/not open/);
        await as('authenticated',admin,false);await call(poll,'transition',[id,'reveal']);
      }
      await as('anon');const r2=normalizeResults(POLLS[2],await call(2,'results',[s2]));
      assert.deepEqual(r2.bins.map(b=>b.count),[1,0,0,0,1]);assert.equal(r2.numericCount,2);assert.equal(r2.unsure,0);
      const r3=normalizeResults(POLLS[3],await call(3,'results',[s3]));
      assert.equal(r3.numericCount,3);assert.equal(r3.unsure,1);
      assert.equal(r3.bins.reduce((sum,b)=>sum+b.count,0),59);
      for(const week of [1,3,10,50,52])assert.equal(r3.bins[week-1].count,2);
      assert.equal(r3.bins[3].count,1);
    });
    await t.test('rerunning the migration preserves all three polls',async()=>{
      await db.exec('reset role');await db.exec(migration);await as('authenticated',admin,false);
      assert.equal((await call(2,'status',[s2])).response_count,2);assert.equal((await call(3,'status',[s3])).response_count,4);
      assert.equal((await db.query('select public.poll1_status($1) as s',[legacy])).rows[0].s.response_count,1);
      await as('anon');await assert.rejects(call(2,'delete_session',[s2]),/permission denied/);
    });
    await t.test('deletion is isolated and retry-safe without affecting Poll 1 or user accounts',async()=>{
      await as('authenticated',admin,false);await call(2,'delete_session',[s2]);await call(2,'delete_session',[s2]);
      assert.deepEqual(await call(2,'list_sessions'),[]);assert.equal((await call(3,'status',[s3])).response_count,4);
      const unused=await call(2,'create_session',['Unused']);await call(2,'delete_session',[unused]);
      await call(3,'delete_session',[s3]);
      assert.equal((await db.query('select public.poll1_status($1) as s',[legacy])).rows[0].s.response_count,1);
      await db.exec('reset role');
      assert.equal((await db.query('select count(*)::int as n from polling.section_responses')).rows[0].n,0);
      assert.equal((await db.query('select count(*)::int as n from auth.users')).rows[0].n,5);
    });
  }finally{await db.close();}
});
