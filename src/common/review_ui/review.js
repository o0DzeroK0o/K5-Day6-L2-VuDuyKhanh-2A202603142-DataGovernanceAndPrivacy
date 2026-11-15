'use strict';
const ROWS = JSON.parse(document.getElementById('queue-data').textContent);
const COLS = ['rank','item_id','score','reason','suggested_action','slice','evidence_path','reviewer','reviewer_decision','override_value','review_note','reviewed_at'];
const EDITABLE = ['reviewer','reviewer_decision','override_value','review_note','reviewed_at'];
const ALLOWED = ['', 'approve','reject','edit','escalate','skip'];
const CLOSED = ['approve','reject','edit'];
const cards = [...document.querySelectorAll('.card')];
const $ = id => document.getElementById(id);
let state = ROWS.map(row => Object.fromEntries(EDITABLE.map(key => [key, row[key] || ''])));
let lastIndex = -1;
function message(text, error=false) { $('message').textContent = text; $('message').className = error ? 'error' : ''; }
function isDone(row) { return CLOSED.includes(row.reviewer_decision); }
function isEdit(row) { return ['edit','reject'].includes(row.reviewer_decision); }
function syncControls() {
  cards.forEach((card,i) => {
    card.querySelector('.dec').value = state[i].reviewer_decision;
    card.querySelector('.ov').value = state[i].override_value;
    card.querySelector('.note').value = state[i].review_note;
  });
}
function chooseOwner() {
  const owners = [...new Set(state.map(r=>r.reviewer).filter(Boolean))];
  $('reviewer').value = owners.length === 1 ? owners[0] : '';
}
function refresh() {
  let done=0, edits=0, visible=0;
  const query=$('search').value.trim().toLocaleLowerCase('vi');
  const filter=$('filter').value;
  cards.forEach((card,i) => {
    const row=state[i], closed=isDone(row), changed=isEdit(row);
    done+=Number(closed); edits+=Number(changed);
    card.dataset.done=String(closed);
    const action=changed && row.override_value ? row.override_value : ROWS[i].suggested_action;
    card.querySelector('.action').textContent=action || '—';
    card.querySelector('.action').classList.toggle('keep',action==='KEEP');
    card.querySelector('.ov').disabled=!changed;
    card.querySelector('.card-state').textContent=closed ? (changed ? '● Đã quyết định · có override' : '● Đã quyết định') : row.reviewer_decision==='escalate' ? '◌ Cần xác minh thêm' : '◌ Cần xem tiếp';
    const match=(!query || [ROWS[i].item_id, ROWS[i].reason, ROWS[i].slice, row.review_note].join(' ').toLocaleLowerCase('vi').includes(query)) &&
      (filter==='all' || filter==='pending' && !closed || filter==='done' && closed || filter==='edit' && changed || filter===row.reviewer_decision);
    card.hidden=!match; visible+=Number(match);
  });
  $('done-count').textContent=done; $('edit-count').textContent=edits; $('pending-count').textContent=ROWS.length-done;
  $('progress').value=done; $('progress-text').textContent=`${done} / ${ROWS.length} đã quyết định`;
  $('visible-count').textContent=`${visible} / ${ROWS.length} frame`;
  $('empty').hidden=visible>0;
}
function saveDraft() {
  try {
    localStorage.setItem(DRAFT_KEY,JSON.stringify({state,reviewer:$('reviewer').value}));
    $('draft-status').textContent='Đã lưu nháp trên trình duyệt';
  } catch (_) { $('draft-status').textContent='Không lưu được nháp. Hãy xuất CSV trước khi đóng.'; }
}
function rowProblem(row) {
  if (!ALLOWED.includes(row.reviewer_decision)) return 'Quyết định không hợp lệ.';
  if (isEdit(row) && (!row.override_value.trim() || !row.review_note.trim())) return 'Sửa hoặc từ chối cần giá trị thay thế và nhận xét.';
  if (isEdit(row) && ROWS.every(r=>['KEEP','RECAPTURE'].includes(r.suggested_action)) && !['KEEP','RECAPTURE'].includes(row.override_value)) return 'Hành động thay thế phải là KEEP hoặc RECAPTURE.';
  if (!isEdit(row) && row.override_value) return 'Chỉ sửa hoặc từ chối mới được có override.';
  return '';
}
function csvEscape(value) {
  const s=String(value ?? '');
  return /[",\r\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s;
}
function parseCsv(text) {
  text=text.replace(/^\uFEFF/,'');
  const rows=[]; let row=[],cell='',quoted=false,ended=false;
  const pushCell=()=>{row.push(cell);cell='';ended=false;};
  const pushRow=()=>{pushCell();rows.push(row);row=[];};
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(quoted){if(c==='"'){if(text[i+1]==='"'){cell+='"';i++;}else{quoted=false;ended=true;}}else cell+=c;}
    else if(c==='"'){if(cell || ended)throw Error('CSV có dấu ngoặc kép không hợp lệ.');quoted=true;}
    else if(c===',')pushCell();
    else if(c==='\n' || c==='\r'){if(c==='\r' && text[i+1]==='\n')i++;pushRow();}
    else {if(ended)throw Error('CSV có ký tự sau dấu ngoặc kép.');cell+=c;}
  }
  if(quoted)throw Error('CSV thiếu dấu ngoặc kép đóng.');
  if(cell || row.length || ended)pushRow();
  if(!rows.length)throw Error('CSV rỗng.');
  const headers=rows.shift();
  if(new Set(headers).size!==headers.length || COLS.some(c=>!headers.includes(c)))throw Error('CSV thiếu cột bắt buộc hoặc trùng tên cột.');
  return rows.map(row=>{
    if(row.length!==headers.length)throw Error('CSV có dòng lệch số cột.');
    return Object.fromEntries(headers.map((key,i)=>[key,row[i]]));
  });
}
function validateImport(entries) {
  const byId=new Map(entries.map(row=>[row.item_id,row]));
  if(entries.length!==ROWS.length || byId.size!==ROWS.length)throw Error('CSV phải chứa đúng mỗi frame một lần, đủ toàn bộ queue.');
  return ROWS.map(original=>{
    const row=byId.get(original.item_id);
    if(!row || COLS.filter(k=>!EDITABLE.includes(k)).some(k=>(row[k]||'')!==(original[k]||'')))throw Error('CSV khác queue hiện tại: mã ảnh, điểm hoặc thông tin gốc đã thay đổi.');
    const issue=rowProblem(row);
    if(issue)throw Error(`${row.item_id}: ${issue}`);
    if(row.reviewer_decision && !row.reviewer.trim())throw Error(`${row.item_id}: thiếu tên người review.`);
    return Object.fromEntries(EDITABLE.map(k=>[k,row[k]]));
  });
}
function exportCsv() {
  const reviewer=$('reviewer').value.trim();
  if(!reviewer){message('Nhập họ và tên người review trước khi xuất CSV.',true);$('reviewer').focus();return;}
  for(let i=0;i<state.length;i++){
    const issue=rowProblem(state[i]);
    if(issue){$('filter').value='all';$('search').value='';refresh();cards[i].scrollIntoView({block:'center'});cards[i].querySelector('.ov').focus();message(`${ROWS[i].item_id}: ${issue}`,true);return;}
  }
  const now=new Date().toISOString();
  const exported=ROWS.map((row,i)=>{
    const review={...state[i]};
    const active=Boolean(review.reviewer_decision);
    review.reviewed_at=active ? (review.reviewed_at && review.reviewer===reviewer ? review.reviewed_at : now) : '';
    review.reviewer=active ? reviewer : '';
    state[i]=review;
    return {...row,...review};
  });
  const text=COLS.join(',')+'\n'+exported.map(row=>COLS.map(k=>csvEscape(row[k])).join(',')).join('\n')+'\n';
  const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download='review_queue_reviewed.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  saveDraft();
  const pending=state.filter(r=>!isDone(r)).length;
  message(`Đã xuất ${ROWS.length} frame. ${pending ? `Còn ${pending} frame chưa hoàn tất.` : 'Đã quyết định đủ queue.'} Chép CSV vào thư mục output rồi chạy lại pipeline để cập nhật audit và decision.`);
}
cards.forEach((card,i)=>{
  for(const eventName of ['input','change'])card.addEventListener(eventName,event=>{
    if(!event.target.matches('.dec,.ov,.note'))return;
    state[i]={...state[i],reviewer_decision:card.querySelector('.dec').value,override_value:card.querySelector('.ov').value,review_note:card.querySelector('.note').value,reviewed_at:''};
    if(!isEdit(state[i])){state[i].override_value='';card.querySelector('.ov').value='';}
    lastIndex=i;refresh();saveDraft();
  });
  card.querySelectorAll('.zoom').forEach(button=>button.addEventListener('click',()=>{
    const image=button.querySelector('img');$('large-image').src=image.src;$('large-image').alt=image.alt;
    $('image-caption').textContent=`${ROWS[i].rank} / ${ROWS.length} · ${image.alt}`;$('image-dialog').showModal();lastIndex=i;
  }));
});
$('close-image').addEventListener('click',()=>$('image-dialog').close());
$('image-dialog').addEventListener('click',e=>{if(e.target===$('image-dialog'))$('image-dialog').close();});
$('reviewer').addEventListener('input',saveDraft);
$('search').addEventListener('input',refresh);$('filter').addEventListener('change',refresh);
$('next').addEventListener('click',()=>{
  const indexes=state.map((_,i)=>(lastIndex+1+i)%state.length);
  const i=indexes.find(i=>!isDone(state[i]));
  if(i===undefined){message('Đã quyết định đủ toàn bộ frame.');return;}
  lastIndex=i;$('search').value='';$('filter').value='pending';refresh();cards[i].scrollIntoView({block:'center'});cards[i].querySelector('.dec').focus();
});
$('export').addEventListener('click',exportCsv);
$('import').addEventListener('click',()=>$('csv-file').click());
$('csv-file').addEventListener('change',async()=>{
  const file=$('csv-file').files[0];if(!file)return;
  try{const incoming=validateImport(parseCsv(await file.text()));state=incoming;chooseOwner();syncControls();refresh();saveDraft();message(`Đã nhập đủ ${state.length} frame. Điểm và thông tin gốc khớp queue.`);}
  catch(e){message(e.message,true);}
  finally{$('csv-file').value='';}
});
$('reset').addEventListener('click',()=>{
  if(!confirm('Bỏ các sửa đổi trên trình duyệt và trở về dữ liệu gốc của trang này?'))return;
  state=ROWS.map(row=>Object.fromEntries(EDITABLE.map(k=>[k,row[k]||''])));
  chooseOwner();syncControls();refresh();saveDraft();message('Đã trở về dữ liệu gốc của trang.');
});
chooseOwner();
try{
  const draft=JSON.parse(localStorage.getItem(DRAFT_KEY)||'null');
  if(draft){
    if(!Array.isArray(draft.state) || draft.state.length!==ROWS.length || draft.state.some(r=>EDITABLE.some(k=>typeof r[k]!=='string') || !ALLOWED.includes(r.reviewer_decision)) || typeof draft.reviewer!=='string')throw Error('Invalid draft');
    state=draft.state;$('reviewer').value=draft.reviewer;$('draft-status').textContent='Đã khôi phục bản nháp trên trình duyệt';
  }
}catch(_){$('draft-status').textContent='Không đọc được bản nháp. Đang dùng dữ liệu gốc.';}
syncControls();refresh();
