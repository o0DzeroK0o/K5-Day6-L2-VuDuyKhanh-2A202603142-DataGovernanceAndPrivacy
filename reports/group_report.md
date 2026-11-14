# Group Report — Day 06 Data Lab (Field-to-Release PoC)

> Điền đầy đủ, cụ thể, không viết chung chung. Mọi con số phải lấy từ file do script sinh ra
> (`reports/metrics_*.json`, `reports/table1_baseline_vs_poc.md`) — không gõ tay, không làm tròn mất đơn vị.
> 3–5 trang (hoặc README + report.md tương đương).

## 00 · Header

| Mục | Giá trị |
|---|---|
| Group ID | T004 |
| Challenge | T02 · Raw QC Triage: ảnh mờ, lóa, tối và nén JPEG |
| Thành viên (5–6) + vai trò | 1. Vũ Duy Khánh, kiêm toàn bộ vai trò (Lead/Integrator) · 2. Không áp dụng (Data & fixtures) · 3. Không áp dụng (Core algorithm) · 4. Không áp dụng (QA/metric) · 5. Không áp dụng (Review + report) · 6. Không áp dụng; nhóm thực tế **1 người**. Tên suy từ thư mục, cần xác nhận; AI hỗ trợ code/draft, chưa thay review người thật. |
| Git URL | https://github.com/o0DzeroK0o/K5-Day6-L2-VuDuyKhanh-2A202603142-DataGovernanceAndPrivacy (commit/tag hiện cục bộ, chưa push) |
| Tag `demo-180m` (commit) | `demo-180m^{commit}` — xem `git rev-parse demo-180m^{commit}`; tạo thực tế khi hoàn tất demo, không khẳng định đúng phút 180 của lớp. |
| Tag `final-24h` (commit) | `final-24h^{commit}` — xem `git rev-parse final-24h^{commit}`; hash bàn giao sau commit, không khẳng định đúng deadline +24h. |
| Deadline (giờ VN) | Chưa được cung cấp. Bạn điền hạn lớp theo Asia/Ho_Chi_Minh; hướng dẫn tại [các bước hoàn tất](../docs/HUONG_DAN_HOAN_TAT_T004.md). |

## 01 · Problem statement

- Ai bị ảnh hưởng / ai chịu hậu quả khi hệ thống sai? Đội thu thập, người gán nhãn và chủ mô hình: bỏ sót ảnh hỏng gây dữ liệu kém; loại nhầm night/cam_B làm mất coverage và tốn thu lại.
- Điểm nghẽn cụ thể: Chỉ review được B=20 trong 40 ảnh eval; một ngưỡng nét toàn ảnh bỏ sót glare cục bộ và nhầm camera mềm.
- Đầu vào → đầu ra: images.csv + JPEG + manifest → feature/score → ranked_review.csv → queue/contact sheet → item KEEP/RECAPTURE → decision/audit.
- Tiêu chí GO / HOLD / REWORK (chốt trước khi chạy eval): HOLD khi chưa đủ người thật review, còn escalation hoặc domain lạ; REWORK nếu còn RECAPTURE; GO khi review đã hoàn tất và không còn yêu cầu thu lại, chỉ trong phạm vi triage. Điểm nội bộ không tự cho phép release.
- Giả định của nhóm (cần DPO/legal/domain owner xác nhận): Ảnh synthetic CC0 không PII thật; chủ dữ liệu xác nhận chuẩn “dùng được”, ROI và chính sách thu lại. Đưa lên dữ liệu thật cần kiểm tra quyền, retention và mục đích sử dụng.

## 02 · Data & provenance

| Split | N | Nguồn / link | License | Synthetic? |
|---|---|---|---|---|
| dev | 56 ảnh / 14 scene | fixtures/t02_raw_qc; synthetic generator seed42 theo manifest | CC0-1.0 | Có |
| eval / heldout | 40 ảnh / 10 scene | cùng fixture; nhãn AI riêng tại annotations/internal_eval_labels.csv | CC0-1.0 | Có |

- Schema & class mapping: image_id/path/camera_id/light/split; defect_type={none,blur,glare,dark,compression}; is_defect=0 cho none, 1 cho lỗi; severity 0–2 do AI ước lượng. Nhãn nội bộ chưa được người thật xác nhận, không phải GT giảng viên.
- Seed: 42 · Cách chia split (theo scene/group/segment?): Dùng split sẵn theo group_id scene trong manifest; không scene nào giao giữa dev và eval; mọi biến thể cùng scene ở cùng split.
- `manifest.csv` verified (sha256): có — lệnh: `python -m tools.verify_manifests`
- Dữ liệu thật dùng (nếu có) và cách xây GT cho nó: Không dùng. Kiểm thêm 10 ảnh synthetic T13 256×144, đã xem bằng mắt AI; chỉ proxy khác track, 0 positive nên không có recall OOD. [OOD](ood_check.csv).

## 03 · Research & design

- 2–3 references (URL + ngày xem) và **vì sao** chọn kỹ thuật: OpenCV Laplace Operator và SciPy ndimage.convolve, xem 2026-11-14 (URL ở mục 11). Chọn Laplacian vì đo biến thiên cạnh rẻ trên CPU; mode reflect giúp xác định biên convolution tái lập. ROI/JPEG/camera là heuristic nhóm thử trên dev, không quy kết các nguồn chứng minh ngưỡng này.
- Sơ đồ data flow (input → process → rank/QC → review → decision → report): input + sha256 → pixel features → sort score, top20 eval → người review/AI simulation → override hành động + audit append-only → decision.json → evaluator riêng và report.
- Thành phần offline (model/weights + checksum + license nếu có): Không pretrained model, không weights/API. NumPy/Pillow/SciPy; môi trường Python 3.12.16, phiên bản ở requirements-lock.txt. Hash input trong manifest, hash protocol trong protocol_freeze.json.
- Trade-offs đã cân nhắc: Max của các tín hiệu giải thích được và chạy CPU; ROI bỏ sky giảm báo nhầm nhưng glare nhẹ chưa cháy trắng vẫn lọt. Camera/light thresholds giảm loại nhầm night/cam_B nhưng cần metadata đúng. 10 OOD synthetic không thay dữ liệu thật.

## 04 · Baseline vs PoC

- Baseline (mô tả, version/config, commit): Một ngưỡng Laplacian 400, score=400/(400+variance); src.t02_baseline, config đã freeze, commit 6c525dc. Random baseline chỉ thử wiring.
- PoC (mô tả, version/config, commit): Max score blur/dark/ROI glare/blockiness; ngưỡng theo cam_A/cam_B và day/dusk/night; src.pipeline commit 6c525dc. Ngưỡng chi tiết metric_contract.md; không đổi sau eval.
- Cùng budget / cùng heldout / cùng seed: xác nhận Có: cùng 40 ảnh eval, cùng B=20, seed42, tie-break image_id. Review chỉ sửa pred_action; raw score/type dùng chấm không bị thay. Bảng chuẩn đầy đủ do src.compare sinh ở [table1_baseline_vs_poc.md](table1_baseline_vs_poc.md); giữ nguyên bố cục bảng mẫu bên dưới.

**Bảng 1 · Baseline vs PoC & hard slices** — dán output của
`python -m src.compare reports/metrics_baseline.json reports/metrics_poc.json`:

| Metric (unit) | Baseline | PoC | Δ & chú thích |
|---|---|---|---|
| Primary: Defect Recall@B | 0.85 (17/20) | 0.95 (19/20) | +0.10 tuyệt đối, nhãn AI nội bộ; higher/lower? higher |
| Hard-slice: False alarm night | 0.25 (2/8 clean) | 0.0 (0/8 clean) | -0.25 tuyệt đối, lower; N=16 |
| Review@B / miss / FP | Precision=0.85; FN=3; FP=3 | Precision=0.95; FN=1; FP=1 | từ analysis_summary.json; B=20 |
| Runtime / 100 items | 0.7614 s | 0.688 s | end-to-end gồm load, HTML, audit; CPU=Intel(R) Core(TM) i7-6820HQ CPU @ 2.70GHz |

## 05 · Evaluation protocol

- Công thức primary metric, đơn vị đánh giá, TP/FP/FN, denominator: TP=ảnh lỗi trong top20; FP=ảnh sạch trong top20; FN=ảnh lỗi ngoài top20. Recall=TP/(TP+FN), Precision=TP/20; đơn vị ảnh, ghép image_id. Denominator nội bộ=20 ảnh lỗi/40 eval, khác với chưa biết GT chính thức. (xem `reports/metric_contract.md`)
- Threshold / budget B / K và lúc chốt: Chốt config trước xem eval tại commit 6c525dc; protocol_freeze.json có timestamp/hash. B=20, action threshold score>=0.5; dev 56 ảnh để quan sát chọn ngưỡng.
- Độ bất định (CI/bootstrap/variance) khi N nhỏ: Bootstrap 2000 lần seed42 theo 10 scene, giữ ranking cố định; CI95 recall baseline=[0.7, 1.0], PoC=[0.85, 1.0]; paired Δ=[-0.09999999999999998, 0.30000000000000004]. Khoảng Δ chứa 0; chưa chứng minh cải thiện chắc chắn. Không bao gồm sai nhãn AI hoặc domain shift.
- Lệnh evaluate chính xác: `python -m src.evaluate --track t02 --gt reports/annotations/internal_eval_labels.csv --pred out/poc/ranked_review.csv --out out/metrics_poc_internal.json`

## 06 · Result slices

| Slice | N | Baseline | PoC | Ghi chú |
|---|---|---|---|---|
| light=night | 16 | Recall=0.75; FA=0.25 | Recall=0.875; FA=0.0 | top20 toàn eval; các slice day/dusk/defect tại detailed_slices.csv |
| camera_id=cam_B | 12 | Recall=1.0; FA=0.5 | Recall=0.8333333333333334; FA=0.0 | top20 toàn eval; các slice day/dusk/defect tại detailed_slices.csv |

- Failure case 1 (ảnh/metadata + root cause): [img_03_0](../fixtures/t02_raw_qc/images/img_03_0.jpg), cam_B/night sạch theo AI: baseline rank13 loại nhầm do quang học mềm; PoC rank30 giữ. [img_05_3](../fixtures/t02_raw_qc/images/img_05_3.jpg) glare cục bộ: baseline rank31 bỏ sót; ROI giúp PoC rank9. [Gallery](failure_gallery.html).
- Failure case 2: [img_03_2](../fixtures/t02_raw_qc/images/img_03_2.jpg) glare nhẹ chưa cháy trắng: PoC rank21 bỏ sót. img_23_1 sạch rank19 do cạnh trùng lưới 8 pixel và quota top20. Bỏ ROI recall=0.85; bỏ ngưỡng riêng recall=0.8. Không sửa ngưỡng sau kết quả này.
- Latency / compute (máy, CPU, ms/item): Intel(R) Core(TM) i7-6820HQ CPU @ 2.70GHz, Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; baseline 0.7309 s / 96 ảnh, PoC 0.6605 s / 96 ảnh; PoC 6.880208333333333 ms/ảnh. Đo một lần gồm I/O, chưa benchmark lặp.

## 07 · Human & decision

- Review queue (file, B, cách ưu tiên): reports/review_queue.csv, 20 ảnh eval theo score giảm; contact_sheet.html nhúng ảnh. Đã review bằng AI:Codex, chưa có review người thật; xem hướng dẫn hoàn tất.
- Cách override + audit log (`out/audit_log.jsonl`): AI đã đổi KEEP→RECAPTURE cho img_19_2 và img_06_3 sau quan sát. Lưu raw_predictions và item_decisions, audit ghi actor/before/after/note; không đổi score. Có test chặn ID trùng/lạ, score stale, thiếu reviewer hoặc override sai.
- Decision policy + `reason_code` + owner: HOLD / HUMAN_REVIEW_REQUIRED; owner Vũ Duy Khánh (chờ xác nhận). n_reviewed=20, n_human_reviewed=0. AI không ký thay người dùng; human_review_confirmed=false.
- Khi nào HOLD/REWORK thay vì tự động release: HOLD khi thiếu review/escalate/domain mới; REWORK khi còn RECAPTURE; không ép GO để đẹp bài. [Hướng dẫn từng bước export CSV và xác nhận](../docs/HUONG_DAN_HOAN_TAT_T004.md).

## 08 · Reproduce & tests

```bash
make setup          # hoặc: python -m venv .venv && pip install -r requirements.txt
python -m src.main --input fixtures/t02_raw_qc --config configs/lab.yaml --output out/ --offline --seed 42
python -m src.evaluate --track t02 --pred out/ranked_review.csv --gt reports/annotations/internal_eval_labels.csv --out reports/metrics_poc.json
pytest -q
```

- Output của `pytest -q`: 69 passed, 39 skipped in 5.19s; các skip yêu cầu GT giảng viên, không tắt test. Preflight 0 FAIL/2 WARN tùy chọn; verify 14 manifests; compileall và kiểm contract pass. Chạy trong .venv (source .venv/bin/activate).
- Máy / CPU / OS / Python: Intel(R) Core(TM) i7-6820HQ CPU @ 2.70GHz; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.12.16 · git sha: 6c525dc

## 09 · Limitations & ethics

- Rủi ro pháp lý / PII / license: Chỉ fixture synthetic CC0; không thu thập PII thật. Model pretrained không dùng. Nguồn/license mỗi file trong manifest. Khi dùng ảnh thật phải xác minh quyền, lưu trữ và xử lý yêu cầu xóa.
- Điều chưa biết; false alarms; nếu scale 10× thì sao: Nhãn AI có sai lệch; glare nhẹ, JPEG nhẹ và cảnh tương phản thấp còn khó. Dev night ít, camera mới cần HOLD. Scale 10× chưa đo: xử lý ảnh tuyến tính, sort N log N; nên cache feature, chia batch và đo RAM/latency trước triển khai.
- Không tuyên bố "đạt GDPR / luật Việt Nam" từ checklist tự động; giả định cần DPO/legal xác nhận: DPO/legal/domain owner phải xác nhận cơ sở xử lý, consent nếu cần, retention, truy cập, license và ngưỡng QC cho dữ liệu thực. PoC chỉ hỗ trợ triage.
- Kế hoạch cải tiến: Review người thật và lấy GT chính thức; sau đó lập dev/heldout mới cho contrast glare/ROI detection, thêm camera/ảnh thật có quyền, benchmark lặp. Không tune lại trên eval vừa báo cáo.

## 10 · Team contribution

**Bảng 2 · Individual contribution evidence** (đối chiếu với `git shortlog -sne --all` và `reports/team_contributions.csv`)

| Học viên | Git author/email | Module / vai trò | Commit SHA / diff chứng minh | Trình bày? |
|---|---|---|---|---|
| Member 1 — Vũ Duy Khánh | Duy Khanh / khanhvd.ldm.0299@gmail.com | Integration / CLI; toàn bộ vai trò nhóm 1 người, AI hỗ trợ code/draft | 6c525dc: pipeline + baseline + tests + protocol; commit bằng chứng theo team_contributions.csv | Có kịch bản, chưa diễn ra trình bày thật |
| Member 2 | Không áp dụng: nhóm 1 người | Data + GT — do Member 1 đảm nhiệm với hỗ trợ AI | Không giả thành viên/commit | Không áp dụng |
| Member 3 | Không áp dụng: nhóm 1 người | Core algorithm — do Member 1 đảm nhiệm với hỗ trợ AI | Không giả thành viên/commit | Không áp dụng |
| Member 4 | Không áp dụng: nhóm 1 người | Metric + tests — do Member 1 đảm nhiệm với hỗ trợ AI | Không giả thành viên/commit | Không áp dụng |
| Member 5 | Không áp dụng: nhóm 1 người | Review queue + report — do Member 1 đảm nhiệm với hỗ trợ AI | Không giả thành viên/commit | Không áp dụng |
| Member 6 (nếu có) | Không áp dụng: nhóm 1 người | Research / ablation / debate — do Member 1 đảm nhiệm với hỗ trợ AI | Không giả thành viên/commit | Không áp dụng |

## 11 · References

| URL | Ngày xem | 1–2 dòng ý nghĩa (không chép nguyên văn) |
|---|---|---|
| https://github.com/opencv/opencv/blob/4.x/doc/tutorials/imgproc/imgtrans/laplace_operator/laplace_operator.markdown <br> https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.convolve.html | 2026-11-14 | OpenCV: cơ sở toán học đạo hàm bậc hai/cạnh, chọn baseline rẻ trên CPU. SciPy: convolution và reflect để tái lập primitive. Không sao chép nguyên văn hoặc coi đây là bằng chứng cho threshold riêng của nhóm. |

---

**Bảng 3 · Checklist chốt khi nộp**

- [x] Link repo và tag cuối cùng trong README; input mẫu không chứa PII thật.
- [x] Đúng 1 lệnh run, 1 lệnh evaluate, 1 lệnh tests; không cần download khi chạy.
- [ ] Có baseline/PoC metrics, ≥1 failure case, reviewer evidence, decision log. — Các file đã có; reviewer hiện là AI, **chờ bạn review thật** theo hướng dẫn, không xác nhận thay.
- [x] Có license/source provenance, data splits, seed, offline environment, GT/eval N.
- [x] Mỗi thành viên có ≥1 commit thực chất và được nêu minh bạch trong bảng trên.
