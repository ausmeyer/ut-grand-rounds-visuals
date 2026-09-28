import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {runInNewContext} from 'node:vm';

for(const file of ['src/slide-25.html','docs/slide-25.html']) {
  test(`${file}: stage 2 finishes at the displayed scenario's minimum`,async()=>{
    const html=await readFile(new URL(`../${file}`,import.meta.url),'utf8');
    const data=JSON.parse(await readFile(new URL('../data/slide-25/slide-25.json',import.meta.url),'utf8'));
    const setup=html.match(/    const examples =[\s\S]*?(?=    const BX =)/)[0];
    const view=html.match(/if\(value<=2\) \{([\s\S]*?)\n      \} else if\(value===3/)[1];
    const remaining=data.scenarios[0].remaining;
    const best=remaining.indexOf(Math.min(...remaining));
    for(const [play,reducedMotion] of [[true,false],[false,false],[true,true]]) {
      const dates=[];
      runInNewContext(setup+view,{
        DATA:{...data,best_index:0}, // The scenario minimum must not use the pooled mean's index.
        value:2,play,reducedMotion,
        samples:()=>{},dc:[{style:{}}],
        renderDate:index=>dates.push(index),
        animate:(duration,tick,done)=>{ for(const p of [0,.5,1]) tick(p); done(); },
      });
      assert.equal(dates.at(-1),best,`play=${play}, reducedMotion=${reducedMotion}`);
      assert.equal(remaining[dates.at(-1)],Math.min(...remaining));
    }
  });

  test(`${file}: playback progress stays between zero and one`,async()=>{
    const html=await readFile(new URL(`../${file}`,import.meta.url),'utf8');
    const animate=html.match(/    function animate\([\s\S]*?(?=    function announce\()/)[0];
    const frames=[], progress=[];
    let completed=0;
    const context={
      performance:{now:()=>105},
      requestAnimationFrame:callback=>frames.push(callback),
      animation:0,
      announce:()=>{},
    };
    runInNewContext(animate,context);
    context.animate(100,p=>progress.push(p),()=>completed++);
    // A browser's frame timestamp can precede performance.now() at startup.
    frames.shift()(100);
    assert.equal(progress[0],0);
    frames.shift()(155);
    assert.equal(progress[1],.5);
    assert.equal(completed,0);
    frames.shift()(250);
    assert.equal(progress[2],1);
    assert.equal(completed,1);
    assert.equal(frames.length,0);
  });
}
