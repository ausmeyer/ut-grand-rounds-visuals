import { config } from './config.js';
import { callPoll } from '../polls/backend.js';
import { WEEKS, QUESTION, isSession, weekAt, normalizeResults } from './model.js';

const $ = id => document.getElementById(id);
const params = new URLSearchParams(location.search);
const mode = ['question', 'vote', 'results', 'admin'].includes(params.get('mode')) ? params.get('mode') : 'question';
const preview = params.get('preview') === '1';
let sessionId = params.get('session') || '';
let state = null, selectedWeek = null, busy = false, presenter = false, renderedSession = null, connectionFailed = false;
let captchaToken = '', captchaWidget = null, authenticated = false;
let client;
document.body.dataset.mode = mode;
$(`${mode}-view`).hidden = false;
$('preview-banner').hidden = !preview;
document.querySelectorAll('.question-text').forEach(el => { el.textContent = QUESTION; });
WEEKS.forEach((week, index) => {
  const tick = document.createElement('span');
  tick.textContent = week;
  tick.style.left = `${index / (WEEKS.length - 1) * 100}%`;
  $('week-ticks').append(tick);
});

function message(error) {
  const raw = error?.message || String(error);
  if (error?.code === 'PGRST202') return 'Run supabase/polls.sql in the Supabase SQL Editor to enable this poll.';
  if (/anonymous sign-ins are disabled/i.test(raw)) return 'Audience sign-in is not enabled yet. Please let the presenter know.';
  if (/rate limit/i.test(raw)) return 'Too many sign-ins from this network. Please let the presenter know and try again shortly.';
  if (/fetch|network|timeout|aborted/i.test(raw)) return 'Connection interrupted. Your selection is still here. Please retry.';
  return raw;
}
function showError(error) { $('connection-message').textContent = message(error); }
function clearError() { $('connection-message').textContent = ''; }
async function rpc(name, args = {}) {
  const data = await callPoll(client,1,name,args);
  if(name==='results')return {bins:data.bins.map(bin=>({week:bin.value,count:bin.count})),unsure:data.unsure};
  return data;
}
function link(view) {
  const url = new URL('poll-01.html', location.href);
  url.searchParams.set('mode', view);
  url.searchParams.set('session', sessionId);
  if (preview) url.searchParams.set('preview', '1');
  return url.href;
}
function updateLinks() {
  if (mode === 'question') {
    const url = link('vote');
    $('vote-link').href = url;
    $('vote-link').textContent = url;
    const qr = window.qrcode(0, 'M');
    qr.addData(url); qr.make();
    $('qr').innerHTML = qr.createSvgTag({ cellSize: 4, margin: 4, scalable: true });
    $('qr').setAttribute('aria-label', 'QR code linking to the voting form');
  }
  if (mode === 'admin') {
    $('session-links').hidden = !sessionId;
    for (const [view, id] of [['question','question'], ['results','results'], ['vote','audience']]) {
      $(`${id}-url`).value = link(view);
      $(`open-${view}`).href = link(view);
    }
  }
}
function updateVote() {
  const unsure = $('unsure').checked;
  $('week-output').textContent = unsure ? 'Not sure' : selectedWeek === null ? 'Choose a week' : `Week ${selectedWeek}`;
  $('week-slider').setAttribute('aria-valuetext', unsure ? 'Not sure selected' : selectedWeek === null ? 'No week selected' : `Week ${selectedWeek}`);
  const allowed = state === 'open' && !busy;
  $('week-slider').disabled = !allowed || unsure;
  $('unsure').disabled = !allowed;
  const captchaReady = !config.turnstileSiteKey || authenticated || captchaToken || preview;
  $('submit-vote').disabled = !allowed || (!unsure && selectedWeek === null) || !captchaReady;
}
function updateState(data) {
  state = data.state;
  const names = { ready:'Not open yet', open:'Voting open', closed:'Voting closed', revealed:'Results revealed' };
  $('state-badge').textContent = names[state] || (mode === 'admin' && !sessionId ? 'No session selected' : 'Unavailable');
  if (mode === 'vote') updateVote();
  if (mode === 'admin') {
    $('session-select').disabled = busy;
    $('new-session-form').querySelector('button').disabled = busy;
    $('sign-out').disabled = busy;
    $('delete-session').disabled = busy || !presenter || !sessionId || !['ready','closed','revealed'].includes(state);
    $('delete-session').title = state === 'open' ? 'Close voting before deleting this session.' : '';
    if (data.response_count !== null && data.response_count !== undefined)
      $('admin-count').textContent = `${data.response_count} ${data.response_count === 1 ? 'response' : 'responses'}`;
    else if (!sessionId) $('admin-count').textContent = 'Choose a session';
    for (const button of document.querySelectorAll('[data-action]')) {
      const from = { open:'ready', close:'open', reveal:'closed' }[button.dataset.action];
      button.disabled = busy || !presenter || state !== from;
    }
  }
}
function renderHistogram(data) {
  const { bins, unsure, numericCount } = normalizeResults(data);
  $('results-wait').hidden = true;
  $('histogram').hidden = false;
  $('response-summary').textContent = `${numericCount} week estimates · ${unsure} not sure`;
  $('empty-results').hidden = numericCount > 0;
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '0 0 1180 385');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', 'Histogram of peak-week estimates in seasonal order, week 44 through week 20');
  const add = (tag, attrs, text) => {
    const el = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k, v));
    if (text !== undefined) el.textContent = text;
    svg.append(el); return el;
  };
  const left=68, top=32, bottom=322, width=1092, step=width/29;
  const maximum = Math.max(1, ...bins.map(b => b.count));
  const tick = Math.max(1, Math.ceil(maximum/5));
  const ceiling = Math.ceil(maximum/tick)*tick;
  for (let count=0; count<=ceiling; count+=tick) {
    const y = bottom-(count/ceiling)*(bottom-top);
    add('line', { x1:left,y1:y,x2:left+width,y2:y,stroke:'#dce2df' });
    add('text', { x:left-12,y:y+5,'text-anchor':'end',fill:'#647278','font-size':16 }, String(count));
  }
  add('text', { x:20,y:178,transform:'rotate(-90 20 178)','text-anchor':'middle',fill:'#14242b','font-size':17 }, 'Number of responses');
  const tbody = $('results-table').querySelector('tbody'); tbody.replaceChildren();
  bins.forEach((bin,i) => {
    const height=bin.count/ceiling*(bottom-top), x=left+i*step+3;
    const bar=add('rect', { x,y:bottom-height,width:step-6,height,fill:'#2677a8',rx:2 });
    const title=document.createElementNS(ns,'title'); title.textContent=`Week ${bin.week}: ${bin.count}`; bar.append(title);
    add('text',{x:x+(step-6)/2,y:bottom+23,'text-anchor':'middle',fill:'#14242b','font-size':16},String(bin.week));
    const tr=document.createElement('tr');
    for (const value of [bin.week,bin.count]) { const td=document.createElement('td');td.textContent=value;tr.append(td); }
    tbody.append(tr);
  });
  add('text',{x:left+width/2,y:375,'text-anchor':'middle',fill:'#14242b','font-size':18},'Week of the year');
  const unsureRow=document.createElement('tr');
  for (const value of ['Not sure',unsure]) { const td=document.createElement('td');td.textContent=value;unsureRow.append(td); }
  tbody.append(unsureRow);
  $('histogram').replaceChildren(svg);
}
async function refresh() {
  if (!sessionId || (mode === 'admin' && !presenter)) return;
  const requestedId = sessionId;
  try {
    const data = preview ? {state: mode === 'results' ? 'revealed' : state || 'open', response_count:0} : await rpc('status',{p_session:requestedId});
    if (requestedId !== sessionId) return;
    updateState(data);
    if (connectionFailed) { clearError(); connectionFailed=false; }
    if (mode === 'results' && state === 'revealed' && renderedSession !== sessionId) {
      const result = preview ? { bins:WEEKS.map((week,i)=>({week,count:[0,1,0,1,2,2,4,5,8,10,11,14,12,9,8,6,4,3,2,2,1,0,1,0,0,0,0,0,0][i]})),unsure:3 } : await rpc('results',{p_session:requestedId});
      if (requestedId !== sessionId) return;
      renderHistogram(result); renderedSession = sessionId;
    }
  } catch (error) {
    connectionFailed=true;
    showError(error);
    if (mode === 'vote') { state = null; updateVote(); }
    $('state-badge').textContent = 'Connection unavailable';
    if (error.code === 'P0002' && mode === 'results') {
      $('histogram').hidden = true; $('histogram').replaceChildren();
      $('results-table').querySelector('tbody').replaceChildren();
      $('response-summary').textContent = ''; $('empty-results').hidden = true;
      $('results-wait').hidden = false;
      $('results-wait').textContent = 'This poll session is no longer available.';
      renderedSession = null;
    }
  }
}
async function pollLoop() {
  if (!document.hidden && !busy) await refresh();
  setTimeout(pollLoop, 3000);
}
function resetCaptcha() {
  captchaToken = '';
  if (captchaWidget !== null) window.turnstile.reset(captchaWidget);
}
async function setupCaptcha() {
  if (!config.turnstileSiteKey || preview || !['vote','admin'].includes(mode)) return;
  await new Promise((resolve,reject) => {
    const script=document.createElement('script');
    script.src='https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
    script.onload=resolve; script.onerror=()=>reject(new Error('Unable to load the security check. Please retry.'));
    document.head.append(script);
  });
  captchaWidget = window.turnstile.render($(`${mode === 'admin' ? 'admin' : 'vote'}-captcha`),{
    sitekey:config.turnstileSiteKey,
    callback:token=>{captchaToken=token;if(mode==='vote')updateVote();},
    'expired-callback':()=>{captchaToken='';if(mode==='vote')updateVote();},
  });
}
function selectWeek() { selectedWeek=weekAt(Number($('week-slider').value));updateVote(); }
$('week-slider').addEventListener('input', selectWeek);
$('week-slider').addEventListener('click', selectWeek);
$('unsure').addEventListener('change', updateVote);
$('vote-form').addEventListener('submit', async event => {
  event.preventDefault();
  if ($('submit-vote').disabled) return;
  busy=true; updateVote(); clearError(); $('vote-message').textContent='Submitting…';
  try {
    if (preview) { $('vote-message').textContent='Preview response only. Nothing was sent.'; return; }
    const {data:{session},error:sessionError}=await client.auth.getSession();
    if(sessionError)throw sessionError;
    authenticated=Boolean(session);
    if(!session) {
      if(config.turnstileSiteKey&&!captchaToken)throw new Error('Complete the security check first.');
      const {error}=await client.auth.signInAnonymously({options:{captchaToken:captchaToken || undefined}});
      resetCaptcha(); if(error)throw error; authenticated=true;
    }
    await rpc('submit',{p_session:sessionId,p_kind:$('unsure').checked?'not_sure':'week',p_start:$('unsure').checked?null:selectedWeek,p_end:null});
    $('vote-message').textContent='Answer received. Thank you.';
  } catch(error) { $('vote-message').textContent='Your answer was not confirmed. You can retry safely.';showError(error); }
  finally { busy=false;updateVote();await refresh(); }
});
async function loadSessions(selectId=sessionId) {
  const sessions=preview?(sessionId?[{id:sessionId,name:'Preview session',state:state||'ready'}]:[]):await rpc('list_sessions');
  $('session-select').replaceChildren(new Option('Choose a session',''));
  sessions.forEach(s=>$('session-select').append(new Option(`${s.name} (${s.state})`,s.id)));
  if(sessions.some(s=>s.id===selectId)) $('session-select').value=selectId;
}
async function showAdmin() {
  presenter=preview || await rpc('is_presenter');
  if(!presenter)throw new Error('This account has not been authorized as a presenter.');
  $('login-form').hidden=true;$('admin-panel').hidden=false;
  await loadSessions();updateLinks();await refresh();
}
$('login-form').addEventListener('submit',async event=>{
  event.preventDefault();clearError();
  const button=event.submitter;button.disabled=true;
  try {
    if(config.turnstileSiteKey&&!captchaToken)throw new Error('Complete the security check first.');
    const {error}=await client.auth.signInWithPassword({email:$('email').value.trim(),password:$('password').value,options:{captchaToken:captchaToken||undefined}});
    $('password').value='';resetCaptcha();if(error)throw error;
    await showAdmin();
  } catch(error) {showError(error);} finally {button.disabled=false;}
});
$('sign-out').addEventListener('click',async()=>{
  if(!preview)await client.auth.signOut({scope:'local'});
  presenter=false;$('admin-panel').hidden=true;$('login-form').hidden=false;
});
$('new-session-form').addEventListener('submit',async event=>{
  event.preventDefault();if(busy)return;busy=true;event.submitter.disabled=true;clearError();
  try {
    sessionId=preview?crypto.randomUUID():await rpc('create_session',{p_name:$('session-name').value.trim()});
    state='ready';const url=new URL(location.href);url.searchParams.set('session',sessionId);history.replaceState(null,'',url);
    await loadSessions(sessionId);updateLinks();await refresh();
  }catch(error){showError(error);}finally{busy=false;event.submitter.disabled=false;await refresh();}
});
$('session-select').addEventListener('change',async()=>{
  sessionId=$('session-select').value;state=null;
  const url=new URL(location.href);if(sessionId)url.searchParams.set('session',sessionId);else url.searchParams.delete('session');history.replaceState(null,'',url);
  updateLinks();updateState({state:null,response_count:null});await refresh();
});
document.querySelectorAll('[data-action]').forEach(button=>button.addEventListener('click',async()=>{
  if(busy||button.disabled)return;
  if(button.dataset.action==='close'&&!confirm('Close voting for this session? It cannot be reopened.'))return;
  if(button.dataset.action==='reveal'&&!confirm('Reveal this session’s histogram to anyone with its results link?'))return;
  busy=true;updateState({state,response_count:null});clearError();
  try {
    if(preview)state={open:'open',close:'closed',reveal:'revealed'}[button.dataset.action];
    else await rpc('transition',{p_session:sessionId,p_action:button.dataset.action});
    await loadSessions();
  }catch(error){showError(error);}finally{busy=false;await refresh();}
}));
$('delete-session').addEventListener('click',async()=>{
  if(busy||$('delete-session').disabled||!sessionId)return;
  const deletingId=sessionId;
  busy=true;updateState({state,response_count:null});clearError();
  let deleted=false;
  try {
    const details=preview?{name:'Preview session',state,response_count:0}:await rpc('status',{p_session:deletingId});
    if(details.state==='open')throw new Error('Close voting before deleting this session.');
    const count=details.response_count;
    if(!confirm(`Permanently delete "${details.name}" and its ${count} ${count===1?'response':'responses'}?\n\nThis cannot be undone. Its question, voting, and results links will stop working.`))return;
    if(!preview)await rpc('delete_session',{p_session:deletingId});
    sessionId='';state=null;deleted=true;
    const url=new URL(location.href);url.searchParams.delete('session');history.replaceState(null,'',url);
    updateLinks();await loadSessions();
  }catch(error){
    showError(error.code==='PGRST202'?new Error('To enable session deletion, run supabase/polls.sql in the Supabase SQL Editor.'):error);
  }finally{
    busy=false;updateState({state,response_count:null});await refresh();
    if(deleted)$('admin-count').textContent=preview?'Preview session removed. Nothing was deleted.':'Session deleted. Choose another session or create a new one.';
  }
});
for(const id of ['question-url','results-url','audience-url']) $(id).addEventListener('click',()=>$(id).select());

async function start() {
  if(preview&&!isSession(sessionId))sessionId='00000000-0000-4000-8000-000000000001';
  if(!preview) {
    if(!window.supabase)throw new Error('The poll library did not load. Please reload the page.');
    const isAuthView=['vote','admin'].includes(mode);
    client=window.supabase.createClient(config.url,config.publishableKey,{
      auth:{persistSession:isAuthView,autoRefreshToken:isAuthView,detectSessionInUrl:false,
        storageKey:mode==='admin'?'poll1-presenter':'poll1-voter',
        storage:isAuthView?(mode==='admin'?sessionStorage:localStorage):undefined},
      global:{fetch:(url,options={})=>fetch(url,{...options,cache:'no-store',signal:options.signal||AbortSignal.timeout(15000)})},
    });
  }
  if(mode!=='admin'&&!isSession(sessionId))throw new Error('Open this poll using the session link or QR code supplied by the presenter.');
  if(mode==='admin'&&sessionId&&!isSession(sessionId))sessionId='';
  updateLinks();
  if(mode==='vote') {
    authenticated=preview||Boolean((await client.auth.getSession()).data.session);
    updateVote();
  }
  if(mode==='admin') {
    if(preview||(await client.auth.getSession()).data.session)await showAdmin();
  }
  await setupCaptcha();await pollLoop();
}
start().catch(error=>{ $('state-badge').textContent='Unavailable';showError(error); });
