import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {runInNewContext} from 'node:vm';

for(const file of ['src/slide-25.html','docs/slide-25.html']) {
  test(`${file}: playback uses the first frame as its time origin`,async()=>{
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
    frames.shift()(150);
    assert.equal(progress[1],.5);
    assert.equal(completed,0);
    frames.shift()(250);
    assert.equal(progress[2],1);
    assert.equal(completed,1);
    assert.equal(frames.length,0);
  });
}
