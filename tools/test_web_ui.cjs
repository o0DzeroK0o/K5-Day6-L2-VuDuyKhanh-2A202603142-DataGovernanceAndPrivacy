/* Execute all five live stages in Chromium. Never manufacture a personal sign-off. */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
(async () => {
  let server, browser;
  let base = process.env.WEB_BASE_URL;
  const directory = process.env.WEB_CAPTURE_DIR || 'out/web-ui-test/captures';
  try {
    if (!base) {
      server = spawn(path.resolve('.venv/bin/python'), ['-m', 'src.web_app', '--port', '0', '--output', 'out/web-ui-test/runs'], {stdio: ['ignore', 'pipe', 'pipe']});
      base = await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('Server startup timeout')), 15000);
        server.stdout.on('data', data => { const m = data.toString().match(/http:\/\/127\.0\.0\.1:\d+/); if (m) { clearTimeout(timer); resolve(m[0]); } });
        server.once('error', reject); server.once('exit', code => { clearTimeout(timer); reject(new Error('Server exited ' + code)); });
      });
    }
    const ready = await fetch(base); assert.equal(ready.status, 200);
    await fs.mkdir(directory, {recursive: true});
    browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true});
    const page = await browser.newPage({viewport: {width: 1440, height: 1200}});
    const errors = [], requests = [], external = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('request', req => { if (req.method() === 'POST') requests.push(new URL(req.url()).pathname); if (!req.url().startsWith(base)) external.push(req.url()); });
    page.on('dialog', dialog => dialog.accept());
    await page.goto(base);
    await page.waitForFunction(() => !document.getElementById('new-run').disabled);
    await page.locator('#new-run').click();
    await page.waitForFunction(() => !document.getElementById('run-load').disabled);
    const view = name => page.locator(`#steps [data-view="${name}"]`).click();
    const step = async name => {
      const response = page.waitForResponse(r => r.url().endsWith('/steps/' + name) && r.request().method() === 'POST');
      await page.locator('#run-' + name).click();
      const result = await response;
      assert.equal(result.status(), 200, await result.text());
      await page.waitForFunction(() => !document.getElementById('refresh').disabled);
      return result.json();
    };
    const capture = async name => {
      await page.waitForFunction(() => !document.getElementById('message').classList.contains('busy'));
      await page.evaluate(() => scrollTo(0, 0));
      return page.screenshot({path: path.join(directory, name), fullPage: false});
    };
    await step('load');
    assert.equal(await page.locator('#loaded-count').textContent(), '96');
    assert.equal(await page.locator('#loaded-gallery figure').count(), 96);
    await page.waitForFunction(() => [...document.querySelectorAll('#loaded-gallery img')].slice(0, 18).every(img => img.complete && img.naturalWidth > 0));
    await view('process'); await step('process');
    assert.equal(await page.locator('#features-table tr').count(), 96);
    const rawLink = await page.locator('#downloads a').filter({hasText: /^raw_predictions.csv$/}).getAttribute('href');
    const raw = Buffer.from(await (await fetch(base + rawLink)).arrayBuffer());
    assert.deepEqual(raw, await fs.readFile('reports/evidence/poc/raw_predictions.csv'));
    await view('rank'); let state = await step('rank');
    assert.equal(await page.locator('#rank-table tr').count(), 20);
    const runId = state.run_id;
    await view('review');
    const visited = [];
    for (let i = 0; i < 20; i++) {
      await page.locator('#frame-nav button').nth(i).click();
      await page.waitForFunction(() => { const img = document.getElementById('review-image'); return img.complete && img.naturalWidth > 0; });
      const title = await page.locator('#image-title').textContent();
      assert.ok(title.includes(state.queue[i].item_id)); visited.push(state.queue[i].item_id);
    }
    await page.locator('#zoom-image').click(); assert.equal(await page.locator('#image-dialog').isVisible(), true);
    await page.keyboard.press('Escape'); assert.equal(await page.locator('#image-dialog').isVisible(), false);
    // Incomplete edits must be rejected before sending, and retained in the form.
    await page.locator('#reviewer').fill('Người kiểm thử giao diện');
    await page.locator('#decision').selectOption('edit');
    await page.locator('#save-review').click();
    assert.match(await page.locator('#message').textContent(), /cần hành động thay thế/);
    assert.equal(await page.locator('#decision').inputValue(), 'edit');
    // Save a partial, unconfirmed review and verify the actual HOLD policy.
    await page.locator('#decision').selectOption('approve');
    await page.locator('#note').fill('Kiểm thử lưu nháp chưa xác nhận.');
    let response = page.waitForResponse(r => r.url().endsWith('/steps/review'));
    await page.locator('#save-review').click(); assert.equal((await response).status(), 200);
    await page.waitForFunction(() => !document.getElementById('refresh').disabled);
    await view('decide'); state = await step('decide');
    assert.equal(state.decision.reason_code, 'HUMAN_REVIEW_REQUIRED');
    assert.equal(state.stats.n_human_reviewed, 0);
    // Restore only the user's already verified attestation for this exact queue.
    await view('review'); response = page.waitForResponse(r => r.url().endsWith('/steps/review'));
    await page.locator('#import-confirmed').click(); assert.equal((await response).status(), 200);
    await page.waitForFunction(() => !document.getElementById('refresh').disabled);
    assert.equal(await page.locator('#human-confirmed').isChecked(), true);
    assert.equal(await page.locator('#reviewer').inputValue(), 'Vũ Duy Khanh');
    const imported = await (await fetch(base + '/api/runs/' + runId)).json();
    assert.equal(imported.stats.n_human_reviewed, 20);
    // A stale tab cannot replace the newly saved review.
    const stale = await fetch(base + '/api/runs/' + runId + '/steps/review', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-QC-Request': 'workspace'},
      body: JSON.stringify({revision: 3, source: 'confirmed'})
    }); assert.equal(stale.status, 409);
    // Editing revokes the form's inherited checkbox and blocks Decide until save.
    await page.locator('#note').fill('Nháp thử chưa lưu.');
    assert.equal(await page.locator('#human-confirmed').isChecked(), false);
    await view('decide'); assert.equal(await page.locator('#run-decide').isDisabled(), true);
    assert.equal(await page.locator('#decision-result').isVisible(), false);
    await view('review');
    await page.route('**/steps/review', route => route.fulfill({status: 409, contentType: 'application/json', body: JSON.stringify({error: 'Phiên bản đã đổi. Tải lại trước khi lưu.'})}), {times: 1});
    await page.locator('#save-review').click();
    await page.waitForFunction(() => document.getElementById('message').classList.contains('error'));
    assert.equal(await page.locator('#note').inputValue(), 'Nháp thử chưa lưu.');
    await page.context().setOffline(true);
    await page.locator('#refresh').click();
    await page.waitForFunction(() => document.getElementById('connection').classList.contains('error'));
    assert.equal(await page.locator('#note').inputValue(), 'Nháp thử chưa lưu.');
    assert.equal(await page.locator('#save-review').isDisabled(), true);
    await page.context().setOffline(false);
    await page.locator('#refresh').click();
    await page.waitForFunction(() => !document.getElementById('refresh').disabled);
    assert.equal(await page.locator('#human-confirmed').isChecked(), true);
    await view('review');
    const overrideIndex = imported.queue.findIndex(r => r.item_id === 'img_19_2');
    await page.locator('#frame-nav button').nth(overrideIndex).click();
    assert.equal(await page.locator('#decision').inputValue(), 'edit');
    assert.equal(await page.locator('#override').inputValue(), 'RECAPTURE');
    await view('decide'); state = await step('decide');
    assert.equal(state.decision.status, 'REWORK'); assert.equal(state.stats.n_human_reviewed, 20);
    // Reload reconstructs the current server state and downloadable artifacts.
    await page.reload(); await page.waitForFunction(() => document.getElementById('decision-status').textContent === 'REWORK');
    assert.match(await page.locator('#run-name').textContent(), new RegExp(runId.slice(0, 8)));
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#downloads a').filter({hasText: /^decision.json$/}).click();
    const download = await downloadPromise; const downloadPath = path.join(directory, 'decision.json');
    await download.saveAs(downloadPath);
    assert.deepEqual(JSON.parse(await fs.readFile(downloadPath, 'utf8')), state.decision);
    assert.deepEqual(Buffer.from(await (await fetch(base + rawLink)).arrayBuffer()), raw);
    // Mobile: every stage remains usable without horizontal document overflow.
    await page.setViewportSize({width: 390, height: 844});
    for (const name of ['load', 'process', 'rank', 'review', 'decide']) {
      await view(name); assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, name);
    }
    await view('review'); await page.locator('#frame-nav button').nth(19).click();
    assert.match(await page.locator('#image-title').textContent(), /20 \/ 20/);
    assert.deepEqual(errors, []); assert.deepEqual(external, []);
    for (const stage of ['load', 'process', 'rank', 'review', 'decide']) assert.ok(requests.some(url => url.endsWith('/steps/' + stage)));
    // Capture a separate clean run. Test drafts and expected HOLD/conflicts
    // remain in the test run, outside the delivered demonstration's audit.
    await page.setViewportSize({width: 1440, height: 1200});
    await page.locator('#new-run').click();
    await page.waitForFunction(() => !document.getElementById('run-load').disabled);
    await step('load');
    await page.waitForFunction(() => [...document.querySelectorAll('#loaded-gallery img')].slice(0, 18).every(img => img.complete && img.naturalWidth > 0));
    await capture('01-load.png');
    await view('process'); await step('process'); await capture('02-process.png');
    await view('rank'); state = await step('rank'); await capture('03-rank.png');
    const finalRunId = state.run_id;
    await view('review');
    for (let i = 0; i < 20; i++) {
      await page.locator('#frame-nav button').nth(i).click();
      await page.waitForFunction(() => { const img = document.getElementById('review-image'); return img.complete && img.naturalWidth > 0; });
      assert.ok((await page.locator('#image-title').textContent()).includes(visited[i]));
    }
    response = page.waitForResponse(r => r.url().endsWith('/steps/review'));
    await page.locator('#import-confirmed').click(); assert.equal((await response).status(), 200);
    await page.waitForFunction(() => !document.getElementById('refresh').disabled);
    await page.locator('#frame-nav button').nth(overrideIndex).click(); await capture('04-review.png');
    await view('decide'); state = await step('decide'); await capture('05-decide.png');
    assert.equal(state.revision, 5); assert.equal(state.decision.status, 'REWORK');
    assert.equal(state.stats.n_human_reviewed, 20);
    assert.equal(state.audit.filter(e => e.action.startsWith('review:')).length, 20);
    await page.setViewportSize({width: 390, height: 844});
    await view('review'); await page.locator('#frame-nav button').nth(19).click();
    await page.screenshot({path: path.join(directory, '06-mobile.png'), fullPage: true});
    assert.deepEqual(errors, []); assert.deepEqual(external, []);
    // Keep self-contained output copies alongside captures so evidence survives out/ cleanup.
    for (const file of ['decision.json', 'workflow.json', 'raw_predictions.csv', 'review_queue_reviewed.csv', 'ranked_review.csv',
      'item_decisions.csv', 'audit_log.jsonl', 'decision_log.csv', 'review_confirmation.json', 'run_info.json']) {
      const result = await fetch(`${base}/api/runs/${finalRunId}/files/${file}`); assert.equal(result.status, 200);
      await fs.writeFile(path.join(directory, file), Buffer.from(await result.arrayBuffer()));
    }
    const report = {tested_at: new Date().toISOString(), browser: await browser.version(), base_url: base,
      run_id: finalRunId, revision: state.revision, test_run_id: runId, passed: true, steps: state.history,
      visited_frames: visited, final_status: state.decision.status, human_reviewed: state.stats.n_human_reviewed,
      checks: ['real pixel processing matches frozen predictions', 'all 20 frames opened', 'image zoom',
        'invalid edit retained and rejected', 'partial unconfirmed review produces HOLD', 'verified CVAT confirmation import',
        'stale revision rejected', 'editing clears confirmation and blocks Decide', 'server state restored after reload',
        'draft survives HTTP rejection and lost connection',
        'decision download matches server', 'scores unchanged after review', 'five mobile views fit 390px', 'no external requests'],
      javascript_errors: errors, post_requests: requests};
    await fs.writeFile(path.join(directory, 'verification.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report, null, 2));
  } finally {
    if (browser) await browser.close();
    if (server && server.exitCode === null) { server.kill('SIGTERM'); await once(server, 'exit'); }
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
