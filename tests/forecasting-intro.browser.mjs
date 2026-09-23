// Self-contained pages: no server, backend, or external runtime requests needed.
import assert from 'node:assert/strict';
import {mkdtemp} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const {chromium}=await import(process.env.SLIDE_PLAYWRIGHT?pathToFileURL(process.env.SLIDE_PLAYWRIGHT).href:'playwright');
const browser=await chromium.launch({channel:'chrome',headless:true});
const artifacts=await mkdtemp(join(tmpdir(),'forecasting-intro-browser-'));
const errors=[];
try {
  const context=await browser.newContext({viewport:{width:1240,height:540}});
  await context.route(/^https?:/,route=>{errors.push(`Unexpected request: ${route.request().url()}`);return route.abort();});
  let geometry;
  for(const number of [12,13,14,15]) {
    const page=await context.newPage(); page.on('pageerror',error=>errors.push(error.message));
    const url=pathToFileURL(fileURLToPath(new URL(`../docs/slide-${number}.html`,import.meta.url))).href;
    const lastState=number===15?4:3;
    for(let state=1;state<=lastState;state++) {
      await page.goto(`${url}#state=${state}`);
      assert.equal(await page.locator('#state-select').inputValue(),String(state));
      assert.equal(await page.locator('#back-button').isDisabled(),state===1);
      assert.equal(await page.locator('#next-button').isDisabled(),state===lastState);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),1240);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight),540);
      assert.doesNotMatch(await page.locator('body').innerText(),/—/);
      const outside=await page.locator('svg text, .subtitle, .controls, .decisions, .other-target, .target-name, .history, .horizon').evaluateAll(nodes=>nodes.filter(el=>getComputedStyle(el).visibility!=='hidden'&&el.getClientRects().length).map(el=>({text:el.textContent,box:el.getBoundingClientRect().toJSON()})).filter(({box:r})=>r.left<0||r.top<0||r.right>1240||r.bottom>540));
      assert.deepEqual(outside,[],`Slide ${number}, state ${state}: content outside frame`);
      assert.ok((await page.locator('svg path').evaluateAll(paths=>paths.map(p=>p.getAttribute('d')))).every(d=>!/(NaN|Infinity|undefined)/.test(d)));
      if(number===12) {
        assert.equal(await page.locator('.models').count(),state>=2?35:0);
        assert.equal(await page.locator('.ensemble').count(),state===3?1:0);
        assert.equal(await page.locator('.interval').count(),state===3?1:0);
        assert.equal(await page.locator('.observed').count(),1);
        assert.equal(await page.locator('.hospital').isVisible(),state===3);
        if(state===3)assert.equal(await page.locator('.hospital img').evaluate(img=>img.complete&&img.naturalWidth>0),true);
      } else if(number===13) {
        assert.equal(await page.locator('.participation, .bar').count(),0);
        assert.equal(await page.locator('.primary').isVisible(),state>=2);
        assert.equal(await page.locator('.other-targets').isVisible(),state===3);
        if(state===3) {
          assert.equal(await page.locator('.primary .target-name').innerText(),'Weekly hospital admissions');
          assert.deepEqual(await page.locator('.other-target').allInnerTexts(),['Influenza share of\nemergency visits','Categorical\nadmission changes\nIncrease / decrease','Peak timing','Peak admissions']);
        }
      } else {
        assert.equal(await page.locator('.ensemble.median').count(),1);
        assert.equal(await page.locator('.ensemble.interval-50').count(),number===15||state>=2?1:0);
        assert.equal(await page.locator('.ensemble.interval-95').count(),number===15||state>=3?1:0);
        assert.equal(await page.locator('.observed').count(),number===15?1:0);
        assert.equal(await page.locator('.baseline.median').count(),number===15&&state===4?1:0);
        assert.equal(await page.locator('.error-gap').count(),number===15&&state===2?1:0);
        assert.equal(await page.locator('.interval-miss').count(),number===15&&state===3?1:0);
        const marks=await page.locator('.ensemble.median, .tick').evaluateAll(nodes=>nodes.map(el=>({text:el.textContent,box:el.getBoundingClientRect().toJSON()})));
        if(!geometry) geometry=marks;
        assert.deepEqual(marks,geometry,'Slides 14 and 15 must keep the median and axis fixed');
        const overlaps=await page.locator('svg text').evaluateAll(nodes=>{
          const boxes=nodes.map(el=>({text:el.textContent,r:el.getBoundingClientRect()}));
          return boxes.flatMap((a,i)=>boxes.slice(i+1).filter(b=>a.r.left<b.r.right&&a.r.right>b.r.left&&a.r.top<b.r.bottom&&a.r.bottom>b.r.top).map(b=>[a.text,b.text]));
        });
        assert.deepEqual(overlaps,[],`Slide ${number}, state ${state}: overlapping text`);
        if(number===15&&state===4) assert.match(await page.locator('#chart').textContent(),/Relative WIS \(this forecast\): 0.63/);
      }
      await page.screenshot({path:join(artifacts,`slide-${number}-state-${state}.png`)});
    }
    await page.locator('#state-select').selectOption('3');await page.waitForFunction(()=>document.querySelector('#state-select').value==='3');
    await page.locator('#back-button').click();await page.waitForFunction(()=>document.querySelector('#state-select').value==='2');
    await page.locator('#back-button').click();await page.waitForFunction(()=>document.querySelector('#state-select').value==='1');
    await page.locator('#next-button').click();await page.waitForFunction(()=>document.querySelector('#state-select').value==='2');
    await page.locator('#state-select').selectOption('3');await page.waitForFunction(()=>location.hash==='#state=3');
    await page.evaluate(()=>document.activeElement.blur());await page.keyboard.press('ArrowLeft');await page.waitForFunction(()=>document.querySelector('#state-select').value==='2');
    await page.goto(`${url}#state=invalid`);assert.equal(await page.locator('#state-select').inputValue(),'1');
    await page.close();
  }
  assert.deepEqual(errors,[]);
  console.log(`All 13 states and navigation checks passed. Screenshots: ${artifacts}`);
} finally {await browser.close();}
