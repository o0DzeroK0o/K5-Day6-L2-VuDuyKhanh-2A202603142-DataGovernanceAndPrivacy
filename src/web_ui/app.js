'use strict';
(() => {
  const steps = ['load', 'process', 'rank', 'review', 'decide'];
  const titles = {load: 'Load', process: 'Process', rank: 'Rank', review: 'Review', decide: 'Decide'};
  const $ = id => document.getElementById(id);
  let run = null, view = 'load', frame = 0, rows = [], dirty = false, busy = false, connected = false, galleryKey = '';
  const closed = r => ['approve', 'edit', 'reject'].includes(r.reviewer_decision);
  const el = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = String(text);
    if (cls) node.className = cls;
    return node;
  };
  const format = (value, digits = 3) => Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : '—';
  const date = value => value ? new Date(value).toLocaleString('vi-VN') : '';
  const imageURL = id => `/api/runs/${run.run_id}/images/${encodeURIComponent(id)}`;
  const finalAction = row => closed(row) ? (row.override_value || row.suggested_action) : 'Chưa chốt';
  function message(text, kind = '') { $('message').textContent = text; $('message').className = kind; }
  function connection(ok) {
    connected = ok;
    $('connection').textContent = ok ? '● Máy chủ đã kết nối' : '● Mất kết nối máy chủ';
    $('connection').classList.toggle('error', !ok);
  }
  function remember(id) { try { localStorage.setItem('qc-web-run', id); } catch {} }
  function recalled() { try { return localStorage.getItem('qc-web-run'); } catch { return null; } }
  async function api(path, payload) {
    let response;
    try {
      response = await fetch(path, payload === undefined ? {cache: 'no-store'} : {
        method: 'POST', headers: {'Content-Type': 'application/json', 'X-QC-Request': 'workspace'},
        body: JSON.stringify(payload)
      });
    } catch {
      connection(false);
      throw new Error('Không kết nối được máy chủ. Khởi động make web rồi bấm Tải lại. Nháp đang nhập vẫn được giữ.');
    }
    connection(true);
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || `Lỗi HTTP ${response.status}`);
    return body;
  }
  function mayDiscard() { return !dirty || window.confirm('Có thay đổi chưa lưu. Bỏ nháp này để tiếp tục?'); }
  function showView(next) {
    if (!steps.includes(next)) return;
    view = next;
    steps.forEach(s => { $('panel-' + s).hidden = s !== view; });
    document.querySelectorAll('#steps button').forEach(b => {
      b.classList.toggle('active', b.dataset.view === view);
      b.setAttribute('aria-current', b.dataset.view === view ? 'step' : 'false');
    });
  }
  function updateControls() {
    document.querySelectorAll('[data-stage]').forEach(button => {
      const stage = button.dataset.stage, index = steps.indexOf(stage);
      button.disabled = busy || !connected || !run || (index > 0 && !run.steps[steps[index - 1]].done)
        || (index < 3 && run.steps[stage].done) || (stage === 'decide' && (dirty || run.steps.decide.done));
    });
    $('new-run').disabled = busy;
    $('runs').disabled = busy;
    $('refresh').disabled = busy;
    $('import-confirmed').disabled = busy || !connected || !run?.steps.rank.done;
    $('save-review').disabled = busy || !connected || !run?.steps.rank.done;
    ['reviewer', 'decision', 'note', 'human-confirmed'].forEach(id => { $(id).disabled = busy; });
    $('override').disabled = busy || !['edit', 'reject'].includes($('decision').value);
    $('prev-frame').disabled = busy || frame === 0;
    $('next-frame').disabled = busy || frame === rows.length - 1;
    document.querySelectorAll('#frame-nav button').forEach(b => { b.disabled = busy; });
  }
  async function action(label, work) {
    if (busy) return;
    busy = true; updateControls(); message(label, 'busy');
    try { await work(); }
    catch (error) { message(error.message, 'error'); }
    finally { busy = false; updateControls(); }
  }
  function tableRow(values) {
    const tr = el('tr');
    values.forEach(value => { const td = el('td'); td.append(value instanceof Node ? value : String(value)); tr.append(td); });
    return tr;
  }
  function badge(value) { return el('span', value, 'badge ' + (value === 'KEEP' ? 'keep' : value === 'HOLD' ? 'hold' : '')); }
  function accept(next) {
    run = next; dirty = false; frame = Math.min(frame, Math.max(run.queue.length - 1, 0));
    rows = structuredClone(run.reviews.length ? run.reviews : run.queue);
    $('reviewer').value = run.reviews.find(r => r.reviewer)?.reviewer || 'Vũ Duy Khanh';
    $('human-confirmed').checked = run.human_confirmed;
    remember(run.run_id); render();
  }
  async function listRuns() {
    const list = await api('/api/runs');
    $('runs').replaceChildren(...list.map(r => {
      const option = el('option', `${date(r.created_at)} · ${r.run_id.slice(0, 6)}${r.decision ? ' · ' + r.decision.status : ''}`);
      option.value = r.run_id; return option;
    }));
    if (run) $('runs').value = run.run_id;
    return list;
  }
  function render() {
    $('run-name').textContent = `Lượt ${run.run_id.slice(0, 8)} · Phiên bản ${run.revision} · ${run.dataset}`;
    $('last-update').textContent = 'Lưu gần nhất: ' + date(run.updated_at);
    $('loaded-count').textContent = run.images.length || '—';
    $('processed-count').textContent = run.features.length || '—';
    $('queue-count').textContent = run.queue.length || '—';
    $('saved-count').textContent = `${run.stats.n_reviewed || 0} / ${run.queue.length || 20}`;
    $('decision-status').textContent = run.decision?.status || 'Chưa chạy';
    steps.forEach(s => {
      const result = run.steps[s];
      $('timing-' + s).textContent = result.done ? `Đã chạy ${date(result.finished_at)} · ${result.runtime_seconds}s` : 'Chưa thực thi';
      const tab = document.querySelector(`#steps [data-view="${s}"]`);
      tab.classList.toggle('done', result.done); tab.querySelector('i').textContent = result.done ? '✓' : '○';
    });
    $('load-result').textContent = run.images.length ? `Đã kiểm manifest và nạp ${run.images.length} ảnh. Có thể chạy Process.` : 'Bấm “Nạp dữ liệu” để máy chủ đọc và kiểm tra bộ ảnh.';
    const nextGalleryKey = run.run_id + ':' + run.images.length;
    if (galleryKey !== nextGalleryKey) $('loaded-gallery').replaceChildren(...run.images.map(r => {
      const figure = el('figure'), img = el('img'); img.src = imageURL(r.image_id); img.alt = r.image_id; img.loading = 'lazy';
      const caption = el('figcaption', r.image_id); caption.append(el('small', `${r.camera_id} · ${r.light} · ${r.split}`));
      figure.append(img, caption); return figure;
    }));
    galleryKey = nextGalleryKey;
    $('features-table').replaceChildren(...run.features.map(r => tableRow([r.image_id, `${r.camera_id} / ${r.light}`,
      format(r.sharpness, 1), format(r.mean, 1), format(r.roi_saturation), format(r.blockiness), format(r.score, 6), badge(r.raw_action)])));
    $('process-summary').replaceChildren(...(run.features.length ? [
      el('span', `${run.features.length} ảnh · multifeature_v1`),
      el('span', `${run.features.filter(r => r.split === 'eval').length} ảnh eval`),
      el('span', 'Seed 42 · tham số đã khóa')
    ] : []));
    $('rank-table').replaceChildren(...run.queue.map((r, index) => {
      const link = el('button', r.item_id, 'rank-link');
      link.onclick = () => { frame = index; renderFrame(); showView('review'); };
      return tableRow([r.rank, link, format(r.score, 6), r.reason, badge(r.suggested_action)]);
    }));
    $('review-unavailable').hidden = run.steps.rank.done;
    $('review-workspace').hidden = !run.steps.rank.done;
    renderFrame(); renderReviewStatus(); renderDecision();
    $('downloads').replaceChildren(...run.downloads.map(name => {
      const a = el('a', name); a.href = `/api/runs/${run.run_id}/files/${name}`; a.download = name; return a;
    }));
    $('history').replaceChildren(...run.history.map(h => el('li', `v${h.revision} · ${titles[h.stage]} · ${date(h.at)} · ${h.runtime_seconds}s`)));
    $('audit').replaceChildren(...run.audit.map(e => tableRow([date(e.ts), `${e.actor} · ${e.action}`, e.item_id,
      `${e.before ?? '—'} → ${e.after ?? '—'}`, e.reason])));
    showView(view); updateControls();
  }
  function renderReviewStatus() {
    const n = rows.filter(closed).length;
    $('review-progress').textContent = `${n} / ${rows.length || 20} đã quyết định`;
    $('review-meter').max = rows.length || 20; $('review-meter').value = n;
    $('save-state').textContent = dirty ? 'Có thay đổi chưa lưu · cần lưu trước Decide' : !run.steps.review.done ? 'Chưa lưu review' :
      run.human_confirmed ? (run.review_source === 'confirmed_cvat' ? 'Đã lưu · xác nhận CVAT được kiểm chứng' : 'Đã lưu · có xác nhận trực tiếp') : 'Đã lưu · chờ xác nhận trực tiếp';
    $('frame-nav').replaceChildren(...rows.map((r, index) => {
      const button = el('button', String(index + 1).padStart(2, '0'), `${closed(r) ? 'closed ' : ''}${index === frame ? 'selected' : ''}`);
      button.title = `${r.item_id} · ${finalAction(r)}`; button.setAttribute('aria-label', `Frame ${index + 1}: ${r.item_id}`);
      button.setAttribute('aria-pressed', index === frame ? 'true' : 'false');
      button.onclick = () => { frame = index; renderFrame(); renderReviewStatus(); updateControls(); };
      return button;
    }));
    $('frame-result').textContent = rows[frame] ? `Kết luận: ${finalAction(rows[frame])}` : '';
    if (dirty) {
      $('decision-empty').hidden = false;
      $('decision-empty').textContent = 'Có thay đổi review chưa lưu. Lưu Review rồi chạy Decide cho kết quả mới.';
      $('decision-result').hidden = true;
    }
    updateControls();
  }
  function renderFrame() {
    const row = rows[frame]; if (!row) return;
    $('image-title').textContent = `${frame + 1} / ${rows.length} · ${row.item_id}`;
    $('review-image').src = imageURL(row.item_id); $('review-image').alt = row.item_id;
    const tag = badge(row.suggested_action); tag.id = 'suggested-action'; $('suggested-action').replaceWith(tag);
    $('decision').value = row.reviewer_decision; $('override').value = row.override_value; $('note').value = row.review_note;
    const feature = run.features.find(r => r.image_id === row.item_id) || {};
    $('image-signals').replaceChildren(...[['Score', format(row.score, 6)], ['Camera', feature.camera_id || '—'],
      ['Ánh sáng', row.slice], ['Tín hiệu', feature.pred_defect_type || '—']].map(([label, value]) => {
        const div = el('div'); div.append(el('span', label), el('b', value)); return div;
      }));
    renderReviewStatus();
  }
  function edit() {
    dirty = true;
    $('human-confirmed').checked = false;
    renderReviewStatus();
    message('Nháp đã đổi. Lưu lên máy chủ khi xong; xác nhận trực tiếp cần áp dụng cho các quyết định mới.');
  }
  function renderDecision() {
    const d = run.decision;
    $('decision-empty').hidden = Boolean(d);
    $('decision-empty').textContent = 'Lưu Review rồi bấm “Chạy Decide”.';
    $('decision-result').hidden = !d; $('decision-result').replaceChildren();
    if (!d) return;
    const card = el('div', undefined, 'decision-card ' + d.status.toLowerCase());
    const left = el('div'); left.append(el('span', 'QUYẾT ĐỊNH BATCH', 'eyebrow'), el('div', d.status, 'status'), el('code', d.reason_code));
    const right = el('div'); right.append(el('h3', d.reason_code === 'HUMAN_REVIEW_REQUIRED' ? 'Cần xác nhận trực tiếp toàn bộ queue.' : d.reason), el('p', `Người chịu trách nhiệm: ${d.owner}`));
    const nums = el('div', undefined, 'decision-numbers');
    for (const [label, n] of [['Review trực tiếp', `${run.stats.n_human_reviewed} / ${run.queue.length}`],
      ['RECAPTURE trong queue', rows.filter(r => finalAction(r) === 'RECAPTURE').length],
      ['KEEP trong queue', rows.filter(r => finalAction(r) === 'KEEP').length]]) {
      const div = el('div'); div.append(el('b', n), el('span', label)); nums.append(div);
    }
    right.append(nums, el('p', 'Phạm vi xác nhận: 20 frame trong queue. Mở file kết quả bên dưới để đối chiếu từng ảnh.'));
    card.append(left, right); $('decision-result').append(card);
  }
  async function execute(stage, extra = {}) {
    await action(`Đang thực thi ${titles[stage]} trên máy chủ…`, async () => {
      const next = await api(`/api/runs/${run.run_id}/steps/${stage}`, {revision: run.revision, ...extra});
      accept(next);
      message(`${titles[stage]} hoàn tất · đã lưu phiên bản ${run.revision} trên máy chủ.`);
      await listRuns();
    });
  }
  document.querySelectorAll('[data-view]').forEach(b => { b.onclick = () => showView(b.dataset.view); });
  document.querySelectorAll('[data-stage]').forEach(b => { b.onclick = () => execute(b.dataset.stage); });
  $('new-run').onclick = () => {
    if (!mayDiscard()) return;
    action('Đang tạo lượt chạy…', async () => {
      accept(await api('/api/runs', {})); showView('load'); await listRuns(); message('Lượt mới đã tạo. Bấm Nạp dữ liệu để bắt đầu.');
    });
  };
  $('runs').onchange = async () => {
    const id = $('runs').value;
    if (!mayDiscard()) { $('runs').value = run.run_id; return; }
    await action('Đang mở lượt chạy…', async () => { accept(await api('/api/runs/' + id)); message('Đã mở kết quả đã lưu trên máy chủ.'); });
    if (run) $('runs').value = run.run_id;
  };
  $('refresh').onclick = () => {
    if (!mayDiscard()) return;
    if (!run) return initialize();
    action('Đang tải lại dữ liệu…', async () => { accept(await api('/api/runs/' + run.run_id)); await listRuns(); message('Đã tải phiên bản mới nhất từ máy chủ.'); });
  };
  $('decision').onchange = () => {
    rows[frame].reviewer_decision = $('decision').value;
    if (!['edit', 'reject'].includes($('decision').value)) { rows[frame].override_value = ''; $('override').value = ''; }
    edit();
  };
  $('override').onchange = () => { rows[frame].override_value = $('override').value; edit(); };
  $('note').oninput = () => { rows[frame].review_note = $('note').value; edit(); };
  $('reviewer').oninput = edit;
  $('human-confirmed').onchange = () => { dirty = true; renderReviewStatus(); };
  $('prev-frame').onclick = () => { frame = Math.max(0, frame - 1); renderFrame(); };
  $('next-frame').onclick = () => { frame = Math.min(rows.length - 1, frame + 1); renderFrame(); };
  $('save-review').onclick = () => {
    if (!$('reviewer').value.trim()) { message('Nhập tên người review trước khi lưu.', 'error'); $('reviewer').focus(); return; }
    const invalid = rows.findIndex(r => ['edit', 'reject'].includes(r.reviewer_decision) && (!['KEEP', 'RECAPTURE'].includes(r.override_value) || !r.review_note.trim()));
    if (invalid >= 0) { frame = invalid; renderFrame(); message(`Frame ${frame + 1}: sửa/từ chối cần hành động thay thế và nhận xét.`, 'error'); return; }
    execute('review', {reviewer: $('reviewer').value.trim(), human_confirmed: $('human-confirmed').checked,
      rows: rows.map(r => ({item_id: r.item_id, reviewer_decision: r.reviewer_decision, override_value: r.override_value, review_note: r.review_note}))});
  };
  $('import-confirmed').onclick = () => { if (mayDiscard()) execute('review', {source: 'confirmed'}); };
  $('zoom-image').onclick = () => {
    $('large-image').src = $('review-image').src; $('large-image').alt = $('review-image').alt; $('image-dialog').showModal();
  };
  $('close-image').onclick = () => $('image-dialog').close();
  addEventListener('beforeunload', event => { if (dirty || busy) { event.preventDefault(); event.returnValue = ''; } });
  async function initialize() {
    await action('Đang kết nối tới máy chủ…', async () => {
      const list = await listRuns(), selected = list.find(r => r.run_id === recalled()) || list[0];
      accept(selected ? await api('/api/runs/' + selected.run_id) : await api('/api/runs', {}));
      await listRuns(); showView(steps.find(s => !run.steps[s].done) || 'decide');
      message('Đã kết nối. Các nút thực thi gọi pipeline Python và lưu kết quả trên máy chủ.');
    });
  }
  initialize();
})();
