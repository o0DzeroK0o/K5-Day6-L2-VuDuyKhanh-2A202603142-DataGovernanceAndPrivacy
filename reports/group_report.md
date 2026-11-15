# Group Report — Day 06 Data Lab (Field-to-Release PoC)

> Điền đầy đủ, cụ thể, không viết chung chung. Mọi con số phải lấy từ file do script sinh ra
> (`reports/metrics_*.json`, `reports/table1_baseline_vs_poc.md`) — không gõ tay, không làm tròn mất đơn vị.
> 3–5 trang (hoặc README + report.md tương đương).

## 00 · Header

| Mục                        | Giá trị                                                                                                                                                                                                                                                                                                                     |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Group ID                   | T004                                                                                                                                                                                                                                                                                                                        |
| Challenge                  | T02 · Raw QC Triage: ảnh mờ, lóa, tối và nén JPEG                                                                                                                                                                                                                                                                           |
| Thành viên (5–6) + vai trò | 1. Vũ Duy Khanh, kiêm toàn bộ vai trò (Lead/Integrator) · 2. Không áp dụng (Data & fixtures) · 3. Không áp dụng (Core algorithm) · 4. Không áp dụng (QA/metric) · 5. Không áp dụng (Review + report) · 6. Không áp dụng; nhóm thực tế **1 người**. Vũ Duy Khanh xác nhận đã trực tiếp review đủ 20 frame và đồng ý kết quả. |
| Git URL                    | https://github.com/o0DzeroK0o/K5-Day6-L2-VuDuyKhanh-2A202603142-DataGovernanceAndPrivacy                                                                                                                                                                                                                                    |
| Tag `demo-180m` (commit)   | `1d2d4a6bd0587ed2b2531c42572cda72a43d1e5b`                                                                                                                                                                                                                                                                                  |
| Tag `final-24h` (commit)   | `83ca5ccc9868bfee89a8f285c3564784c174056b`                                                                                                                                                                                                                                                                                  |
| Deadline (giờ VN)          | 11:40 15/11/2026                                                                                                                                                                                                                                                                                                            |

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
| eval / heldout | 40 ảnh / 10 scene | cùng fixture; nhãn quan sát nội bộ; nguồn tại annotations/README.md và annotations/internal_eval_labels.csv | CC0-1.0 | Có |

- Schema & class mapping: image_id/path/camera_id/light/split; defect_type={none,blur,glare,dark,compression}; is_defect=0 cho none, 1 cho lỗi; severity 0–2 theo nhãn quan sát nội bộ. Xác nhận 20 frame review không chứng nhận toàn bộ 40 nhãn eval; nguồn nhãn tại [annotations/README.md](annotations/README.md), không phải GT giảng viên.
- Seed: 42 · Cách chia split (theo scene/group/segment?): Dùng split sẵn theo group_id scene trong manifest; không scene nào giao giữa dev và eval; mọi biến thể cùng scene ở cùng split.
- `manifest.csv` verified (sha256): có — lệnh: `python -m tools.verify_manifests`
- Dữ liệu thật dùng (nếu có) và cách xây GT cho nó: Không dùng. Kiểm thêm 10 ảnh synthetic T13 256×144, đã có nhãn quan sát nội bộ; chỉ proxy khác track, 0 positive nên không có recall OOD. [OOD](ood_check.csv).

## 03 · Research & design

- 2–3 references (URL + ngày xem) và **vì sao** chọn kỹ thuật: OpenCV Laplace Operator và SciPy ndimage.convolve, xem 2026-11-14 (URL ở mục 11). Chọn Laplacian vì đo biến thiên cạnh rẻ trên CPU; mode reflect giúp xác định biên convolution tái lập. ROI/JPEG/camera là heuristic nhóm thử trên dev, không quy kết các nguồn chứng minh ngưỡng này.
- Sơ đồ data flow (input → process → rank/QC → review → decision → report): Web HTTP chạy bằng `make web`: Load kiểm input + sha256 → Process tính pixel features → Rank lấy top20 eval → Review lưu quyết định hoặc nhập bản CVAT đã xác nhận → Decide áp policy và tạo decision/audit. Mỗi nút thực thi hàm tương ứng trong src.pipeline qua worker riêng; kết quả và phiên bản giữ trong out/web/. [Hướng dẫn](../docs/HUONG_DAN_CHAY_DEMO_T004.md), [ảnh thực thi](../demo/web/index.html). Evaluator và report chạy riêng, không dùng GT khi xử lý.
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
| Primary: Defect Recall@B | 0.85 (17/20) | 0.95 (19/20) | +0.10 tuyệt đối, nhãn quan sát nội bộ; higher/lower? higher |
| Hard-slice: False alarm night | 0.25 (2/8 clean) | 0.0 (0/8 clean) | -0.25 tuyệt đối, lower; N=16 |
| Review@B / miss / FP | Precision=0.85; FN=3; FP=3 | Precision=0.95; FN=1; FP=1 | từ analysis_summary.json; B=20 |
| Runtime / 100 items | 0.7614 s | 0.688 s | end-to-end gồm load, HTML, audit; CPU=Intel(R) Core(TM) i7-6820HQ CPU @ 2.70GHz |

## 05 · Evaluation protocol

- Công thức primary metric, đơn vị đánh giá, TP/FP/FN, denominator: TP=ảnh lỗi trong top20; FP=ảnh sạch trong top20; FN=ảnh lỗi ngoài top20. Recall=TP/(TP+FN), Precision=TP/20; đơn vị ảnh, ghép image_id. Denominator nội bộ=20 ảnh lỗi/40 eval, khác với chưa biết GT chính thức. (xem `reports/metric_contract.md`)
- Threshold / budget B / K và lúc chốt: Chốt config trước xem eval tại commit 6c525dc; protocol_freeze.json có timestamp/hash. B=20, action threshold score>=0.5; dev 56 ảnh để quan sát chọn ngưỡng.
- Độ bất định (CI/bootstrap/variance) khi N nhỏ: Bootstrap 2000 lần seed42 theo 10 scene, giữ ranking cố định; CI95 recall baseline=[0.7, 1.0], PoC=[0.85, 1.0]; paired Δ=[-0.09999999999999998, 0.30000000000000004]. Khoảng Δ chứa 0; chưa chứng minh cải thiện chắc chắn. Không bao gồm sai nhãn quan sát hoặc domain shift.
- Lệnh evaluate chính xác: `python -m src.evaluate --track t02 --gt reports/annotations/internal_eval_labels.csv --pred out/poc/ranked_review.csv --out out/metrics_poc_internal.json`

## 06 · Result slices

| Slice | N | Baseline | PoC | Ghi chú |
|---|---|---|---|---|
| light=night | 16 | Recall=0.75; FA=0.25 | Recall=0.875; FA=0.0 | top20 toàn eval; các slice day/dusk/defect tại detailed_slices.csv |
| camera_id=cam_B | 12 | Recall=1.0; FA=0.5 | Recall=0.8333333333333334; FA=0.0 | top20 toàn eval; các slice day/dusk/defect tại detailed_slices.csv |

- Failure case 1 (ảnh/metadata + root cause): [img_03_0](../fixtures/t02_raw_qc/images/img_03_0.jpg), cam_B/night sạch theo nhãn nội bộ: baseline rank13 loại nhầm do quang học mềm; PoC rank30 giữ. [img_05_3](../fixtures/t02_raw_qc/images/img_05_3.jpg) glare cục bộ: baseline rank31 bỏ sót; ROI giúp PoC rank9. [Gallery](failure_gallery.html).
- Failure case 2: [img_03_2](../fixtures/t02_raw_qc/images/img_03_2.jpg) glare nhẹ chưa cháy trắng: PoC rank21 bỏ sót. img_23_1 sạch rank19 do cạnh trùng lưới 8 pixel và quota top20. Bỏ ROI recall=0.85; bỏ ngưỡng riêng recall=0.8. Không sửa ngưỡng sau kết quả này.
- Latency / compute (máy, CPU, ms/item): Intel(R) Core(TM) i7-6820HQ CPU @ 2.70GHz, Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; baseline 0.7309 s / 96 ảnh, PoC 0.6605 s / 96 ảnh; PoC 6.880208333333333 ms/ảnh. Đo một lần gồm I/O, chưa benchmark lặp; đây là snapshot trước khi thiết kế lại UI. Runtime lần ký duyệt ở evidence/human_review/run_info.json.

## 07 · Human & decision

- Review queue (file, B, cách ưu tiên): reports/review_queue.csv: đã nhập 20/20 quyết định từ CVAT task/job #17, 19 RECAPTURE / 1 KEEP. [Ảnh từng frame](../demo/cvat/index.html), [XML](../demo/cvat/annotations.xml), [biên nhận nhập](cvat_review_import.json). review_source=Vũ Duy Khanh; review_note giữ nhận xét CVAT; reviewer pipeline hiện tại là Vũ Duy Khanh. Học viên xác nhận đã trực tiếp review đủ 20 frame và đồng ý kết quả; [xác nhận](human_review_confirmation.json). [Ứng dụng web và hướng dẫn](../docs/HUONG_DAN_CHAY_DEMO_T004.md); [bản review HTML](contact_sheet.html).
- Cách override + audit log (`out/audit_log.jsonl`): Đã áp 2 override KEEP→RECAPTURE cho img_19_2 và img_06_3 từ export CVAT, chạy lại pipeline offline và thêm audit mới với ghi chú nguyên văn. Giữ toàn bộ audit cũ, raw_predictions, score và ranking. Verifier đối chiếu đủ 20 quyết định CSV, hành động cuối và audit với XML/API.
- Decision policy + `reason_code` + owner: REWORK / QUALITY_RECAPTURE_REQUIRED; owner Vũ Duy Khanh. n_reviewed=20, n_human_reviewed=20; human_review_confirmed=true. Đã ghi lần ký duyệt mới sau xác nhận trực tiếp của học viên; giữ nguyên lịch sử nhập CVAT.
- Khi nào HOLD/REWORK thay vì tự động release: HOLD khi thiếu review/escalate/domain mới; REWORK khi còn RECAPTURE; không ép GO để đẹp bài. [Hướng dẫn review, xác nhận và quyết định](../docs/HUONG_DAN_HOAN_TAT_T004.md).

## 08 · Reproduce & tests

```bash
make setup          # hoặc: python -m venv .venv && pip install -r requirements.txt
source .venv/bin/activate && python -m src.main --input fixtures/t02_raw_qc --config configs/lab.yaml --output out/report-reproduce/poc --offline --seed 42
python -m src.evaluate --track t02 --pred out/report-reproduce/poc/ranked_review.csv --gt reports/annotations/internal_eval_labels.csv --out out/report-reproduce/metrics_poc_internal.json
pytest -q
```

- Output của `pytest -q`: 149 passed, 39 skipped in 56.28s; các skip yêu cầu GT giảng viên, không tắt test. Preflight 0 FAIL/2 WARN tùy chọn; verify 14 manifests; compileall và kiểm contract pass. Dùng make setup với requirements-lock.txt, rồi các lệnh bash trên kích hoạt .venv. Lượt CLI mới chưa nạp review sẽ HOLD; tái lập cả 20 quyết định đã xác nhận bằng `make t02-submission OUT=out/check-final` vào thư mục mới sẽ REWORK. Output tái lập ở out/, không ghi đè metrics bài nộp. [Nhật ký kiểm tra](../docs/2026-11-15-111055-kiem-tra-repo-va-report.md).
- Máy / CPU / OS / Python: Intel(R) Core(TM) i7-6820HQ CPU @ 2.70GHz; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.12.16 · git sha: 6c525dc (commit của snapshot đo runtime baseline/PoC; không phải HEAD hiện tại)

## 09 · Limitations & ethics

- Rủi ro pháp lý / PII / license: Chỉ fixture synthetic CC0; không thu thập PII thật. Model pretrained không dùng. Nguồn/license mỗi file trong manifest. Khi dùng ảnh thật phải xác minh quyền, lưu trữ và xử lý yêu cầu xóa.
- Điều chưa biết; false alarms; nếu scale 10× thì sao: Nhãn nội bộ có sai lệch; glare nhẹ, JPEG nhẹ và cảnh tương phản thấp còn khó. Dev night ít, camera mới cần HOLD. Scale 10× chưa đo: xử lý ảnh tuyến tính, sort N log N; nên cache feature, chia batch và đo RAM/latency trước triển khai.
- Không tuyên bố "đạt GDPR / luật Việt Nam" từ checklist tự động; giả định cần DPO/legal xác nhận: DPO/legal/domain owner phải xác nhận cơ sở xử lý, consent nếu cần, retention, truy cập, license và ngưỡng QC cho dữ liệu thực. PoC chỉ hỗ trợ triage.
- Kế hoạch cải tiến: Lấy GT chính thức; lập dev/heldout mới cho contrast glare/ROI detection, thêm camera/ảnh thật có quyền, benchmark lặp. Không tune lại trên eval vừa báo cáo.

## 10 · Team contribution

**Bảng 2 · Individual contribution evidence** (đối chiếu với `git shortlog -sne --all` và `reports/team_contributions.csv`)

| Học viên | Git author/email | Module / vai trò | Commit SHA / diff chứng minh | Trình bày? |
|---|---|---|---|---|
| Member 1 — Vũ Duy Khanh | Duy Khanh / khanhvd.ldm.0299@gmail.com | Integration / CLI; toàn bộ vai trò nhóm 1 người | 6c525dc: pipeline + baseline + tests + protocol; 28092af: demo CVAT 20 frame; commit bằng chứng theo team_contributions.csv | Có kịch bản, chưa diễn ra trình bày thật |
| Member 2 | Không áp dụng: nhóm 1 người | Data + GT — do Member 1 đảm nhiệm  | Không giả thành viên/commit | Không áp dụng |
| Member 3 | Không áp dụng: nhóm 1 người | Core algorithm — do Member 1 đảm nhiệm  | Không giả thành viên/commit | Không áp dụng |
| Member 4 | Không áp dụng: nhóm 1 người | Metric + tests — do Member 1 đảm nhiệm  | Không giả thành viên/commit | Không áp dụng |
| Member 5 | Không áp dụng: nhóm 1 người | Review queue + report — do Member 1 đảm nhiệm  | Không giả thành viên/commit | Không áp dụng |
| Member 6 (nếu có) | Không áp dụng: nhóm 1 người | Research / ablation / debate — do Member 1 đảm nhiệm  | Không giả thành viên/commit | Không áp dụng |

## 11 · References

| URL | Ngày xem | 1–2 dòng ý nghĩa (không chép nguyên văn) |
|---|---|---|
| https://github.com/opencv/opencv/blob/4.x/doc/tutorials/imgproc/imgtrans/laplace_operator/laplace_operator.markdown <br> https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.convolve.html | 2026-11-14 | OpenCV: cơ sở toán học đạo hàm bậc hai/cạnh, chọn baseline rẻ trên CPU. SciPy: convolution và reflect để tái lập primitive. Không sao chép nguyên văn hoặc coi đây là bằng chứng cho threshold riêng của nhóm. |

---

**Bảng 3 · Checklist chốt khi nộp**

- [ ] Link repo và tag cuối cùng trong README; input mẫu không chứa PII thật.
- [x] Đúng 1 lệnh run, 1 lệnh evaluate, 1 lệnh tests; không cần download khi chạy.
- [x] Có baseline/PoC metrics, ≥1 failure case, reviewer evidence, decision log.
- [x] Có license/source provenance, data splits, seed, offline environment, GT/eval N.
- [x] Mỗi thành viên có ≥1 commit thực chất và được nêu minh bạch trong bảng trên.
