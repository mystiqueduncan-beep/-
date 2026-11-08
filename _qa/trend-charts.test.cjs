'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync(require('node:path').join(__dirname,'../assets/trend-charts.js'),'utf8');
function run({reduce=false,fail=false,missing=false}={}){
 const classes=new Set();let callback,change,disconnected=0,timer;
 const chart={classList:{add:c=>classes.add(c),remove:c=>classes.delete(c)}};
 const window={matchMedia:()=>({matches:reduce,addEventListener:(_,cb)=>change=cb}),addEventListener(){},setTimeout:cb=>timer=cb};
 class Observer{constructor(cb){if(fail)throw Error('unsupported');callback=cb;}observe(){}disconnect(){disconnected++;}}
 if(!missing)window.IntersectionObserver=Observer;
 vm.runInNewContext(source,{window,document:{querySelector:()=>chart},IntersectionObserver:Observer});
 return {classes,enter:()=>callback([{isIntersecting:true}]),reduce:()=>change({matches:true}),finish:()=>timer(),get disconnected(){return disconnected}};
}
test('reduced motion and missing/failed observers leave static content complete',()=>{
 for(const opts of [{reduce:true},{fail:true},{missing:true}])assert.equal(run(opts).classes.size,0);
});
test('first entry disconnects observer and animation completes with no hiding class',()=>{
 const h=run();h.enter();assert.ok(h.classes.has('is-entering'));assert.equal(h.disconnected,1);h.finish();assert.equal(h.classes.size,0);
});
test('changing to reduced motion immediately finishes an active entrance',()=>{
 const h=run();h.enter();h.reduce();assert.equal(h.classes.size,0);
});
