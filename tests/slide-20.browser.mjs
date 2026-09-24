import assert from 'node:assert/strict';
import {mkdtemp,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const {chromium}=await import(process.env.SLIDE_PLAYWRIGHT?pathToFileURL(process.env.SLIDE_PLAYWRIGHT).href:'playwright');
const browser=await chromium.launch({channel:'chrome',headless:true});
const artifacts=await mkdtemp(join(tmpdir(),'slide-20-browser-'));
const data=JSON.parse(await readFile(new URL('../data/slide-20/slide-20.json',import.meta.url),'utf8'));
const url=pathToFileURL(fileURLToPath(new URL('../docs/slide-20.html',import.meta.url))).href;
const errors=[];
const stamp=d=>Date.parse(`${d}T00:00:00Z`);
const x=d=>248+(stamp(d)-stamp(data.start))/(stamp(data.end)-stamp(data.start))*910;
try {
  const context=await browser.newContext({viewport:{width:1240,height:540}});
  await context.route(/^https?:/,route=>{errors.push(`Unexpected request: ${route.request().url()}`);return route.abort();});
  const page=await context.newPage();
  page.on('pageerror',error=>errors.push(error.message));
  const settled=state=>page.waitForFunction(state=>document.body.dataset.state===String(state)&&Array.from(document.querySelectorAll('.view')).every((el,i)=>getComputedStyle(el).opacity===(i===state-1?'1':'0')),state);
  let calendar;
  for(const state of [1,2,3]) {
    await page.goto(`${url}#state=${state}`); await settled(state);
    assert.equal(await page.locator('#state-select').inputValue(),String(state));
    assert.equal(await page.locator('#back-button').isDisabled(),state===1);
    assert.equal(await page.locator('#next-button').isDisabled(),state===3);
    const markup=await page.locator('#calendar').innerHTML(); calendar??=markup;
    assert.equal(markup,calendar,'Calendar positions remain fixed');
    for(const view of [1,2,3]) assert.equal(await page.locator(`#view-${view}`).isVisible(),view===state);
    const count=[1,3,4][state-1],height=(380-20*(count-1))/count;
    const panels=await page.locator(`#view-${state} > g`).all();
    assert.equal(panels.length,count);
    for(const [i,panel] of panels.entries()) {
      const signal=data.panels[i],top=24+i*(height+20),bottom=top+height;
      assert.equal(await panel.getAttribute('data-signal'),signal.id);
      const path=await panel.locator('.signal-line').getAttribute('d');
      const vertices=Array.from(path.matchAll(/[ML]([\d.]+),([\d.]+)/g),m=>[Number(m[1]),Number(m[2])]);
      const expected=signal.points.filter(p=>p.value!==null).map(p=>[x(p.date),bottom-(p.value-signal.domain[0])/(signal.domain[1]-signal.domain[0])*height]);
      assert.equal(vertices.length,expected.length);
      vertices.forEach((p,n)=>p.forEach((value,j)=>assert.ok(Math.abs(value-expected[n][j])<.006,'Every vertex matches its source value and calendar date')));
      assert.equal(await panel.locator('.unit').textContent(),signal.unit);
      assert.equal(await panel.locator('.signal-line').getAttribute('stroke'),signal.color);
    }
    const labels=await page.locator(`#view-${state} text, #calendar text, .subtitle, .controls`).evaluateAll(nodes=>nodes.map(el=>({text:el.textContent,r:el.getBoundingClientRect().toJSON()})));
    assert.deepEqual(labels.filter(({r})=>r.left<0||r.top<0||r.right>1240||r.bottom>540),[],'All labels fit');
    assert.deepEqual(labels.flatMap((a,i)=>labels.slice(i+1).filter(b=>a.r.left<b.r.right&&a.r.right>b.r.left&&a.r.top<b.r.bottom&&a.r.bottom>b.r.top).map(b=>[a.text,b.text])),[],'Labels do not overlap');
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),1240);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight),540);
    await page.screenshot({path:join(artifacts,`state-${state}.png`)});
  }
  await page.locator('#back-button').click();
  await page.waitForFunction(()=>{const o=Number(getComputedStyle(document.getElementById('view-2')).opacity);return o>.1&&o<.9;});
  await settled(2);
  await page.locator('#next-button').click(); await settled(3);
  await page.locator('#state-select').selectOption('1'); await settled(1);
  await page.evaluate(()=>document.activeElement.blur());
  await page.keyboard.press('ArrowRight'); await settled(2);
  await page.keyboard.press('ArrowLeft'); await settled(1);
  await page.locator('#state-select').selectOption('3');
  await page.locator('#state-select').selectOption('2'); await settled(2);
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.locator('#next-button').click(); await settled(3);
  assert.equal(await page.locator('#view-3').evaluate(el=>getComputedStyle(el).transitionDuration),'0s');
  await page.goto(`${url}#state=invalid`); await settled(1);
  assert.deepEqual(errors,[]);
  console.log(`Slide 20: all three builds, all plotted values, calendar alignment, labels, navigation, fades, reduced motion, and offline rendering passed. Screenshots: ${artifacts}`);
} finally {await browser.close();}
