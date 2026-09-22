// Serve docs/ on localhost:8765 first. Point POLL_PLAYWRIGHT to an installed
// Playwright package if it is not resolvable from this repository.
import assert from 'node:assert/strict';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { WEEKS } from '../docs/assets/poll-01/model.js';
import { config } from '../docs/assets/poll-01/config.js';
const {chromium}=await import(process.env.POLL_PLAYWRIGHT?pathToFileURL(process.env.POLL_PLAYWRIGHT).href:'playwright');
const browser=await chromium.launch({channel:'chrome',headless:true});
const artifacts=await mkdtemp(join(tmpdir(),'poll-01-browser-'));
const base='http://127.0.0.1:8765/poll-01.html';
const errors=[];
const observe=page=>page.on('pageerror',error=>errors.push(error.message));
let blockedExternalRequests=0;
try {
  // Previews must not contact Supabase or create real anonymous users.
  const previews=await browser.newContext({viewport:{width:1240,height:540}});
  await previews.route('**/*',async route=>{
    if(!route.request().url().startsWith('http://127.0.0.1:8765/')){
      blockedExternalRequests++;return route.abort();
    }
    return route.continue();
  });
  for(const mode of ['question','results']) {
    const page=await previews.newPage();observe(page);
    await page.goto(`${base}?mode=${mode}&preview=1`);
    await page.waitForFunction(()=>document.querySelector('#state-badge').textContent!=='Connecting');
    assert.equal(await page.locator('#connection-message').textContent(),'');
    assert.doesNotMatch(await page.locator('body').innerText(),/52\s*(→|->)\s*1/);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),1240);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight),540);
    if(mode==='question')assert.equal(await page.locator('#qr svg').count(),1);
    else assert.equal(await page.locator('#histogram rect').count(),29);
    await page.screenshot({path:join(artifacts,`${mode}.png`)});
    await page.close();
  }
  const phone=await previews.newPage();observe(phone);await phone.setViewportSize({width:390,height:844});
  await phone.goto(`${base}?mode=vote&preview=1`);
  await phone.waitForFunction(()=>document.querySelector('#state-badge').textContent==='Voting open');
  assert.equal(await phone.locator('#submit-vote').isDisabled(),true);
  assert.doesNotMatch(await phone.locator('body').innerText(),/52\s*(→|->)\s*1/);
  assert.equal(await phone.locator('#choose-week').count(),0);
  assert.deepEqual(await phone.locator('#week-ticks span').allTextContents(),WEEKS.map(String));
  for(const width of [320,390,1000]) {
    await phone.setViewportSize({width,height:844});
    const tickLayout=await phone.locator('#week-ticks span').evaluateAll(ticks=>ticks.map(tick=>{
      const range=document.createRange();range.selectNodeContents(tick);
      const box=range.getBoundingClientRect();
      return {left:box.left,right:box.right,top:box.top,bottom:box.bottom,tickHeight:parseFloat(getComputedStyle(tick,'::before').height)};
    }));
    for(let i=0;i<tickLayout.length;i++) {
      const a=tickLayout[i];
      assert.ok(a.left>=0&&a.right<=width&&a.tickHeight>0,`Visible tick and number at width ${width}`);
      for(const b of tickLayout.slice(i+1))
        assert.ok(a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top,`Week labels overlap at width ${width}`);
    }
  }
  await phone.setViewportSize({width:390,height:844});
  // Tapping the initial thumb explicitly selects week 6 without another button.
  await phone.locator('#week-slider').click();
  assert.equal(await phone.locator('#week-output').textContent(),'Week 6');
  assert.equal(await phone.locator('#submit-vote').isDisabled(),false);
  const sliderBox=await phone.locator('#week-slider').boundingBox();
  await phone.mouse.move(sliderBox.x+sliderBox.width/2,sliderBox.y+sliderBox.height/2);
  await phone.mouse.down();
  await phone.mouse.move(sliderBox.x+sliderBox.width-12,sliderBox.y+sliderBox.height/2,{steps:12});
  await phone.mouse.up();
  assert.equal(await phone.locator('#week-output').textContent(),'Week 20');
  await phone.locator('#week-slider').focus();await phone.keyboard.press('Home');
  assert.equal(await phone.locator('#week-output').textContent(),'Week 44');
  await phone.locator('#week-slider').evaluate(el=>{el.value='8';el.dispatchEvent(new Event('input',{bubbles:true}));});
  await phone.keyboard.press('ArrowRight');
  assert.equal(await phone.locator('#week-output').textContent(),'Week 1');
  assert.equal(await phone.locator('#week-slider').getAttribute('aria-valuetext'),'Week 1');
  await phone.locator('#submit-vote').click();
  await phone.waitForFunction(()=>document.querySelector('#vote-message').textContent.includes('Nothing was sent'));
  await phone.screenshot({path:join(artifacts,'phone.png'),fullPage:true});
  await phone.locator('#unsure').check();
  assert.equal(await phone.locator('#week-slider').isDisabled(),true);
  assert.equal(await phone.locator('#week-output').textContent(),'Not sure');
  assert.equal(await phone.evaluate(()=>document.documentElement.scrollWidth),390);
  await previews.close();
  assert.equal(blockedExternalRequests,0,'Preview unexpectedly attempted an external request');

  // Exercise the live frontend against a deterministic mocked API. SQL security
  // is tested separately against PostgreSQL; these are not production requests.
  let sessionState='open',submissions=0,failNext=false;
  const session='00000000-0000-4000-8000-000000000009';
  const second='00000000-0000-4000-8000-000000000010';
  const received=[];
  const authRequests=[];
  const deletedSessions=new Set(),deletionRequests=[];
  let deletionAvailable=true;
  const authBody=anonymous=>{
    const id=anonymous?'00000000-0000-4000-8000-000000000002':'00000000-0000-4000-8000-000000000001';
    const payload={sub:id,exp:Math.floor(Date.now()/1000)+3600,is_anonymous:anonymous,role:'authenticated'};
    const access=[{alg:'HS256',typ:'JWT'},payload].map(v=>Buffer.from(JSON.stringify(v)).toString('base64url')).join('.')+'.signature';
    return {access_token:access,refresh_token:'test-refresh',token_type:'bearer',expires_in:3600,user:{id,aud:'authenticated',role:'authenticated',is_anonymous:anonymous,email:anonymous?'':'presenter@example.test'}};
  };
  const live=await browser.newContext({viewport:{width:390,height:844}});
  // Test the integration with a mock widget, never an automated CAPTCHA solve.
  await live.route('https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit',route=>route.fulfill({
    contentType:'application/javascript',body:`
      window.turnstile={
        render(container,options){
          window.testCaptchaOptions=options;
          const button=document.createElement('button');
          button.type='button';button.textContent='Complete mock security check';
          button.onclick=()=>options.callback('synthetic-captcha-token');
          container.append(button);return 'test-widget';
        },
        reset(){}
      };`,
  }));
  await live.route('https://iehrrxfxoldwzvauhpsm.supabase.co/**',async route=>{
    const url=new URL(route.request().url());
    const body=route.request().postDataJSON()||{};
    const send=(data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
    if(url.pathname.startsWith('/auth/v1/')){
      authRequests.push({path:url.pathname,body});
      return send(authBody(url.pathname.endsWith('/signup')));
    }
    const name=url.pathname.split('/').at(-1);
    if(deletedSessions.has(body.p_session)&&['poll1_status','poll1_results'].includes(name))return send({message:'Poll session not found',code:'P0002'},404);
    if(name==='poll1_status')return send({id:body.p_session,name:body.p_session===second?'New session':'Rehearsal',state:body.p_session===second?'ready':sessionState,response_count:body.p_session===second?0:submissions});
    if(name==='poll1_submit') {
      if(failNext){failNext=false;return route.abort();}
      if(sessionState!=='open')return send({message:'Voting is not open',code:'42501'},403);
      received.push(body);submissions=1;return send(true);
    }
    if(name==='poll1_results')return sessionState==='revealed'?send({bins:WEEKS.map(week=>({week,count:week===1?1:0})),unsure:0}):send({message:'Results have not been revealed'},403);
    if(name==='poll1_is_presenter')return send(true);
    if(name==='poll1_list_sessions')return send([{id:session,name:'Rehearsal',state:sessionState},{id:second,name:'New session',state:'ready'}].filter(s=>!deletedSessions.has(s.id)));
    if(name==='poll1_create_session')return send(second);
    if(name==='poll1_transition'){sessionState={open:'open',close:'closed',reveal:'revealed'}[body.p_action];return send(sessionState);}
    if(name==='poll1_delete_session'){
      if(!deletionAvailable)return send({code:'PGRST202',message:'Function not found'},404);
      if(body.p_session===session&&sessionState==='open')return send({code:'42501',message:'Close voting before deleting this session'},403);
      deletionRequests.push(body.p_session);deletedSessions.add(body.p_session);return send(true);
    }
    throw new Error(`Unexpected request: ${url}`);
  });
  const vote=await live.newPage();observe(vote);await vote.goto(`${base}?mode=vote&session=${session}`);
  await vote.waitForFunction(()=>document.querySelector('#state-badge').textContent==='Voting open');
  assert.equal(await vote.locator('#submit-vote').isDisabled(),true);
  await vote.locator('#week-slider').evaluate(el=>{el.value='9';el.dispatchEvent(new Event('input',{bubbles:true}));});
  assert.equal(await vote.locator('#submit-vote').isDisabled(),true,'A week alone cannot bypass CAPTCHA');
  assert.equal(await vote.evaluate(()=>window.testCaptchaOptions.sitekey),config.turnstileSiteKey);
  await vote.getByRole('button',{name:'Complete mock security check'}).click();
  assert.equal(await vote.locator('#submit-vote').isDisabled(),false);
  await vote.evaluate(()=>window.testCaptchaOptions['expired-callback']());
  assert.equal(await vote.locator('#submit-vote').isDisabled(),true,'Expired CAPTCHA must disable submission');
  await vote.getByRole('button',{name:'Complete mock security check'}).click();
  await vote.locator('#submit-vote').click();
  await vote.waitForFunction(()=>document.querySelector('#vote-message').textContent==='Answer received. Thank you.');
  assert.deepEqual(received[0],{p_session:session,p_week:1,p_unsure:false});
  assert.equal(authRequests.find(r=>r.path.endsWith('/signup')).body.gotrue_meta_security.captcha_token,'synthetic-captcha-token');
  await vote.reload();await vote.waitForFunction(()=>document.querySelector('#state-badge').textContent==='Voting open');
  await vote.locator('#week-slider').click();failNext=true;await vote.locator('#submit-vote').click();
  await vote.waitForFunction(()=>document.querySelector('#vote-message').textContent.includes('not confirmed'));
  assert.equal(await vote.locator('#week-output').textContent(),'Week 6');
  await vote.locator('#submit-vote').click();
  await vote.waitForFunction(()=>document.querySelector('#vote-message').textContent==='Answer received. Thank you.');
  assert.equal(submissions,1);
  const result=await live.newPage();observe(result);await result.setViewportSize({width:1240,height:540});
  await result.goto(`${base}?mode=results&session=${session}`);
  await result.waitForFunction(()=>document.querySelector('#state-badge').textContent==='Voting open');
  assert.equal(await result.locator('#histogram').isVisible(),false);
  sessionState='closed';
  await vote.waitForFunction(()=>document.querySelector('#state-badge').textContent==='Voting closed');
  assert.equal(await vote.locator('#submit-vote').isDisabled(),true);
  assert.equal(await result.locator('#histogram').isVisible(),false);
  sessionState='revealed';await result.waitForSelector('#histogram svg');
  assert.equal(await result.locator('#histogram rect').count(),29);
  const admin=await live.newPage();observe(admin);await admin.setViewportSize({width:1000,height:900});
  await admin.goto(`${base}?mode=admin&session=${session}`);
  await admin.locator('#email').fill('presenter@example.test');await admin.locator('#password').fill('synthetic-test-only');
  const beforeLogin=authRequests.length;
  await admin.locator('#login-form button[type=submit]').click();
  assert.match(await admin.locator('#connection-message').textContent(),/Complete the security check/);
  assert.equal(authRequests.length,beforeLogin,'No password request before CAPTCHA');
  await admin.getByRole('button',{name:'Complete mock security check'}).click();
  await admin.locator('#login-form button[type=submit]').click();await admin.waitForSelector('#admin-panel');
  const inputBox=await admin.locator('#session-name').boundingBox();
  const buttonBox=await admin.locator('#new-session-form button').boundingBox();
  assert.ok(Math.abs(inputBox.y-buttonBox.y)<1,'New-session input and button tops align');
  assert.ok(Math.abs(inputBox.y+inputBox.height-buttonBox.y-buttonBox.height)<1,'New-session input and button bottoms align');
  assert.equal(authRequests.find(r=>r.path.endsWith('/token')).body.gotrue_meta_security.captcha_token,'synthetic-captcha-token');
  assert.equal(await admin.locator('#question-url').inputValue(),`${base}?mode=question&session=${session}`);
  await admin.locator('#session-name').fill('Another rehearsal');await admin.locator('#new-session-form button').click();
  await admin.waitForFunction(id=>document.querySelector('#audience-url').value.includes(id),second);
  await admin.waitForFunction(()=>!document.querySelector('[data-action=open]').disabled);
  assert.equal(await admin.locator('#admin-count').textContent(),'0 responses');
  assert.ok((await result.url()).includes(session));
  assert.equal(await admin.locator('#password').inputValue(),'');
  await admin.screenshot({path:join(artifacts,'presenter.png'),fullPage:true});
  // Cancellation sends no delete request; the named session remains selected.
  const cancelDialog=admin.waitForEvent('dialog');
  const cancelClick=admin.locator('#delete-session').click();
  const cancel=await cancelDialog;
  assert.match(cancel.message(),/"New session" and its 0 responses/);
  assert.match(cancel.message(),/cannot be undone/);
  await cancel.dismiss();await cancelClick;
  await admin.waitForFunction(()=>!document.querySelector('#delete-session').disabled);
  assert.deepEqual(deletionRequests,[]);
  assert.equal(await admin.locator('#session-select').inputValue(),second);
  // Missing production setup must explain the required SQL, not lose the session.
  deletionAvailable=false;
  admin.once('dialog',dialog=>dialog.accept());await admin.locator('#delete-session').click();
  await admin.waitForFunction(()=>document.querySelector('#connection-message').textContent.includes('updated supabase/poll-01.sql'));
  assert.equal(await admin.locator('#session-select').inputValue(),second);
  assert.deepEqual(deletionRequests,[]);deletionAvailable=true;
  sessionState='open';await admin.locator('#session-select').selectOption(session);
  await admin.waitForFunction(()=>document.querySelector('#state-badge').textContent==='Voting open');
  assert.equal(await admin.locator('#delete-session').isDisabled(),true);
  // Delete a revealed session; clear its selection/links and the old result view.
  sessionState='revealed';await admin.reload();await admin.waitForSelector('#admin-panel');
  await admin.waitForFunction(()=>!document.querySelector('#delete-session').disabled);
  const confirmDialog=admin.waitForEvent('dialog');
  const confirmClick=admin.locator('#delete-session').click();
  const confirmation=await confirmDialog;
  assert.match(confirmation.message(),/"Rehearsal" and its 1 response\?/);
  await confirmation.accept();await confirmClick;
  await admin.waitForFunction(()=>document.querySelector('#admin-count').textContent.startsWith('Session deleted.'));
  assert.deepEqual(deletionRequests,[session]);
  assert.equal(await admin.locator('#session-select').inputValue(),'');
  assert.equal(await admin.locator(`#session-select option[value="${session}"]`).count(),0);
  assert.equal(await admin.locator(`#session-select option[value="${second}"]`).count(),1);
  assert.equal(await admin.locator('#session-links').isVisible(),false);
  assert.equal(await admin.locator('#delete-session').isDisabled(),true);
  assert.equal(new URL(admin.url()).searchParams.has('session'),false);
  await result.waitForFunction(()=>document.querySelector('#results-wait').textContent==='This poll session is no longer available.');
  assert.equal(await result.locator('#histogram').isVisible(),false);
  assert.equal(await result.locator('#results-table tbody tr').count(),0);
  await live.close();
  assert.deepEqual(errors,[]);
  console.log('PASS: previews, no preview network writes, 1240×540 layout, all 29 ticks without label overlap, slider tap/drag and keyboard rollover, explicit selection, aligned presenter controls, CAPTCHA gating/expiry and auth-token forwarding, submission, retry, closure, hidden/revealed results, presenter login, session-bound links, deletion confirmation/cancel, open-poll protection, setup errors, and deleted-session cleanup.');
  console.log(`Screenshots: ${artifacts}`);
}finally{await browser.close();}
