/* Real browser checks. Set PLAYWRIGHT_MODULE and CHROMIUM_PATH if not on PATH. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('node:fs/promises');
const path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
 const root=process.cwd(), evidence=path.join(root,'demo/ui'), out=path.join(root,'out/ui-test');
 await fs.mkdir(evidence,{recursive:true});await fs.mkdir(out,{recursive:true});
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const checks=[];const ok=name=>checks.push(name);
 try {
 await page.goto('file://'+path.join(root,'reports/contact_sheet.html'));
 assert.equal(await page.locator('.card').count(),20);assert.equal(await page.locator('#done-count').innerText(),'20');
 assert.equal(await page.locator('#edit-count').innerText(),'2');assert.equal(await page.locator('#reviewer').inputValue(),'Vũ Duy Khanh');
 assert.equal(await page.locator('.imgs img').evaluateAll(imgs=>imgs.every(i=>i.complete && i.naturalWidth>0)),true);
 await page.screenshot({path:path.join(evidence,'01-workspace.png')});ok('20 prefilled decisions, two overrides, all images loaded');
 // Inspect each frame through the visible zoom interaction.
 for(let i=0;i<20;i++){
   await page.locator('.card').nth(i).locator('.zoom').click();
   assert.equal(await page.locator('#image-dialog').evaluate(d=>d.open),true);
   assert.match(await page.locator('#image-caption').innerText(),new RegExp(`^${i+1} / 20`));
   await page.locator('#close-image').click();
 }
 ok('Opened and closed enlarged images for all 20 frames');
 await page.locator('#search').fill('img_23_1');assert.equal(await page.locator('.card:visible').count(),1);
 assert.equal(await page.locator('.card:visible .action').innerText(),'KEEP');
 await page.locator('#search').fill('');await page.locator('#filter').selectOption('edit');
 assert.equal(await page.locator('.card:visible').count(),2);await page.evaluate(()=>scrollTo(0,0));
 await page.screenshot({path:path.join(evidence,'02-overrides.png')});ok('Search KEEP frame and filter both overrides');
 await page.locator('#filter').selectOption('all');
 // Export the exact signed decisions before any test edits.
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export').click()]);
 await download.saveAs(path.join(out,'review_queue_reviewed.csv'));
 assert.equal(await fs.readFile(path.join(out,'review_queue_reviewed.csv'),'utf8'),await fs.readFile(path.join(root,'reports/review_queue.csv'),'utf8'));
 await page.screenshot({path:path.join(evidence,'03-export.png')});ok('Export includes all 20 rows, byte-for-byte equal to confirmed CSV');
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>scrollTo(0,0));
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await page.screenshot({path:path.join(evidence,'04-mobile.png')});ok('390px mobile layout has no horizontal overflow');
 await page.setViewportSize({width:1440,height:1000});
 await page.locator('#reviewer').fill('');await page.locator('#export').click();assert.match(await page.locator('#message').innerText(),/Nhập họ và tên/);
 await page.locator('#reviewer').fill('UI TEST');
 const first=page.locator('.card').first();await first.locator('.dec').selectOption('edit');await page.locator('#export').click();
 assert.match(await page.locator('#message').innerText(),/cần giá trị thay thế/);
 await first.locator('.ov').fill('INVALID');await first.locator('.note').fill('Nhận xét thử');await page.locator('#export').click();assert.match(await page.locator('#message').innerText(),/KEEP hoặc RECAPTURE/);ok('Missing owner, missing override, and invalid T02 action block export');
 await first.locator('.ov').fill('RECAPTURE');const note='Kiểm thử: "lóa", nhận xét\ndòng thứ hai có dấu';await first.locator('.note').fill(note);
 await page.reload();assert.equal(await first.locator('.note').inputValue(),note);assert.equal(await page.locator('#reviewer').inputValue(),'UI TEST');ok('Draft survives reload');
 const [testDownload]=await Promise.all([page.waitForEvent('download'),page.locator('#export').click()]);await testDownload.saveAs(path.join(out,'roundtrip.csv'));
 await page.locator('#csv-file').setInputFiles(path.join(out,'roundtrip.csv'));await page.waitForFunction(()=>document.getElementById('message').textContent.startsWith('Đã nhập'));
 assert.equal(await first.locator('.note').inputValue(),note);ok('CSV round-trip preserves commas, quotes, Unicode, multiline notes');
 const original=await fs.readFile(path.join(root,'reports/review_queue.csv'),'utf8');
 const bad=original.replace('img_13_3','foreign_id');
 await page.locator('#csv-file').setInputFiles({name:'bad.csv',mimeType:'text/csv',buffer:Buffer.from(bad)});
 await page.waitForFunction(()=>document.getElementById('message').classList.contains('error'));
 assert.equal(await first.locator('.note').inputValue(),note);ok('Foreign queue import rejected atomically');
 await first.locator('.dec').selectOption('skip');await page.locator('#next').click();assert.equal(await page.locator('.card:visible').count(),1);
 assert.equal(await first.locator('.ov').inputValue(),'');ok('Changing away from edit clears override; next pending navigation works');
 page.once('dialog',d=>d.accept());await page.locator('#reset').click();await page.locator('#filter').selectOption('all');
 assert.equal(await page.locator('#reviewer').inputValue(),'Vũ Duy Khanh');assert.equal(await page.locator('#done-count').innerText(),'20');ok('Reset restores the original signed queue');
 assert.deepEqual(errors,[]);ok('No browser JavaScript errors');
 const report={tested_at:new Date().toISOString(),browser:await browser.version(),checks,frame_count:20,passed:true,scope:'Browser operation checks; test edits kept in out/ui-test only. Human attestation is recorded separately.'};
 await fs.writeFile(path.join(root,'reports/ui_verification.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report,null,2));
 } finally {await context.close();await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
