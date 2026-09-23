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
  for(const number of [12,13]) {
    const page=await context.newPage(); page.on('pageerror',error=>errors.push(error.message));
    const url=pathToFileURL(fileURLToPath(new URL(`../docs/slide-${number}.html`,import.meta.url))).href;
    for(const state of [1,2,3]) {
      await page.goto(`${url}#state=${state}`);
      assert.equal(await page.locator('#state-select').inputValue(),String(state));
      assert.equal(await page.locator('#back-button').isDisabled(),state===1);
      assert.equal(await page.locator('#next-button').isDisabled(),state===3);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),1240);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight),540);
      assert.doesNotMatch(await page.locator('body').innerText(),/—/);
      const outside=await page.locator('svg text, .subtitle, .controls, .decisions, .other-target, .target-name').evaluateAll(nodes=>nodes.filter(el=>getComputedStyle(el).visibility!=='hidden'&&el.getClientRects().length).map(el=>({text:el.textContent,box:el.getBoundingClientRect().toJSON()})).filter(({box:r})=>r.left<0||r.top<0||r.right>1240||r.bottom>540));
      assert.deepEqual(outside,[],`Slide ${number}, state ${state}: content outside frame`);
      assert.ok((await page.locator('svg path').evaluateAll(paths=>paths.map(p=>p.getAttribute('d')))).every(d=>!/(NaN|Infinity|undefined)/.test(d)));
      if(number===12) {
        assert.equal(await page.locator('.models').count(),state>=2?35:0);
        assert.equal(await page.locator('.ensemble').count(),state===3?1:0);
        assert.equal(await page.locator('.interval').count(),state===3?1:0);
        assert.equal(await page.locator('.observed').count(),1);
        assert.equal(await page.locator('.hospital').isVisible(),state===3);
        if(state===3)assert.equal(await page.locator('.hospital img').evaluate(img=>img.complete&&img.naturalWidth>0),true);
      } else {
        assert.equal(await page.locator('.participation').isVisible(),state>=2);
        assert.equal(await page.locator('.targets').isVisible(),state===3);
        assert.deepEqual(await page.locator('.bar').evaluateAll(bars=>bars.map(b=>Number(b.dataset.count))),[23,21,34,43,49]);
        if(state===3) {
          assert.equal(await page.locator('.primary .target-name').innerText(),'Weekly hospital admissions');
          assert.deepEqual(await page.locator('.other-target').allInnerTexts(),['Influenza share of\nemergency visits','Categorical\nadmission changes\nIncrease / decrease','Peak timing','Peak admissions']);
        }
      }
      await page.screenshot({path:join(artifacts,`slide-${number}-state-${state}.png`)});
    }
    await page.locator('#back-button').click();await page.waitForFunction(()=>document.querySelector('#state-select').value==='2');
    await page.locator('#back-button').click();await page.waitForFunction(()=>document.querySelector('#state-select').value==='1');
    await page.locator('#next-button').click();await page.waitForFunction(()=>document.querySelector('#state-select').value==='2');
    await page.locator('#state-select').selectOption('3');await page.waitForFunction(()=>location.hash==='#state=3');
    await page.locator('#state-select').evaluate(el=>el.blur());await page.keyboard.press('ArrowLeft');await page.waitForFunction(()=>document.querySelector('#state-select').value==='2');
    await page.goto(`${url}#state=invalid`);assert.equal(await page.locator('#state-select').inputValue(),'1');
    await page.close();
  }
  assert.deepEqual(errors,[]);
  console.log(`All six states and navigation checks passed. Screenshots: ${artifacts}`);
} finally {await browser.close();}
