import assert from 'node:assert/strict';
import {mkdtemp, readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const {chromium}=await import(process.env.SLIDE_PLAYWRIGHT?pathToFileURL(process.env.SLIDE_PLAYWRIGHT).href:'playwright');
const browser=await chromium.launch({channel:'chrome',headless:true});
const artifacts=await mkdtemp(join(tmpdir(),'slide-17-browser-'));
const data=JSON.parse(await readFile(new URL('../data/slide-17/slide-17.json',import.meta.url),'utf8'));
const shiftPx=1046*data.training_shift_days*86400000/(Date.parse(data.end)-Date.parse(data.start));
const retained=data.observed.filter(point=>point.date>=data.retained_observed_start);
const excluded=data.observed.filter(point=>point.date<data.retained_observed_start);
const url=pathToFileURL(fileURLToPath(new URL('../docs/slide-17.html',import.meta.url))).href;
const errors=[];
try {
  const context=await browser.newContext({viewport:{width:1240,height:540}});
  await context.route(/^https?:/,route=>{errors.push(`Unexpected request: ${route.request().url()}`);return route.abort();});
  const page=await context.newPage();
  page.on('pageerror',error=>errors.push(error.message));
  let geometry;
  for(const state of [1,2,3]) {
    await page.goto(`${url}#state=${state}`);
    await page.waitForFunction(state=>{
      const style=getComputedStyle(document.querySelector('#reconstructed'));
      return style.opacity===(state>=2?'1':'0')&&style.visibility===(state>=2?'visible':'hidden');
    },state);
    await page.waitForFunction(({state,shiftPx})=>{
      const offset=new DOMMatrix(getComputedStyle(document.querySelector('#reconstructed-shift')).transform).m41;
      return Math.abs(offset-(state===3?shiftPx:0))<.001&&getComputedStyle(document.querySelector('#stitch-join')).opacity===(state===3?'1':'0');
    },{state,shiftPx});
    assert.equal(await page.locator('#state-select').inputValue(),String(state));
    assert.equal(await page.locator('#back-button').isDisabled(),state===1);
    assert.equal(await page.locator('#next-button').isDisabled(),false);
    assert.equal(await page.locator('#reconstructed').isVisible(),state>=2);
    assert.equal(await page.locator('#reconstructed').getAttribute('aria-hidden'),String(state===1));
    assert.equal(await page.locator('#observed-early').isVisible(),state!==3);
    assert.equal(await page.locator('#observed-retained').isVisible(),true);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),1240);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight),540);
    const labels=await page.locator('svg text, .subtitle, .controls').evaluateAll(nodes=>nodes.filter(el=>getComputedStyle(el).visibility!=='hidden'&&el.getBoundingClientRect().width>0).map(el=>({text:el.textContent,r:el.getBoundingClientRect().toJSON()})));
    assert.deepEqual(labels.filter(({r})=>r.left<0||r.top<0||r.right>1240||r.bottom>540),[],'All labels fit the iframe');
    const overlaps=labels.flatMap((a,i)=>labels.slice(i+1).filter(b=>a.r.left<b.r.right&&a.r.right>b.r.left&&a.r.top<b.r.bottom&&a.r.bottom>b.r.top).map(b=>[a.text,b.text]));
    assert.deepEqual(overlaps,[],'Visible text does not overlap');
    const marks=await page.locator('#axes, #observed-retained').evaluateAll(nodes=>nodes.map(el=>el.innerHTML));
    if(!geometry) geometry=marks;
    assert.deepEqual(marks,geometry,'Revealing history must not change axes or observations');
    for(const [kind,points] of [['reconstructed',data.reconstructed],['observed-early',[...excluded,retained[0]]],['observed-retained',retained]]) {
      const path=await page.locator(`#${kind} path`).getAttribute('d');
      const vertices=Array.from(path.matchAll(/[ML]([\d.]+),([\d.]+)/g),m=>[Number(m[1]),Number(m[2])]);
      assert.equal(vertices.length,points.length);
      assert.equal((path.match(/M/g)||[]).length,1);
      for(let index=0;index<vertices.length;index++) {
        const point=points[index];
        const ratio=(Date.parse(point.date)-Date.parse(data.start))/(Date.parse(data.end)-Date.parse(data.start));
        assert.ok(Math.abs(vertices[index][0]-(84+1046*ratio))<.006,'Every date maps to the shared calendar');
        assert.ok(Math.abs(vertices[index][1]-(338-point.value/2500*275))<.006,'Every count maps to the displayed axis');
      }
    }
    assert.equal(await page.locator('#reconstructed path').getAttribute('stroke-dasharray'),'5 3');
    assert.equal(await page.locator('#observed-retained path').getAttribute('stroke-dasharray'),null);
    assert.doesNotMatch(await page.locator('svg text, .subtitle').allTextContents().then(parts=>parts.join(' ')),/training time index/i);
    assert.equal(await page.locator('.takeaway').textContent(),'A longer training history provides more context for the model to forecast.');
    assert.doesNotMatch(await page.locator('body').innerText(),/—/);
    await page.screenshot({path:join(artifacts,`state-${state}.png`)});
  }
  await page.locator('#back-button').click();
  await page.waitForFunction(shiftPx=>{
    const offset=new DOMMatrix(getComputedStyle(document.querySelector('#reconstructed-shift')).transform).m41;
    return document.body.dataset.state==='2'&&offset>shiftPx*.25&&offset<shiftPx*.85;
  },shiftPx);
  await page.waitForFunction(()=>document.body.dataset.state==='2'&&new DOMMatrix(getComputedStyle(document.querySelector('#reconstructed-shift')).transform).m41===0);
  await page.locator('#next-button').click();
  await page.waitForFunction(shiftPx=>{
    const offset=new DOMMatrix(getComputedStyle(document.querySelector('#reconstructed-shift')).transform).m41;
    return offset>shiftPx*.25&&offset<shiftPx*.85;
  },shiftPx);
  await page.screenshot({path:join(artifacts,'forward-mid-animation.png')});
  await page.waitForFunction(shiftPx=>Math.abs(new DOMMatrix(getComputedStyle(document.querySelector('#reconstructed-shift')).transform).m41-shiftPx)<.001,shiftPx);
  const joinCoords=await page.locator('#stitch-join line').evaluate(el=>({x1:Number(el.getAttribute('x1')),x2:Number(el.getAttribute('x2'))}));
  assert.ok(Math.abs((joinCoords.x2-joinCoords.x1)-1046*7*86400000/(Date.parse(data.end)-Date.parse(data.start)))<.001,'Stitch connects consecutive weeks');
  await page.locator('#state-select').selectOption('1');
  await page.waitForFunction(()=>document.body.dataset.state==='1');
  await page.evaluate(()=>document.activeElement.blur());
  await page.keyboard.press('ArrowRight');
  await page.waitForFunction(()=>document.body.dataset.state==='2');
  await page.keyboard.press('ArrowLeft');
  await page.waitForFunction(()=>document.body.dataset.state==='1');
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.locator('#state-select').selectOption('3');
  await page.waitForFunction(()=>document.body.dataset.state==='3');
  for(const id of ['reconstructed','reconstructed-shift','observed-early','stitch-join']) {
    assert.equal(await page.locator(`#${id}`).evaluate(el=>getComputedStyle(el).transitionDuration),'0s');
  }
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.goto('about:blank');
  await page.goto(`${url}#state=3`);
  await page.waitForFunction(shiftPx=>{
    const offset=new DOMMatrix(getComputedStyle(document.querySelector('#reconstructed-shift')).transform).m41;
    return offset>shiftPx*.25&&offset<shiftPx*.85;
  },shiftPx);
  await page.waitForFunction(shiftPx=>Math.abs(new DOMMatrix(getComputedStyle(document.querySelector('#reconstructed-shift')).transform).m41-shiftPx)<.001,shiftPx);
  await page.locator('#next-button').click();
  await page.waitForFunction(()=>document.body.dataset.state==='4');
  const shifted=data.reconstructed.map(point=>({date:new Date(Date.parse(point.date)+data.training_shift_days*86400000).toISOString().slice(0,10),value:point.value}));
  for(const [kind,points] of [['full-reconstructed',[...shifted,retained[0]]],['full-observed',[...retained,...data.extended]]]) {
    const path=await page.locator(`#${kind} path`).getAttribute('d');
    const vertices=Array.from(path.matchAll(/[ML]([\d.]+),([\d.]+)/g),m=>[Number(m[1]),Number(m[2])]);
    assert.equal(vertices.length,points.length);
    assert.equal((path.match(/M/g)||[]).length,1);
    for(let index=0;index<vertices.length;index++) {
      const point=points[index];
      const expectedX=84+1046*(Date.parse(point.date)-Date.parse(data.start))/(Date.parse(data.full_end)-Date.parse(data.start));
      const expectedY=338-point.value/data.full_axis_max*275;
      assert.ok(Math.abs(vertices[index][0]-expectedX)<.006,'Full history preserves every date on the expanded axis');
      assert.ok(Math.abs(vertices[index][1]-expectedY)<.006,'Full history preserves every count on the expanded axis');
      assert.ok(vertices[index][0]>=84&&vertices[index][0]<=1130&&vertices[index][1]>=63&&vertices[index][1]<=338,'Full history fits the plot');
    }
  }
  assert.equal(await page.locator('#full-history').isVisible(),true);
  assert.equal(await page.locator('#initial-history').isVisible(),false);
  assert.equal(await page.locator('#full-history').getAttribute('aria-hidden'),'false');
  assert.equal(await page.locator('#next-button').isDisabled(),true);
  assert.equal(await page.locator('#back-button').isDisabled(),false);
  assert.ok((await page.locator('#full-axes text').allTextContents()).includes('Jul 2026'));
  assert.ok((await page.locator('#full-axes text').allTextContents()).includes('5,000'));
  const fullLabels=await page.locator('svg text, .subtitle, .controls').evaluateAll(nodes=>nodes.filter(el=>getComputedStyle(el).visibility!=='hidden'&&el.getBoundingClientRect().width>0).map(el=>({text:el.textContent,r:el.getBoundingClientRect().toJSON()})));
  assert.deepEqual(fullLabels.filter(({r})=>r.left<0||r.top<0||r.right>1240||r.bottom>540),[],'Full-history labels fit the iframe');
  assert.deepEqual(fullLabels.flatMap((a,i)=>fullLabels.slice(i+1).filter(b=>a.r.left<b.r.right&&a.r.right>b.r.left&&a.r.top<b.r.bottom&&a.r.bottom>b.r.top).map(b=>[a.text,b.text])),[],'Full-history labels do not overlap');
  await page.screenshot({path:join(artifacts,'state-4.png')});
  await page.locator('#back-button').click();
  await page.waitForFunction(()=>document.body.dataset.state==='3');
  assert.deepEqual(await page.locator('#axes, #observed-retained').evaluateAll(nodes=>nodes.map(el=>el.innerHTML)),geometry,'Returning from stage 4 restores the unchanged original plot');
  assert.equal(await page.locator('#observed-early').evaluate(el=>getComputedStyle(el).opacity),'0','Excluded observations stay hidden when returning to stage 3');
  assert.equal(await page.locator('#full-history').isVisible(),false);
  await page.goto('about:blank');
  await page.goto(`${url}#state=4`);
  await page.waitForFunction(()=>document.body.dataset.state==='4');
  assert.equal(await page.locator('#full-history').isVisible(),true);
  assert.equal(await page.locator('#state-select').inputValue(),'4');
  await page.goto(`${url}#state=invalid`);
  assert.equal(await page.locator('#state-select').inputValue(),'1');
  assert.deepEqual(errors,[]);
  console.log(`Slide 17: all four states, forward/reverse and direct-entry animation, source values, weekly stitch, full-history extension, layout, and reduced motion passed. Screenshots: ${artifacts}`);
} finally {await browser.close();}
