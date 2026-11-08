'use strict';
// Run: node _qa/trend-charts.browser.cjs (serve repository on localhost:8000).
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {execFileSync}=require('node:child_process');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 for(const file of ['trend.html','mobile-trend.html']){
  const old=execFileSync('git',['show',`origin/main:${file}`],{encoding:'utf8'});
  const current=fs.readFileSync(file,'utf8');
  const circles=s=>s.match(/<circle\b[^>]*>/g);
  assert.deepEqual(circles(current),circles(old),'SVG geometry and colors must be unchanged');
  // Everything following the charts, including sources and resume content, stays unchanged.
  const marker=file==='trend.html'?'<!-- VISUALIZATION 2:':'<!-- SECTION 01-C:';
  assert.equal(current.slice(current.indexOf(marker)),old.slice(old.indexOf(marker)));
  for(const match of old.matchAll(/<p\b[^>]*>([\s\S]*?)<\/p>/g)) assert.ok(current.includes(match[1]),'original analysis preserved');
  for(const width of [320,375,768,1440]){
   const context=await browser.newContext({viewport:{width,height:900},hasTouch:width<768});
   const page=await context.newPage();
   const view=file.startsWith('mobile')?'mobile':'desktop';
   await page.addInitScript(() => { window.firstRuns = 0; document.addEventListener('animationstart', e => { if(e.animationName === 'channel-bar') window.firstRuns++; }); });
   await page.goto(`http://127.0.0.1:8000/${file}?view=${view}`);
   await page.locator('.channel-study').scrollIntoViewIfNeeded();
   await page.waitForTimeout(1000);
   assert.equal(await page.evaluate(()=>window.firstRuns),4,'four bars animate on first entry');
   assert.deepEqual(await page.locator('.channel-value').allTextContents(),['45.2%','42.5%','28.7%','24.4%']);
   assert.deepEqual(await page.locator('.channel-metric > strong').allTextContents(),['45.2%','42.5%']);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`${file} ${width} overflow`);
   const ratios=await page.locator('.channel-fill').evaluateAll(es=>es.map(e=>e.getBoundingClientRect().width/(e.parentElement.clientWidth)*100));
   ratios.forEach((r,i)=>assert.ok(Math.abs(r-[45.2,42.5,28.7,24.4][i])<.2));
   if(width<768) await page.locator('.channel-row').first().tap();
   await page.locator('.channel-row').first().focus();
   await page.keyboard.press('Tab');
   assert.equal(await page.locator('.channel-row:focus').evaluate(e=>getComputedStyle(e).outlineStyle),'solid');
   await page.evaluate(()=>{window.chartRuns=0;document.querySelector('.channel-study').addEventListener('animationstart',()=>window.chartRuns++);scrollTo(0,0)});
   await page.waitForTimeout(100);
   await page.locator('.channel-study').scrollIntoViewIfNeeded();await page.waitForTimeout(900);
   assert.equal(await page.evaluate(()=>window.chartRuns),0,'no repeated entrance');
   assert.ok(await page.locator('.category-donut').evaluate(e=>e.getBoundingClientRect().width>150));
   if([375,1440].includes(width)) await page.locator('.channel-study').screenshot({path:`/workspace/work/qa/${file}-${width}.png`});
   await context.close();
  }
  for(const options of [{javaScriptEnabled:false},{reducedMotion:'reduce'}]){
   const context=await browser.newContext({...options,viewport:{width:file.startsWith('mobile')?375:1440,height:900}});const page=await context.newPage();
   // Without JS, the supplied page remains directly accessible and fully readable.
   await page.goto(`http://127.0.0.1:8000/${file}?view=${file.startsWith('mobile')?'mobile':'desktop'}`);
   await page.locator('.channel-study').scrollIntoViewIfNeeded();
   assert.equal(await page.locator('.channel-fill').first().evaluate(e=>getComputedStyle(e).transform),'none');
   assert.equal(await page.locator('.channel-value').first().evaluate(e=>getComputedStyle(e).opacity),'1');
   await context.close();
  }
 }
 await browser.close();console.log('PASS: both pages, four viewport widths, ratios, immutable SVG/analysis, focus, once-only animation, no-JS and reduced motion');
})().catch(e=>{console.error(e);process.exit(1)});
