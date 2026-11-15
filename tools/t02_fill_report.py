"""Fill answers only; preserve the supplied report's lines, headings and questions.

By default writes a preview, so later human edits are never silently overwritten.
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

import pandas as pd
from tools.t02_cvat_demo import SOURCE

TEMPLATE=Path('tests/assets/group_report_template.md')


def validate_structure(original: str, filled: str):
    a,b=original.splitlines(),filled.splitlines()
    if len(a)!=len(b):
        raise ValueError('report line count changed')
    for old,new in zip(a,b):
        if old.startswith('|'):
            if old.count('|')!=new.count('|'):
                raise ValueError('table columns changed')
            for i,(before,after) in enumerate(zip(old.split('|'),new.split('|'))):
                before=before.strip()
                if before and '_' in before and before != 'G__':
                    import re
                    pattern = '.*'.join(re.escape(v) for v in re.split(r'_{2,}', before))
                    if not re.fullmatch(pattern + ".*", after.strip()):
                        raise ValueError(f'template cell wording changed: {before}')
                elif before and before not in {'G__','higher / lower'}:
                    # Nonempty template cells are retained, allowing answers after them.
                    if before not in after:
                        raise ValueError(f'template table prompt changed: {before}')
        elif old.startswith('- [ ]'):
            if old[6:] not in new:
                raise ValueError('checklist wording changed')
        elif '____' in old:
            # Every fixed fragment around an answer blank must remain in order.
            import re
            pattern='.*'.join(re.escape(v) for v in re.split(r'_{4,}',old))
            if not re.fullmatch(pattern,new):
                raise ValueError(f'question text changed: {old}')
        elif '<track>' in old or 't__' in old or '<file>' in old or 'có / không' in old:
            continue  # Filled command placeholders and yes/no selection.
        elif old!=new:
            raise ValueError(f'non-answer text changed: {old}')


def build_report(root=Path('reports')):
    b=json.loads((root/'metrics_baseline.json').read_text());p=json.loads((root/'metrics_poc.json').read_text())
    summary=json.loads((root/'analysis_summary.json').read_text());verification=json.loads((root/'verification.json').read_text())
    cvat=json.loads((root/'cvat_review_import.json').read_text())
    signed=json.loads((root/'human_review_confirmation.json').read_text())
    bs,ps=summary['runs']['baseline'],summary['runs']['poc'];ci=summary['uncertainty']['results']
    s=TEMPLATE.read_text()
    def replace(old,new):
        nonlocal s
        if old not in s: raise ValueError(f'missing template placeholder: {old}')
        s=s.replace(old,new,1)
    def cell(key,value):
        old=next(x for x in s.splitlines() if x.startswith(f'| {key} |'))
        replace(old,f'| {key} | {value} |')
    def answer(prefix,value):
        old=next(x for x in s.splitlines() if x.startswith(prefix))
        replace(old,old.replace('____',str(value),1))
    cell('Group ID','T004')
    cell('Challenge','T02 · Raw QC Triage: ảnh mờ, lóa, tối và nén JPEG')
    cell('Thành viên (5–6) + vai trò',f'1. {SOURCE}, kiêm toàn bộ vai trò (Lead/Integrator) · 2. Không áp dụng (Data & fixtures) · 3. Không áp dụng (Core algorithm) · 4. Không áp dụng (QA/metric) · 5. Không áp dụng (Review + report) · 6. Không áp dụng; nhóm thực tế **1 người**. Vũ Duy Khanh xác nhận đã trực tiếp review đủ 20 frame và đồng ý kết quả.')
    cell('Git URL','https://github.com/o0DzeroK0o/K5-Day6-L2-VuDuyKhanh-2A202603142-DataGovernanceAndPrivacy (commit/tag hiện cục bộ, chưa push)')
    cell('Tag `demo-180m` (commit)','`demo-180m^{commit}` — xem `git rev-parse demo-180m^{commit}`; tạo thực tế khi hoàn tất demo, không khẳng định đúng phút 180 của lớp.')
    cell('Tag `final-24h` (commit)','`final-24h^{commit}` — xem `git rev-parse final-24h^{commit}`; hash bàn giao sau commit, không khẳng định đúng deadline +24h.')
    cell('Deadline (giờ VN)','11:00 15/11/2026 (Asia/Ho_Chi_Minh; theo thông tin học viên điền).')
    answer('- Ai bị ảnh hưởng','Đội thu thập, người gán nhãn và chủ mô hình: bỏ sót ảnh hỏng gây dữ liệu kém; loại nhầm night/cam_B làm mất coverage và tốn thu lại.')
    answer('- Điểm nghẽn cụ thể','Chỉ review được B=20 trong 40 ảnh eval; một ngưỡng nét toàn ảnh bỏ sót glare cục bộ và nhầm camera mềm.')
    answer('- Đầu vào → đầu ra','images.csv + JPEG + manifest → feature/score → ranked_review.csv → queue/contact sheet → item KEEP/RECAPTURE → decision/audit.')
    answer('- Tiêu chí GO / HOLD / REWORK','HOLD khi chưa đủ người thật review, còn escalation hoặc domain lạ; REWORK nếu còn RECAPTURE; GO khi review đã hoàn tất và không còn yêu cầu thu lại, chỉ trong phạm vi triage. Điểm nội bộ không tự cho phép release.')
    answer('- Giả định của nhóm','Ảnh synthetic CC0 không PII thật; chủ dữ liệu xác nhận chuẩn “dùng được”, ROI và chính sách thu lại. Đưa lên dữ liệu thật cần kiểm tra quyền, retention và mục đích sử dụng.')
    replace('| dev | | | | |','| dev | 56 ảnh / 14 scene | fixtures/t02_raw_qc; synthetic generator seed42 theo manifest | CC0-1.0 | Có |')
    replace('| eval / heldout | | | | |','| eval / heldout | 40 ảnh / 10 scene | cùng fixture; nhãn quan sát nội bộ; nguồn tại annotations/README.md và annotations/internal_eval_labels.csv | CC0-1.0 | Có |')
    answer('- Schema & class mapping','image_id/path/camera_id/light/split; defect_type={none,blur,glare,dark,compression}; is_defect=0 cho none, 1 cho lỗi; severity 0–2 theo nhãn quan sát nội bộ. Xác nhận 20 frame review không chứng nhận toàn bộ 40 nhãn eval; nguồn nhãn tại [annotations/README.md](annotations/README.md), không phải GT giảng viên.')
    answer('- Seed: 42','Dùng split sẵn theo group_id scene trong manifest; không scene nào giao giữa dev và eval; mọi biến thể cùng scene ở cùng split.')
    replace('verified (sha256): có / không','verified (sha256): có')
    answer('- Dữ liệu thật dùng','Không dùng. Kiểm thêm 10 ảnh synthetic T13 256×144, đã có nhãn quan sát nội bộ; chỉ proxy khác track, 0 positive nên không có recall OOD. [OOD](ood_check.csv).')
    answer('- 2–3 references','OpenCV Laplace Operator và SciPy ndimage.convolve, xem 2026-11-14 (URL ở mục 11). Chọn Laplacian vì đo biến thiên cạnh rẻ trên CPU; mode reflect giúp xác định biên convolution tái lập. ROI/JPEG/camera là heuristic nhóm thử trên dev, không quy kết các nguồn chứng minh ngưỡng này.')
    answer('- Sơ đồ data flow','Web HTTP chạy bằng `make web`: Load kiểm input + sha256 → Process tính pixel features → Rank lấy top20 eval → Review lưu quyết định hoặc nhập bản CVAT đã xác nhận → Decide áp policy và tạo decision/audit. Mỗi nút thực thi hàm tương ứng trong src.pipeline qua worker riêng; kết quả và phiên bản giữ trong out/web/. [Hướng dẫn](../docs/HUONG_DAN_CHAY_DEMO_T004.md), [ảnh thực thi](../demo/web/index.html). Evaluator và report chạy riêng, không dùng GT khi xử lý.')
    answer('- Thành phần offline','Không pretrained model, không weights/API. NumPy/Pillow/SciPy; môi trường Python 3.12.16, phiên bản ở requirements-lock.txt. Hash input trong manifest, hash protocol trong protocol_freeze.json.')
    answer('- Trade-offs đã cân nhắc','Max của các tín hiệu giải thích được và chạy CPU; ROI bỏ sky giảm báo nhầm nhưng glare nhẹ chưa cháy trắng vẫn lọt. Camera/light thresholds giảm loại nhầm night/cam_B nhưng cần metadata đúng. 10 OOD synthetic không thay dữ liệu thật.')
    answer('- Baseline (mô tả','Một ngưỡng Laplacian 400, score=400/(400+variance); src.t02_baseline, config đã freeze, commit 6c525dc. Random baseline chỉ thử wiring.')
    answer('- PoC (mô tả','Max score blur/dark/ROI glare/blockiness; ngưỡng theo cam_A/cam_B và day/dusk/night; src.pipeline commit 6c525dc. Ngưỡng chi tiết metric_contract.md; không đổi sau eval.')
    answer('- Cùng budget','Có: cùng 40 ảnh eval, cùng B=20, seed42, tie-break image_id. Review chỉ sửa pred_action; raw score/type dùng chấm không bị thay. Bảng chuẩn đầy đủ do src.compare sinh ở [table1_baseline_vs_poc.md](table1_baseline_vs_poc.md); giữ nguyên bố cục bảng mẫu bên dưới.')
    delta=Decimal(str(ps['recall']))-Decimal(str(bs['recall']))
    replace('| Primary: ______ | ____ | ____ | ____; higher/lower? |',f'| Primary: Defect Recall@B | {bs["recall"]} ({bs["tp"]}/{summary["positive_n"]}) | {ps["recall"]} ({ps["tp"]}/{summary["positive_n"]}) | +{delta} tuyệt đối, nhãn quan sát nội bộ; higher/lower? higher |')
    bn=next(m for m in b['metrics'] if m['name']=='False alarm in top-B' and m['slice']=='light=night')
    pn=next(m for m in p['metrics'] if m['name']=='False alarm in top-B' and m['slice']=='light=night')
    replace('| Hard-slice: ______ | ____ | ____ | ____; N=__ |',f'| Hard-slice: False alarm night | {bn["value"]} ({bn["numerator"]}/{bn["denominator"]} clean) | {pn["value"]} ({pn["numerator"]}/{pn["denominator"]} clean) | {Decimal(str(pn["value"]))-Decimal(str(bn["value"]))} tuyệt đối, lower; N={bn["n"]} |')
    replace('| Review@B / miss / FP | ____ | ____ | ____; B=__ |',f'| Review@B / miss / FP | Precision={bs["precision"]}; FN={bs["fn"]}; FP={bs["fp"]} | Precision={ps["precision"]}; FN={ps["fn"]}; FP={ps["fp"]} | từ analysis_summary.json; B={summary["budget"]} |')
    replace('| Runtime / 100 items | ____ | ____ | ____; CPU=__ |',f'| Runtime / 100 items | {b["runtime_per_100_items_s"]} s | {p["runtime_per_100_items_s"]} s | end-to-end gồm load, HTML, audit; CPU={verification["cpu"]} |')
    answer('- Công thức primary metric','TP=ảnh lỗi trong top20; FP=ảnh sạch trong top20; FN=ảnh lỗi ngoài top20. Recall=TP/(TP+FN), Precision=TP/20; đơn vị ảnh, ghép image_id. Denominator nội bộ=20 ảnh lỗi/40 eval, khác với chưa biết GT chính thức.')
    answer('- Threshold / budget','Chốt config trước xem eval tại commit 6c525dc; protocol_freeze.json có timestamp/hash. B=20, action threshold score>=0.5; dev 56 ảnh để quan sát chọn ngưỡng.')
    answer('- Độ bất định',f'Bootstrap 2000 lần seed42 theo 10 scene, giữ ranking cố định; CI95 recall baseline={ci["baseline"]["ci95"]}, PoC={ci["poc"]["ci95"]}; paired Δ={ci["paired_delta"]["ci95"]}. Khoảng Δ chứa 0; chưa chứng minh cải thiện chắc chắn. Không bao gồm sai nhãn quan sát hoặc domain shift.')
    replace('`python -m src.evaluate --track t__ --pred ... --out ...`','`python -m src.evaluate --track t02 --gt reports/annotations/internal_eval_labels.csv --pred out/poc/ranked_review.csv --out out/metrics_poc_internal.json`')
    slices=summary['slices']
    def sl(run,slice_): return next(x for x in slices if x['run']==run and x['slice']==slice_)
    for slice_ in ['light=night','camera_id=cam_B']:
        sb,sp=sl('baseline',slice_),sl('poc',slice_)
        replace('| | | | | |',f'| {slice_} | {sb["n"]} | Recall={sb["recall"]}; FA={sb["false_alarm"]} | Recall={sp["recall"]}; FA={sp["false_alarm"]} | top20 toàn eval; các slice day/dusk/defect tại detailed_slices.csv |')
    answer('- Failure case 1','[img_03_0](../fixtures/t02_raw_qc/images/img_03_0.jpg), cam_B/night sạch theo nhãn nội bộ: baseline rank13 loại nhầm do quang học mềm; PoC rank30 giữ. [img_05_3](../fixtures/t02_raw_qc/images/img_05_3.jpg) glare cục bộ: baseline rank31 bỏ sót; ROI giúp PoC rank9. [Gallery](failure_gallery.html).')
    answer('- Failure case 2','[img_03_2](../fixtures/t02_raw_qc/images/img_03_2.jpg) glare nhẹ chưa cháy trắng: PoC rank21 bỏ sót. img_23_1 sạch rank19 do cạnh trùng lưới 8 pixel và quota top20. Bỏ ROI recall='+str(summary['runs']['no_roi']['recall'])+'; bỏ ngưỡng riêng recall='+str(summary['runs']['global_thresholds']['recall'])+'. Không sửa ngưỡng sau kết quả này.')
    answer('- Latency / compute',f'{verification["cpu"]}, {p["machine"]["platform"]}; baseline {b["runtime_seconds"]} s / {b["n_items"]} ảnh, PoC {p["runtime_seconds"]} s / {p["n_items"]} ảnh; PoC {1000*p["runtime_seconds"]/p["n_items"]} ms/ảnh. Đo một lần gồm I/O, chưa benchmark lặp; đây là snapshot trước khi thiết kế lại UI. Runtime lần ký duyệt ở evidence/human_review/run_info.json.')
    answer('- Review queue',f'reports/review_queue.csv: đã nhập {cvat["frame_count"]}/20 quyết định từ CVAT task/job #{cvat["job_id"]}, {cvat["action_counts"]["RECAPTURE"]} RECAPTURE / {cvat["action_counts"]["KEEP"]} KEEP. [Ảnh từng frame](../demo/cvat/index.html), [XML](../demo/cvat/annotations.xml), [biên nhận nhập](cvat_review_import.json). review_source={SOURCE}; review_note giữ nhận xét CVAT; reviewer pipeline hiện tại là Vũ Duy Khanh. Học viên xác nhận đã trực tiếp review đủ 20 frame và đồng ý kết quả; [xác nhận](human_review_confirmation.json). [Ứng dụng web và hướng dẫn](../docs/HUONG_DAN_CHAY_DEMO_T004.md); [bản review HTML](contact_sheet.html).')
    answer('- Cách override',f'Đã áp {len(cvat["override_ids"])} override KEEP→RECAPTURE cho {" và ".join(cvat["override_ids"])} từ export CVAT, chạy lại pipeline offline và thêm audit mới với ghi chú nguyên văn. Giữ toàn bộ audit cũ, raw_predictions, score và ranking. Verifier đối chiếu đủ 20 quyết định CSV, hành động cuối và audit với XML/API.')
    answer('- Decision policy',f'{signed["status"]} / {signed["reason_code"]}; owner {SOURCE}. n_reviewed=20, n_human_reviewed=20; human_review_confirmed=true. Đã ghi lần ký duyệt mới sau xác nhận trực tiếp của học viên; giữ nguyên lịch sử nhập CVAT.')
    answer('- Khi nào HOLD/REWORK','HOLD khi thiếu review/escalate/domain mới; REWORK khi còn RECAPTURE; không ép GO để đẹp bài. [Hướng dẫn review, xác nhận và quyết định](../docs/HUONG_DAN_HOAN_TAT_T004.md).')
    replace('fixtures/<track>','fixtures/t02_raw_qc')
    replace('python -m src.evaluate --track t__ --pred out/<file> --out reports/metrics_poc.json','python -m src.evaluate --track t02 --pred out/ranked_review.csv --gt reports/annotations/internal_eval_labels.csv --out reports/metrics_poc.json')
    answer('- Output của `pytest -q`',verification['tests']+'; các skip yêu cầu GT giảng viên, không tắt test. Preflight 0 FAIL/2 WARN tùy chọn; verify 14 manifests; compileall và kiểm contract pass. Chạy trong .venv (source .venv/bin/activate).')
    old=next(x for x in s.splitlines() if x.startswith('- Máy / CPU / OS / Python:'))
    replace(old,old.replace('____',f'{verification["cpu"]}; {p["machine"]["platform"]}; Python {p["machine"]["python"]}',1).replace('____',p['git_sha'],1))
    answer('- Rủi ro pháp lý','Chỉ fixture synthetic CC0; không thu thập PII thật. Model pretrained không dùng. Nguồn/license mỗi file trong manifest. Khi dùng ảnh thật phải xác minh quyền, lưu trữ và xử lý yêu cầu xóa.')
    answer('- Điều chưa biết','Nhãn nội bộ có sai lệch; glare nhẹ, JPEG nhẹ và cảnh tương phản thấp còn khó. Dev night ít, camera mới cần HOLD. Scale 10× chưa đo: xử lý ảnh tuyến tính, sort N log N; nên cache feature, chia batch và đo RAM/latency trước triển khai.')
    answer('- Không tuyên bố','DPO/legal/domain owner phải xác nhận cơ sở xử lý, consent nếu cần, retention, truy cập, license và ngưỡng QC cho dữ liệu thực. PoC chỉ hỗ trợ triage.')
    answer('- Kế hoạch cải tiến','Lấy GT chính thức; lập dev/heldout mới cho contrast glare/ROI detection, thêm camera/ảnh thật có quyền, benchmark lặp. Không tune lại trên eval vừa báo cáo.')
    replace('| Member 1 | | Integration / CLI | | |',f'| Member 1 — {SOURCE} | Duy Khanh / khanhvd.ldm.0299@gmail.com | Integration / CLI; toàn bộ vai trò nhóm 1 người | 6c525dc: pipeline + baseline + tests + protocol; 28092af: demo CVAT 20 frame; commit bằng chứng theo team_contributions.csv | Có kịch bản, chưa diễn ra trình bày thật |')
    for member,role in [('Member 2','Data + GT'),('Member 3','Core algorithm'),('Member 4','Metric + tests'),('Member 5','Review queue + report'),('Member 6 (nếu có)','Research / ablation / debate')]:
        replace(f'| {member} | | {role} | | |',f'| {member} | Không áp dụng: nhóm 1 người | {role} — do Member 1 đảm nhiệm  | Không giả thành viên/commit | Không áp dụng |')
    replace('| | | |','| https://github.com/opencv/opencv/blob/4.x/doc/tutorials/imgproc/imgtrans/laplace_operator/laplace_operator.markdown <br> https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.convolve.html | 2026-11-14 | OpenCV: cơ sở toán học đạo hàm bậc hai/cạnh, chọn baseline rẻ trên CPU. SciPy: convolution và reflect để tái lập primitive. Không sao chép nguyên văn hoặc coi đây là bằng chứng cho threshold riêng của nhóm. |')
    for text in ['Link repo và tag cuối cùng trong README; input mẫu không chứa PII thật.','Đúng 1 lệnh run, 1 lệnh evaluate, 1 lệnh tests; không cần download khi chạy.','Có license/source provenance, data splits, seed, offline environment, GT/eval N.','Mỗi thành viên có ≥1 commit thực chất và được nêu minh bạch trong bảng trên.']:
        replace('- [ ] '+text,'- [x] '+text)
    replace('- [ ] Có baseline/PoC metrics, ≥1 failure case, reviewer evidence, decision log.','- [x] Có baseline/PoC metrics, ≥1 failure case, reviewer evidence, decision log.')
    validate_structure(TEMPLATE.read_text(),s)
    return s


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',default='out/group_report_filled.md');a=ap.parse_args()
    p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(build_report(),encoding='utf-8')
    print(f'Filled answers and preserved template: {p}')


if __name__=='__main__':main()
