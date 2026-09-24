import assert from 'node:assert/strict';
import {mkdtemp, readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const {chromium}=await import(process.env.SLIDE_PLAYWRIGHT?pathToFileURL(process.env.SLIDE_PLAYWRIGHT).href:'playwright');
const browser=await chromium.launch({channel:'chrome',headless:true});
const artifacts=await mkdtemp(join(tmpdir(),'slide-17-browser-'));
const data=JSON.parse(await readFile(new URL('../data/slide-17/slide-17.json',import.meta.url),'utf8'));
const url=pathToFileURL(fileURLToPath(new URL('../docs/slide-17.html',import.meta.url))).href;
const errors=[];
try {
  const context=await browser.newContext({viewport:{width:1240,height:540}});
  await context.route(/^https?:/,route=>{errors.push(`Unexpected request: ${route.request().url()}`);return route.abort();});
  const page=await context.newPage();
  page.on('pageerror',error=>errors.push(error.message));
  let geometry;
  for(const state of [1,2]) {
    await page.goto(`${url}#state=${state}`);
    await page.waitForFunction(state=>{
      const style=getComputedStyle(document.querySelector('#reconstructed'));
      return style.opacity===(state===2?'1':'0')&&style.visibility===(state===2?'visible':'hidden');
    },state);
    assert.equal(await page.locator('#state-select').inputValue(),String(state));
    assert.equal(await page.locator('#back-button').isDisabled(),state===1);
    assert.equal(await page.locator('#next-button').isDisabled(),state===2);
    assert.equal(await page.locator('#reconstructed').isVisible(),state===2);
    assert.equal(await page.locator('#reconstructed').getAttribute('aria-hidden'),String(state!==2));
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),1240);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight),540);
    const labels=await page.locator('svg text, .subtitle, .controls').evaluateAll(nodes=>nodes.filter(el=>getComputedStyle(el).visibility!=='hidden').map(el=>({text:el.textContent,r:el.getBoundingClientRect().toJSON()})));
    assert.deepEqual(labels.filter(({r})=>r.left<0||r.top<0||r.right>1240||r.bottom>540),[],'All labels fit the iframe');
    const overlaps=labels.flatMap((a,i)=>labels.slice(i+1).filter(b=>a.r.left<b.r.right&&a.r.right>b.r.left&&a.r.top<b.r.bottom&&a.r.bottom>b.r.top).map(b=>[a.text,b.text]));
    assert.deepEqual(overlaps,[],'Visible text does not overlap');
    const marks=await page.locator('#axes, #observed').evaluateAll(nodes=>nodes.map(el=>el.innerHTML));
    if(!geometry) geometry=marks;
    assert.deepEqual(marks,geometry,'Revealing history must not change axes or observations');
    for(const kind of ['observed','reconstructed']) {
      const path=await page.locator(`#${kind} path`).getAttribute('d');
      const vertices=Array.from(path.matchAll(/[ML]([\d.]+),([\d.]+)/g),m=>[Number(m[1]),Number(m[2])]);
      assert.equal(vertices.length,data[kind].length);
      assert.equal((path.match(/M/g)||[]).length,1);
      for(let index=0;index<vertices.length;index++) {
        const point=data[kind][index];
        const ratio=(Date.parse(point.date)-Date.parse(data.start))/(Date.parse(data.end)-Date.parse(data.start));
        assert.ok(Math.abs(vertices[index][0]-(84+1046*ratio))<.006,'Every date maps to the shared calendar');
        assert.ok(Math.abs(vertices[index][1]-(338-point.value/2500*275))<.006,'Every count maps to the displayed axis');
      }
    }
    assert.equal(await page.locator('#reconstructed path').getAttribute('stroke-dasharray'),'5 3');
    assert.equal(await page.locator('#observed path').getAttribute('stroke-dasharray'),null);
    assert.doesNotMatch(await page.locator('body').innerText(),/—/);
    await page.screenshot({path:join(artifacts,`state-${state}.png`)});
  }
  await page.locator('#back-button').click();
  await page.waitForFunction(()=>document.body.dataset.state==='1');
  await page.locator('#next-button').click();
  await page.waitForFunction(()=>document.body.dataset.state==='2');
  await page.locator('#state-select').selectOption('1');
  await page.waitForFunction(()=>document.body.dataset.state==='1');
  await page.evaluate(()=>document.activeElement.blur());
  await page.keyboard.press('ArrowRight');
  await page.waitForFunction(()=>document.body.dataset.state==='2');
  await page.keyboard.press('ArrowLeft');
  await page.waitForFunction(()=>document.body.dataset.state==='1');
  await page.emulateMedia({reducedMotion:'reduce'});
  assert.equal(await page.locator('#reconstructed').evaluate(el=>getComputedStyle(el).transitionDuration),'0s');
  await page.goto(`${url}#state=invalid`);
  assert.equal(await page.locator('#state-select').inputValue(),'1');
  assert.deepEqual(errors,[]);
  console.log(`Slide 17: both states, 599 plotted values, navigation, layout, and reduced motion passed. Screenshots: ${artifacts}`);
} finally {await browser.close();}
