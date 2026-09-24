import assert from 'node:assert/strict';
import {mkdtemp, readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const {chromium}=await import(process.env.SLIDE_PLAYWRIGHT?pathToFileURL(process.env.SLIDE_PLAYWRIGHT).href:'playwright');
const browser=await chromium.launch({channel:'chrome',headless:true});
const artifacts=await mkdtemp(join(tmpdir(),'slide-18-browser-'));
const data=JSON.parse(await readFile(new URL('../data/slide-18/slide-18.json',import.meta.url),'utf8'));
const url=pathToFileURL(fileURLToPath(new URL('../docs/slide-18.html',import.meta.url))).href;
const errors=[];
try {
  const context=await browser.newContext({viewport:{width:1240,height:540}});
  await context.route(/^https?:/,route=>{errors.push(`Unexpected request: ${route.request().url()}`);return route.abort();});
  const page=await context.newPage();
  page.on('pageerror',error=>errors.push(error.message));
  const settled=async state=>page.waitForFunction(state=>{
    const pooled=new DOMMatrix(getComputedStyle(document.querySelector('#pooled-model')).transform).m41;
    const old=getComputedStyle(document.querySelector('#earlier-models'));
    const detail=getComputedStyle(document.querySelector('#distribution'));
    return document.body.dataset.state===String(state)&&Math.abs(pooled-(state===1?850:404))<.001&&old.opacity===(state===1?'1':'0')&&detail.opacity===(state===1?'0':'1');
  },state);
  for(const state of [1,2]) {
    await page.goto(`${url}#state=${state}`);
    await settled(state);
    assert.equal(await page.locator('#state-select').inputValue(),String(state));
    assert.equal(await page.locator('#back-button').isDisabled(),state===1);
    assert.equal(await page.locator('#next-button').isDisabled(),state===2);
    assert.equal(await page.locator('#earlier-models').isVisible(),state===1);
    assert.equal(await page.locator('#distribution').isVisible(),state===2);
    assert.equal(await page.locator('#earlier-models').getAttribute('aria-hidden'),String(state!==1));
    assert.equal(await page.locator('#distribution').getAttribute('aria-hidden'),String(state!==2));
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),1240);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight),540);
    const labels=await page.locator('svg text, .subtitle, .controls').evaluateAll(nodes=>nodes.filter(el=>getComputedStyle(el).visibility!=='hidden').map(el=>({text:el.textContent,r:el.getBoundingClientRect().toJSON()})));
    assert.deepEqual(labels.filter(({r})=>r.left<0||r.top<0||r.right>1240||r.bottom>540),[],'All text fits the fixed iframe');
    assert.deepEqual(labels.flatMap((a,i)=>labels.slice(i+1).filter(b=>a.r.left<b.r.right&&a.r.right>b.r.left&&a.r.top<b.r.bottom&&a.r.bottom>b.r.top).map(b=>[a.text,b.text])),[],'Visible labels do not overlap');
    assert.equal(await page.locator('#quantile-count').textContent(),'Derive 23');
    assert.doesNotMatch(await page.locator('body').innerText(),/—/);
    await page.screenshot({path:join(artifacts,`state-${state}.png`)});
  }
  const vertices=Array.from((await page.locator('#density-curve').getAttribute('d')).matchAll(/[ML]([\d.]+),([\d.]+)/g),m=>[Number(m[1]),Number(m[2])]);
  assert.equal(vertices.length,141);
  const peak=Math.max(...data.curve.map(point=>point.density));
  data.curve.forEach((point,i)=>{
    assert.ok(Math.abs(vertices[i][0]-(980+point.density/peak*100))<.006);
    assert.ok(Math.abs(vertices[i][1]-(198-point.z/3.5*124))<.006);
  });
  assert.equal(vertices[70][1],Number(await page.locator('#center-marker').getAttribute('y1')),'Center marker aligns with the forecast value');
  assert.equal(vertices[70][1],Number(await page.locator('#forecast-center').getAttribute('cy')),'Density and future forecast point have the same vertical center');
  assert.ok(Math.abs(Number(await page.locator('#spread-marker').getAttribute('y1'))-(198-124/3.5))<.006);
  assert.ok(Math.abs(Number(await page.locator('#spread-marker').getAttribute('y2'))-(198+124/3.5))<.006);
  assert.equal(await page.locator('#spread-marker').getAttribute('x1'),await page.locator('#spread-marker').getAttribute('x2'),'Spread is vertical');
  assert.equal(await page.locator('#forecast-link').getAttribute('d'),'M911,213 L980,198');
  assert.ok(await page.locator('#center-label').evaluate(el=>el.getBoundingClientRect().right<document.getElementById('density-axis').getBoundingClientRect().left-10),'Center label stays clear of the vertical forecast-time line');
  assert.match(await page.locator('#diagram-desc').textContent(),/not a trajectory/);
  const pooled=await page.locator('#pooled-model').elementHandle();
  await page.locator('#back-button').click();
  await page.waitForFunction(()=>{
    const x=new DOMMatrix(getComputedStyle(document.querySelector('#pooled-model')).transform).m41;
    return x>480&&x<780;
  });
  await settled(1);
  await page.locator('#next-button').click();
  await page.waitForFunction(()=>{
    const x=new DOMMatrix(getComputedStyle(document.querySelector('#pooled-model')).transform).m41;
    return x>480&&x<780;
  });
  assert.equal(await pooled.evaluate(el=>el===document.getElementById('pooled-model')),true,'The same pooled model element moves between views');
  await page.screenshot({path:join(artifacts,'mid-transition.png')});
  await settled(2);
  await page.locator('#state-select').selectOption('1');
  await settled(1);
  await page.evaluate(()=>document.activeElement.blur());
  await page.keyboard.press('ArrowRight');
  await settled(2);
  await page.keyboard.press('ArrowLeft');
  await settled(1);
  await page.goto('about:blank');
  await page.goto(`${url}#state=2`);
  await page.waitForFunction(()=>{
    const x=new DOMMatrix(getComputedStyle(document.querySelector('#pooled-model')).transform).m41;
    return document.body.dataset.state==='2'&&x>480&&x<780;
  });
  await page.locator('#back-button').click();
  await settled(1);
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.locator('#next-button').click();
  await settled(2);
  for(const id of ['pooled-model','earlier-models','distribution']) assert.equal(await page.locator(`#${id}`).evaluate(el=>getComputedStyle(el).transitionDuration),'0s');
  await page.goto(`${url}#state=invalid`);
  await settled(1);
  assert.deepEqual(errors,[]);
  console.log(`Slide 18: both views, bounds, label spacing, curve geometry, forward/reverse animation, direct entry, interruption, keyboard navigation, reduced motion, and offline rendering passed. Screenshots: ${artifacts}`);
} finally {await browser.close();}
