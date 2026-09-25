import assert from 'node:assert/strict';
import {mkdtemp,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const {chromium}=await import(process.env.SLIDE_PLAYWRIGHT?pathToFileURL(process.env.SLIDE_PLAYWRIGHT).href:'playwright');
const slide=process.env.SLIDE_NUMBER||'19';
assert.ok(['19','21'].includes(slide));
const browser=await chromium.launch({channel:'chrome',headless:true});
const artifacts=await mkdtemp(join(tmpdir(),`slide-${slide}-browser-`));
const data=JSON.parse(await readFile(new URL(`../data/slide-${slide}/slide-${slide}.json`,import.meta.url),'utf8'));
const url=pathToFileURL(fileURLToPath(new URL(`../docs/slide-${slide}.html`,import.meta.url))).href;
const errors=[];
const stamp=d=>Date.parse(`${d}T00:00:00Z`);
const x=d=>88+(stamp(d)-stamp(data.start))/(stamp(data.end)-stamp(data.start))*1070;
const y=v=>408-v/data.axis_max*354;
const vertices=d=>Array.from(d.matchAll(/[ML]([\d.]+),([\d.]+)/g),m=>[Number(m[1]),Number(m[2])]);
function check(points,expected) {
  assert.equal(points.length,expected.length);
  points.forEach((point,i)=>point.forEach((v,j)=>assert.ok(Math.abs(v-expected[i][j])<.006)));
}
try {
  const context=await browser.newContext({viewport:{width:1240,height:540}});
  await context.route(/^https?:/,route=>{errors.push(`Unexpected request: ${route.request().url()}`);return route.abort();});
  const page=await context.newPage();
  page.on('pageerror',error=>errors.push(error.message));
  const settled=async state=>{
    await page.waitForFunction(state=>document.body.dataset.state===String(state)&&Array.from(document.querySelectorAll('.forecast-layer')).every((el,i)=>getComputedStyle(el).opacity===(i===state-1?'1':'0')),state);
    assert.equal(await page.locator('#rwis').textContent(),`rWIS: ${data.scores[state-1].rwis.toFixed(2)}`);
    assert.match(await page.locator('#score-desc').textContent(),new RegExp(`${data.scores[state-1].n} matched location-weeks for horizon ${state-1}`));
  };
  let truthPath,axesMarkup;
  for(const state of [1,2,3,4]) {
    await page.goto(`${url}#state=${state}`);
    await settled(state);
    assert.equal(await page.locator('#state-select').inputValue(),String(state));
    assert.equal(await page.locator('#legend text').count(),5);
    assert.equal(await page.locator('#rwis').getAttribute('text-anchor'),'end');
    assert.equal(await page.locator('#rwis').getAttribute('x'),'1158');
    assert.equal(await page.locator('#back-button').isDisabled(),state===1);
    assert.equal(await page.locator('#next-button').isDisabled(),state===4);
    for(const horizon of [0,1,2,3]) {
      assert.equal(await page.locator(`#horizon-${horizon}`).isVisible(),horizon===state-1);
      assert.equal(await page.locator(`#horizon-${horizon}`).getAttribute('aria-hidden'),String(horizon!==state-1));
    }
    const path=await page.locator('#truth-line').getAttribute('d'),axes=await page.locator('#axes').innerHTML();
    truthPath??=path; axesMarkup??=axes;
    assert.equal(path,truthPath,'Observations stay unchanged');
    assert.equal(axes,axesMarkup,'Axes stay unchanged');
    check(vertices(path),data.observed.map(p=>[x(p.date),y(p.value)]));
    assert.equal(await page.locator('#truth-line').getAttribute('stroke'),'#111111');
    assert.ok(await page.locator('#observed').evaluate(el=>Boolean(document.getElementById('forecasts').compareDocumentPosition(el)&Node.DOCUMENT_POSITION_FOLLOWING)),'Observed line is drawn above forecast bands');
    const group=data.series[state-1];
    const segments=await page.locator(`#horizon-${state-1} > g`).all();
    assert.equal(segments.length,1,'Complete weekly forecasts render as one continuous segment');
    assert.equal(group.points.length,82-state);
    assert.equal(group.points.filter(p=>p.reference_date==='2025-01-25').length,1,'January 25 reference week is plotted');
    const plotted=[];
    for(const segment of segments) {
      const start=await segment.getAttribute('data-start'),end=await segment.getAttribute('data-end');
      const rows=group.points.filter(p=>p.date>=start&&p.date<=end);
      rows.slice(1).forEach((p,i)=>assert.equal(stamp(p.date)-stamp(rows[i].date),7*86400000,'Forecasts are not drawn across missing weeks'));
      plotted.push(...rows.map(p=>p.date));
      check(vertices(await segment.locator('.median').getAttribute('d')),rows.map(p=>[x(p.date),y(p.median)]));
      for(const [level,low,high] of [[50,'q25','q75'],[90,'q05','q95']]) {
        check(vertices(await segment.locator(`.band-${level}`).getAttribute('d')),[...rows.map(p=>[x(p.date),y(p[high])]),...[...rows].reverse().map(p=>[x(p.date),y(p[low])])]);
      }
    }
    assert.deepEqual(plotted,group.points.map(p=>p.date),'Every saved forecast is plotted exactly once');
    const labels=await page.locator('svg text, .subtitle, .controls').evaluateAll(nodes=>nodes.map(el=>({text:el.textContent,r:el.getBoundingClientRect().toJSON()})));
    assert.deepEqual(labels.filter(({r})=>r.left<0||r.top<0||r.right>1240||r.bottom>540),[],'All labels fit');
    assert.deepEqual(labels.flatMap((a,i)=>labels.slice(i+1).filter(b=>a.r.left<b.r.right&&a.r.right>b.r.left&&a.r.top<b.r.bottom&&a.r.bottom>b.r.top).map(b=>[a.text,b.text])),[],'Labels do not overlap');
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),1240);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight),540);
    await page.screenshot({path:join(artifacts,`state-${state}.png`)});
  }
  await page.locator('#back-button').click();
  await page.waitForFunction(()=>{const o=Number(getComputedStyle(document.getElementById('horizon-2')).opacity);return o>.1&&o<.9;});
  assert.equal(await page.locator('#truth-line').getAttribute('d'),truthPath,'Truth does not move during transitions');
  await page.screenshot({path:join(artifacts,'transition.png')});
  await settled(3);
  await page.locator('#next-button').click();
  await settled(4);
  await page.locator('#state-select').selectOption('1');
  await settled(1);
  await page.evaluate(()=>document.activeElement.blur());
  await page.keyboard.press('ArrowRight');
  await settled(2);
  await page.keyboard.press('ArrowLeft');
  await settled(1);
  await page.locator('#state-select').selectOption('4');
  await page.locator('#state-select').selectOption('2');
  await settled(2);
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.locator('#next-button').click();
  await settled(3);
  assert.equal(await page.locator('#horizon-2').evaluate(el=>getComputedStyle(el).transitionDuration),'0s');
  await page.goto(`${url}#state=invalid`);
  await settled(1);
  assert.deepEqual(errors,[]);
  console.log(`Slide ${slide}: all four horizons, dynamic state/DC rWIS, every plotted quantile and observation, continuous weekly coverage, shared axes, label layout, navigation, fades, reduced motion, and offline rendering passed. Screenshots: ${artifacts}`);
} finally {await browser.close();}
