import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {PGlite} from '@electric-sql/pglite';
import {callPoll} from '../docs/assets/polls/backend.js';

const admin='00000000-0000-4000-8000-000000000001';
const voter='00000000-0000-4000-8000-000000000002';
const other='00000000-0000-4000-8000-000000000003';
const sql=await readFile(new URL('../supabase/polls.sql',import.meta.url),'utf8');
const fixture=async name=>readFile(new URL(`./fixtures/legacy-${name}.sql`,import.meta.url),'utf8');
async function database() {
  const db=new PGlite();
  await db.exec(`create role anon;create role authenticated;create schema auth;
    create table auth.users(id uuid primary key,email text,email_confirmed_at timestamptz,is_anonymous boolean);
    create function auth.jwt() returns jsonb language sql as $$ select coalesce(nullif(current_setting('request.jwt.claims',true),''),'{}')::jsonb $$;
    create function auth.uid() returns uuid language sql as $$ select (auth.jwt()->>'sub')::uuid $$;
    insert into auth.users values
      ('${admin}','austin.g.meyer@gmail.com',now(),false),('${voter}',null,null,true),('${other}',null,null,true);`);
  async function as(uid=null,anonymous=true) {
    await db.exec('reset role');
    await db.query("select set_config('request.jwt.claims',$1,false)",[JSON.stringify(uid?{sub:uid,is_anonymous:anonymous}:{})]);
    await db.exec(`set role ${uid?'authenticated':'anon'}`);
  }
  async function call(name,args=[]) {
    return (await db.query(`select public.${name}(${args.map((_,i)=>`$${i+1}`).join(',')}) as result`,args)).rows[0].result;
  }
  // Execute the shared frontend connector against actual SQL, not a mock result.
  const client={rpc(name,args){return {abortSignal:async()=>{
    try{return {data:await call(name,Object.values(args)),error:null};}
    catch(error){return {data:null,error:{code:error.code==='42883'?'PGRST202':error.code,message:error.message}};}
  }};}};
  return {db,as,call,client};
}

for(const installation of ['fresh','poll1','all'])test(`unified setup: ${installation}`,async t=>{
  const {db,as,call,client}=await database();
  const oldSessions=[];
  let beforeSessions=[],beforeResponses=[];
  try {
    if(installation!=='fresh') {
      await db.exec(await fixture('poll-01'));
      await db.exec(await readFile(new URL('../supabase/authorize-presenter.sql',import.meta.url),'utf8'));
      if(installation==='all')await db.exec(await fixture('polls-02-03'));
      for(const poll of installation==='all'?[1,2,3]:[1]) {
        await as(admin,false);
        const id=await callPoll(client,poll,'create_session',{p_name:`Existing poll ${poll}`});
        oldSessions.push({poll,id});
        await callPoll(client,poll,'transition',{p_session:id,p_action:'open'});
        await as(voter);
        await callPoll(client,poll,'submit',{p_session:id,p_kind:poll===1?'week':poll===2?'weeks':'window',p_start:poll===1?52:poll===2?0:50,p_end:poll===3?3:null});
        await as(other);
        await callPoll(client,poll,'submit',{p_session:id,p_kind:poll===2?'weeks':'not_sure',p_start:poll===2?4:null,p_end:null});
        await as(admin,false);
        if(poll!==3)await callPoll(client,poll,'transition',{p_session:id,p_action:'close'});
        if(poll===1)await callPoll(client,poll,'transition',{p_session:id,p_action:'reveal'});
      }
      await db.exec('reset role');
      beforeSessions=(await db.query('select id,1 as poll_number,name,state,created_by,created_at from polling.sessions')).rows;
      beforeResponses=(await db.query("select session_id,1 as poll_number,user_id,case when unsure then 'not_sure' else 'week' end as answer_kind,week as value_start,null::integer as value_end,submitted_at from polling.responses")).rows;
      if(installation==='all') {
        beforeSessions.push(...(await db.query('select * from polling.section_sessions')).rows);
        beforeResponses.push(...(await db.query('select * from polling.section_responses')).rows);
      }
    }
    await db.exec(sql);
    if(installation==='fresh')await db.exec(await readFile(new URL('../supabase/authorize-presenter.sql',import.meta.url),'utf8'));
    const ordered=rows=>rows.toSorted((a,b)=>JSON.stringify([a.poll_number,a.session_id||a.id,a.user_id]).localeCompare(JSON.stringify([b.poll_number,b.session_id||b.id,b.user_id])));
    await t.test('migration preserves every ID, state, answer, presenter and timestamp',async()=>{
      assert.deepEqual(ordered((await db.query('select * from polling.sessions')).rows),ordered(beforeSessions));
      assert.deepEqual(ordered((await db.query('select * from polling.responses')).rows),ordered(beforeResponses));
      assert.deepEqual((await db.query('select user_id from polling.presenters')).rows,[{user_id:admin}]);
      assert.equal((await db.query("select to_regclass('polling.section_sessions') as old")).rows[0].old,null);
      assert.equal((await db.query('select count(*)::int as n from polling.schema_migrations')).rows[0].n,1);
      for(const {poll,id} of oldSessions) {
        await as(admin,false);
        const status=await callPoll(client,poll,'status',{p_session:id});
        assert.equal(status.response_count,2);
        assert.equal(status.state,poll===1?'revealed':poll===2?'closed':'open');
      }
    });
    await t.test('one API isolates all three polls and shares storage with cached-page adapters',async()=>{
      const created=[];
      for(const poll of [1,2,3]) {
        await as(admin,false);
        const id=await call('poll_create_session',[poll,`New poll ${poll}`]);created.push({poll,id});
        await call('poll_transition',[poll,id,'open']);
        await as(voter);
        const kind=poll===1?'week':poll===2?'weeks':'window';
        await call('poll_submit',[poll,id,kind,poll===1?1:poll===2?0:50,poll===3?3:null]);
        // A cached old page replaces this same row, not a second copy.
        if(poll===1)await call('poll1_submit',[id,52,false]);
        else await call('poll23_submit',[poll,id,kind,poll===2?4:51,poll===3?2:null]);
        await assert.rejects(call('poll_submit',[poll,id,null,1,null]),/valid response/);
        await assert.rejects(call('poll_submit',[poll,id,kind,null,null]),/valid response/);
        if(poll===1)for(const start of [0,21,43,53])await assert.rejects(call('poll_submit',[poll,id,'week',start,null]),/valid response/);
        for(const wrong of [1,2,3].filter(x=>x!==poll)) {
          await assert.rejects(call('poll_status',[wrong,id]),/not found/);
          await assert.rejects(call('poll_submit',[wrong,id,kind,1,null]),/not found/);
          await as(admin,false);
          assert.equal(await call('poll_delete_session',[wrong,id]),true);
          await assert.rejects(call('poll_transition',[wrong,id,'close']),/not found/);
          await as(voter);
        }
        await as(admin,false);
        assert.equal((await call('poll_status',[poll,id])).response_count,1);
        await call('poll_transition',[poll,id,'close']);await call('poll_transition',[poll,id,'reveal']);
        await as();
        const result=await call('poll_results',[poll,id]);
        assert.equal(result.numeric_count,1);
        assert.equal(result.bins.length,poll===1?29:poll===2?5:52);
        if(poll===1)assert.deepEqual((await call('poll1_results',[id])).bins,result.bins.map(b=>({week:b.value,count:b.count})));
        else assert.deepEqual(await call('poll23_results',[poll,id]),result);
        await assert.rejects(call('poll_results',[poll===1?2:1,id]),/not found/);
      }
      await db.exec('reset role');
      assert.equal((await db.query('select count(*)::int as n from polling.responses')).rows[0].n,beforeResponses.length+3);
      for(const {poll,id} of created) {await as(admin,false);await call('poll_delete_session',[poll,id]);}
    });
    await t.test('core and compatibility APIs enforce permissions; archived records stay private',async()=>{
      for(const [uid,anonymous] of [[null,true],[voter,true],[other,false],[admin,true]]) {
        await as(uid,anonymous);
        for(const poll of [1,2,3]) {
          for(const [name,args] of [['create_session',[poll,'attack']],['list_sessions',[poll]],['transition',[poll,admin,'open']],['delete_session',[poll,admin]]])
            await assert.rejects(call(`poll_${name}`,args),/permission denied|Presenter access/);
        }
        for(const table of ['polling.sessions','polling.responses','polling.presenters','polling.schema_migrations'])
          await assert.rejects(db.query(`select * from ${table}`),/permission denied/);
        if(installation!=='fresh')await assert.rejects(db.query('select * from polling_archive.responses'),/permission denied/);
      }
      await db.exec('reset role');
      const adapters=(await db.query("select proname,prosecdef,prosrc from pg_proc where pronamespace='public'::regnamespace and (proname like 'poll1_%' or proname like 'poll23_%')")).rows;
      assert.equal(adapters.length,15);
      for(const f of adapters) {assert.equal(f.prosecdef,false);assert.doesNotMatch(f.prosrc,/polling_archive|polling\.responses|polling\.sessions/);}
    });
    await t.test('rerunning setup does not restore deleted sessions or overwrite newer answers',async()=>{
      for(const {poll,id} of oldSessions) {
        if(poll===3){await as(voter);await call('poll_submit',[3,id,'window',40,45]);}
        if(poll===1){await as(admin,false);await call('poll_delete_session',[1,id]);}
      }
      await db.exec('reset role');
      const sessions=ordered((await db.query('select * from polling.sessions')).rows);
      const responses=ordered((await db.query('select * from polling.responses')).rows);
      await db.exec(sql);
      assert.deepEqual(ordered((await db.query('select * from polling.sessions')).rows),sessions);
      assert.deepEqual(ordered((await db.query('select * from polling.responses')).rows),responses);
      if(installation!=='fresh')assert.equal((await db.query('select count(*)::int as n from polling_archive.responses')).rows[0].n,2);
    });
  }finally{await db.close();}
});

test('a migration conflict rolls back without changing either legacy backend',async()=>{
  const {db,as,call}=await database();
  try {
    await db.exec(await fixture('poll-01'));await db.exec(await fixture('polls-02-03'));
    await db.exec(await readFile(new URL('../supabase/authorize-presenter.sql',import.meta.url),'utf8'));
    await as(admin,false);
    const id=await call('poll1_create_session',['Existing Poll 1']);
    await db.exec('reset role');
    await db.query("insert into polling.section_sessions(id,poll_number,name,created_by) values($1,2,'UUID conflict',$2)",[id,admin]);
    await assert.rejects(db.exec(sql),/duplicate key/);await db.exec('rollback');
    assert.equal((await db.query('select count(*)::int as n from polling.sessions')).rows[0].n,1);
    assert.equal((await db.query('select count(*)::int as n from polling.section_sessions')).rows[0].n,1);
    assert.equal((await db.query("select to_regclass('polling_archive.sessions') as archive")).rows[0].archive,null);
    await as(admin,false);
    assert.equal((await call('poll1_status',[id])).name,'Existing Poll 1');
    assert.equal((await call('poll23_status',[2,id])).name,'UUID conflict');
  }finally{await db.close();}
});

test('shared connector falls back only for missing functions, then prefers the unified API',async()=>{
  const calls=[];let installed=false,failure=null;
  const client={rpc(name,args){calls.push({name,args});return {abortSignal:async()=>{
    if(failure)return {error:failure};
    if(name.startsWith('poll_')&&!installed)return {error:{code:'PGRST202'}};
    return {data:true,error:null};
  }};}};
  for(const poll of [1,2,3]) {
    calls.length=0;
    await callPoll(client,poll,'submit',{p_session:'test',p_kind:poll===1?'week':poll===2?'weeks':'window',p_start:poll===2?0:1,p_end:poll===3?2:null});
    assert.deepEqual(calls.map(c=>c.name),['poll_submit',poll===1?'poll1_submit':'poll23_submit']);
    if(poll===1)assert.deepEqual(calls[1].args,{p_session:'test',p_week:1,p_unsure:false});
    else assert.equal(calls[1].args.p_poll,poll);
  }
  installed=true;calls.length=0;await callPoll(client,1,'status',{p_session:'test'});
  assert.deepEqual(calls.map(c=>c.name),['poll_status']);
  for(const code of ['42501','22023','P0002','NETWORK_ERROR']) {
    failure={code,message:'Rejected'};calls.length=0;
    await assert.rejects(callPoll(client,2,'submit',{p_session:'test'}),error=>error===failure);
    assert.equal(calls.length,1,'Never replay failed writes through a different API');
  }
});
