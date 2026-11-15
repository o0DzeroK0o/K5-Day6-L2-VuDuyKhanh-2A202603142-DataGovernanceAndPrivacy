/* Capture and verify the complete offline deck in Chromium. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('node:fs/promises');
const path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 try {
   await fs.mkdir('demo/slides',{recursive:true});
   await page.goto('file://'+path.resolve('demo/t004_demo.html'));
   assert.equal(await page.locator('section').count(),5);
   assert.equal(await page.locator('img').evaluateAll(imgs=>imgs.every(i=>i.complete && i.naturalWidth>0)),true);
   const sizes=[];
   for(let i=1;i<=5;i++){
     const slide=page.locator('#s'+i);
     await slide.evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
     const size=await slide.evaluate(el=>({id:el.id,height:el.getBoundingClientRect().height,width:el.getBoundingClientRect().width,overflow:document.documentElement.scrollWidth>innerWidth}));
     assert.equal(size.height,1000);assert.equal(size.overflow,false);sizes.push(size);
     await page.waitForFunction(i=>document.getElementById('position').textContent===i+' / 5',i);
     await slide.screenshot({path:`demo/slides/0${i}.png`});
   }
   await page.keyboard.press('Home');
   await page.waitForFunction(()=>document.getElementById('position').textContent==='1 / 5');
   await page.locator('#next').click();
   await page.waitForFunction(()=>document.getElementById('position').textContent==='2 / 5');
   await page.keyboard.press('End');
   await page.waitForFunction(()=>document.getElementById('position').textContent==='5 / 5');
   await page.setViewportSize({width:390,height:844});
   for(let i=1;i<=5;i++){
     await page.locator('#s'+i).evaluate(el=>el.scrollIntoView({block:'start'}));
     assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   }
   const links=await page.locator('a').evaluateAll(links=>links.map(a=>a.getAttribute('href')));
   for(const link of links){assert.ok(!/^https?:/.test(link));await fs.access(path.resolve('demo',link));}
   assert.deepEqual(errors,[]);
   const report={tested_at:new Date().toISOString(),browser:await browser.version(),passed:true,slides:sizes,
     navigation:'Buttons, Home and End passed',mobile:'All five slides fit width 390px',links:links.length,
     images:'All embedded images loaded',javascript_errors:errors};
   await fs.writeFile('reports/demo_verification.json',JSON.stringify(report,null,2)+'\n');
   console.log(JSON.stringify(report,null,2));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
