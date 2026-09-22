// Serve docs/ on 127.0.0.1:8765. All backend/CAPTCHA interactions are mocked.
import assert from 'node:assert/strict';
import {mkdtemp} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {POLLS,includesWeek} from '../docs/assets/polls-02-03/model.js';
const {chromium}=await import(process.env.POLL_PLAYWRIGHT?pathToFileURL(process.env.POLL_PLAYWRIGHT).href:'playwright');
const browser=await chromium.launch({channel:'chrome',headless:true});
const artifacts=await mkdtemp(join(tmpdir(),'polls-02-03-browser-'));
const errors=[];const observe=page=>page.on('pageerror',error=>errors.push(error.message));
const root='http://127.0.0.1:8765/';
try {
  for(const poll of Object.values(POLLS)) {
    const base=`${root}poll-0${poll.id}.html`,prefix=`poll-0${poll.id}`;
    let external=0;
    const previews=await browser.newContext({viewport:{width:1240,height:540}});
    await previews.route('**/*',route=>{
      if(!route.request().url().startsWith(root)){external++;return route.abort();}
      return route.continue();
    });
    for(const mode of ['question','results']) {
      const page=await previews.newPage();observe(page);await page.goto(`${base}?mode=${mode}&preview=1`);
      await page.waitForFunction(()=>document.querySelector('#state-badge').textContent!=='Connecting');
      assert.equal(await page.locator('#connection-message').textContent(),'');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),1240);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight),540);
      assert.doesNotMatch(await page.locator('body').innerText(),/52\s*(→|->)\s*1|within two weeks|Not reliably predictable/);
      if(mode==='question') {
        assert.equal(await page.locator('#qr svg').count(),1);
        assert.equal(await page.locator('#question-view h1').textContent(),poll.question);
        assert.ok((await page.locator('#vote-link').getAttribute('href')).includes(`${prefix}.html?mode=vote`));
        const bottom=await page.locator('#question-view').evaluate(el=>el.getBoundingClientRect().bottom);
        assert.ok(bottom<=540,`Poll ${poll.id} question clipped at ${bottom}`);
      } else {
        const bars=await page.locator('#histogram rect').evaluateAll(nodes=>nodes.map(el=>({x:+el.getAttribute('x'),y:+el.getAttribute('y'),width:+el.getAttribute('width'),height:+el.getAttribute('height')})));
        assert.equal(bars.length,poll.values.length);
        if(poll.id===2) {
          assert.equal(new Set(bars.map(b=>b.x)).size,1,'Horizontal bars share a left edge');
          assert.equal(new Set(bars.map(b=>b.y)).size,5,'Each option has its own row');
          assert.equal(new Set(bars.map(b=>b.height)).size,1);
        }
      }
      await page.screenshot({path:join(artifacts,`${prefix}-${mode}.png`)});await page.close();
    }
    const phone=await previews.newPage();observe(phone);await phone.setViewportSize({width:390,height:844});
    await phone.goto(`${base}?mode=vote&preview=1`);
    await phone.waitForFunction(()=>document.querySelector('#state-badge').textContent==='Voting open');
    assert.equal(await phone.locator('#submit-vote').isDisabled(),true);
    if(poll.id===2) {
      assert.equal(await phone.locator('input[type=range]').count(),0);
      assert.deepEqual(await phone.locator('[name=lead-weeks]').evaluateAll(nodes=>nodes.map(el=>el.value)),['0','1','2','3','4']);
      assert.equal(await phone.locator('[name=lead-weeks]:checked').count(),0);
      await phone.getByRole('radio',{name:'0 weeks',exact:true}).check();
      assert.equal(await phone.locator('#submit-vote').isDisabled(),false);
      await phone.getByRole('radio',{name:'4 weeks',exact:true}).check();
      assert.equal(await phone.locator('[name=lead-weeks]:checked').count(),1);
    } else {
      for(const width of [320,390,600,800,1000]) {
        await phone.setViewportSize({width,height:844});
        for(const id of ['week-ticks','end-week-ticks']) {
          assert.deepEqual(await phone.locator(`#${id} span`).allTextContents(),poll.values.map(String));
          const boxes=await phone.locator(`#${id} span`).evaluateAll(nodes=>nodes.map(el=>{
            const range=document.createRange();range.selectNodeContents(el);const r=range.getBoundingClientRect();
            return {left:r.left,right:r.right,top:r.top,bottom:r.bottom};
          }));
          for(let i=0;i<boxes.length;i++)for(const b of boxes.slice(i+1)) {
            const a=boxes[i];assert.ok(a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top,`Poll 3 labels overlap at ${width}`);
          }
        }
        assert.equal(await phone.evaluate(()=>document.documentElement.scrollWidth),width);
      }
      await phone.setViewportSize({width:390,height:844});
      await phone.locator('#week-slider').focus();await phone.keyboard.press('End');
      assert.equal(await phone.locator('#start-output').textContent(),'Week 52');
      assert.equal(await phone.locator('#submit-vote').isDisabled(),true,'Both endpoints need explicit selection');
      await phone.locator('#end-week-slider').focus();await phone.keyboard.press('Home');
      assert.equal(await phone.locator('#end-output').textContent(),'Week 1');
      assert.equal(await phone.locator('#window-note').isVisible(),true);
      assert.equal(await phone.locator('#submit-vote').isDisabled(),false);
      await phone.getByRole('radio',{name:'Not sure',exact:true}).check();
      assert.equal(await phone.locator('#week-slider').isDisabled(),true);
      await phone.getByRole('radio',{name:'Use my window',exact:true}).check();
    }
    await phone.locator('#submit-vote').click();
    assert.match(await phone.locator('#vote-message').textContent(),/Nothing was sent/);
    await phone.screenshot({path:join(artifacts,`${prefix}-phone.png`),fullPage:true});
    await previews.close();assert.equal(external,0,'Preview attempted an external request');

    const live=await browser.newContext({viewport:{width:390,height:844}});
    const id=`00000000-0000-4000-8000-00000000000${poll.id}`;
    const newId=`00000000-0000-4000-8000-00000000001${poll.id}`;
    const sessions=new Map([[id,{name:`Poll ${poll.id} rehearsal`,state:'open',answer:null}]]);
    const submitted=[],authRequests=[];let failNext=false;
    await live.route('https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit',route=>route.fulfill({contentType:'application/javascript',body:`
      window.turnstile={render(container,options){const b=document.createElement('button');b.type='button';b.textContent='Complete mock security check';b.onclick=()=>options.callback('synthetic-captcha-token');container.append(b);return 'mock';},reset(){}};`}));
    await live.route('https://iehrrxfxoldwzvauhpsm.supabase.co/**',async route=>{
      const url=new URL(route.request().url()),body=route.request().postDataJSON()||{};
      const send=(data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
      if(url.pathname.startsWith('/auth/v1/')) {
        authRequests.push(body);
        const anonymous=url.pathname.endsWith('/signup'),uid='00000000-0000-4000-8000-000000000099';
        const token=[{alg:'HS256',typ:'JWT'},{sub:uid,exp:Math.floor(Date.now()/1000)+3600,is_anonymous:anonymous,role:'authenticated'}].map(v=>Buffer.from(JSON.stringify(v)).toString('base64url')).join('.')+'.signature';
        return send({access_token:token,refresh_token:'synthetic-refresh',token_type:'bearer',expires_in:3600,user:{id:uid,aud:'authenticated',role:'authenticated',is_anonymous:anonymous}});
      }
      const name=url.pathname.split('/').at(-1);
      if(name==='poll1_is_presenter')return send(true);
      assert.ok(name.startsWith('poll23_'));assert.equal(body.p_poll,poll.id);
      if(name==='poll23_list_sessions')return send([...sessions].map(([key,s])=>({id:key,name:s.name,state:s.state,poll_number:poll.id})));
      if(name==='poll23_create_session'){sessions.set(newId,{name:body.p_name,state:'ready',answer:null});return send(newId);}
      const s=sessions.get(body.p_session);
      if(!s)return send({code:'P0002',message:'Poll session not found'},404);
      if(name==='poll23_status')return send({id:body.p_session,name:s.name,state:s.state,poll_number:poll.id,response_count:s.answer?1:0});
      if(name==='poll23_submit') {
        if(failNext){failNext=false;return route.abort();}
        if(s.state!=='open')return send({code:'42501',message:'Voting is not open'},403);
        submitted.push(body);s.answer={kind:body.p_kind,start:body.p_start,end:body.p_end};return send(true);
      }
      if(name==='poll23_transition'){s.state={open:'open',close:'closed',reveal:'revealed'}[body.p_action];return send(s.state);}
      if(name==='poll23_delete_session'){if(s.state==='open')return send({code:'42501',message:'Close voting before deleting'},403);sessions.delete(body.p_session);return send(true);}
      if(name==='poll23_results') {
        if(s.state!=='revealed')return send({code:'42501',message:'Results have not been revealed'},403);
        const a=s.answer,numeric=a?.kind===poll.kind?1:0;
        return send({bins:poll.values.map(value=>({value,count:numeric&&(poll.id===2?a.start===value:includesWeek(a.start,a.end,value))?1:0})),numeric_count:numeric,unsure:a?.kind==='not_sure'?1:0});
      }
      throw new Error(`Unexpected RPC ${name}`);
    });
    const vote=await live.newPage();observe(vote);await vote.goto(`${base}?mode=vote&session=${id}`);
    await vote.waitForFunction(()=>document.querySelector('#state-badge').textContent==='Voting open');
    if(poll.id===2)await vote.getByRole('radio',{name:'0 weeks',exact:true}).check();
    else {
      await vote.locator('#week-slider').focus();await vote.keyboard.press('End');
      await vote.locator('#end-week-slider').focus();await vote.keyboard.press('Home');
    }
    assert.equal(await vote.locator('#submit-vote').isDisabled(),true,'Selection cannot bypass CAPTCHA');
    await vote.getByRole('button',{name:'Complete mock security check'}).click();
    failNext=true;await vote.locator('#submit-vote').click();
    await vote.waitForFunction(()=>document.querySelector('#vote-message').textContent.includes('not confirmed'));
    await vote.locator('#submit-vote').click();
    await vote.waitForFunction(()=>document.querySelector('#vote-message').textContent==='Answer received. Thank you.');
    assert.deepEqual(submitted.at(-1),{p_poll:poll.id,p_session:id,p_kind:poll.kind,p_start:poll.id===2?0:52,p_end:poll.id===2?null:1});
    assert.equal(authRequests[0].gotrue_meta_security.captcha_token,'synthetic-captcha-token');
    const results=await live.newPage();observe(results);await results.setViewportSize({width:1240,height:540});
    await results.goto(`${base}?mode=results&session=${id}`);
    await results.waitForFunction(()=>document.querySelector('#state-badge').textContent==='Voting open');
    assert.equal(await results.locator('#histogram').isVisible(),false);
    const admin=await live.newPage();observe(admin);await admin.setViewportSize({width:1000,height:1000});
    await admin.goto(`${base}?mode=admin&session=${id}`);
    await admin.locator('#email').fill('presenter@example.test');await admin.locator('#password').fill('synthetic-only');
    await admin.getByRole('button',{name:'Complete mock security check'}).click();
    await admin.locator('#login-form button[type=submit]').click();await admin.waitForSelector('#admin-panel');
    assert.equal(await admin.locator('#delete-session').isDisabled(),true);
    admin.once('dialog',dialog=>dialog.accept());await admin.locator('[data-action=close]').click();
    await vote.waitForFunction(()=>document.querySelector('#state-badge').textContent==='Voting closed');
    assert.equal(await vote.locator('#submit-vote').isDisabled(),true);
    assert.equal(await results.locator('#histogram').isVisible(),false);
    admin.once('dialog',dialog=>dialog.accept());await admin.locator('[data-action=reveal]').click();
    await results.waitForSelector('#histogram svg');
    assert.equal(await results.locator('#histogram rect').count(),poll.values.length);
    assert.equal(await admin.locator('#audience-url').inputValue(),`${base}?mode=vote&session=${id}`);
    await admin.locator('#session-name').fill(`New poll ${poll.id}`);await admin.locator('#new-session-form button').click();
    await admin.waitForFunction(()=>document.querySelector('#admin-count').textContent==='0 responses');
    assert.equal(await admin.locator('#audience-url').inputValue(),`${base}?mode=vote&session=${newId}`);
    assert.ok(results.url().includes(id));
    await admin.screenshot({path:join(artifacts,`${prefix}-admin.png`),fullPage:true});
    admin.once('dialog',dialog=>dialog.dismiss());await admin.locator('#delete-session').click();
    assert.ok(sessions.has(newId));
    await admin.waitForFunction(()=>!document.querySelector('#delete-session').disabled);
    admin.once('dialog',dialog=>dialog.accept());await admin.locator('#delete-session').click();
    await admin.waitForFunction(()=>document.querySelector('#admin-count').textContent.startsWith('Session deleted.'));
    assert.equal(sessions.has(newId),false);assert.ok(sessions.has(id));
    await live.close();
  }
  assert.deepEqual(errors,[]);
  console.log('PASS: both question/results frames, Poll 2 exact radios and horizontal bars, Poll 3 two-endpoint selection and all week ticks, mobile layout, no preview writes, CAPTCHA forwarding, failed submission retry, close/reveal, scoped presenter links, new sessions and confirmed deletion.');
  console.log(`Screenshots: ${artifacts}`);
}finally{await browser.close();}
