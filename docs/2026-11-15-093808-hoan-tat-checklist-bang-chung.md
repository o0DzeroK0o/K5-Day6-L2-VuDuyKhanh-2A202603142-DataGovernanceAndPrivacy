# Hoàn tất checklist bằng chứng baseline/PoC và review

## Mục tiêu

Kiểm tra rồi đánh dấu mục “Có baseline/PoC metrics, ≥1 failure case, reviewer evidence, decision log.” trong Bảng 3 theo yêu cầu người dùng.

## Hiện trạng và quyết định

- HEAD đầu nhiệm vụ: `13f81c5`; quy trình Git/docs đã có. `reports/group_report.md` có chỉnh sửa sẵn: định dạng bảng, deadline `11:00 15/11/2026`, bỏ các dòng Member 2–6 và bỏ ghi chú sau checkbox. `.obsidian/` chưa track, ngoài nhiệm vụ.
- Bốn loại bằng chứng của đúng mục này đều đã có. Vì vậy đánh dấu `[x]`; không diễn giải việc có reviewer evidence thành xác nhận người học đã trực tiếp review. Mục 07, provenance CVAT và trạng thái HOLD tiếp tục phản ánh thực tế.
- Chỉ thay dòng checklist trong report hiện tại, giữ nguyên mọi chỉnh sửa khác của người dùng. Sửa cùng dòng trong generator để preview sinh lại không bỏ dấu tick.
- Commit chọn riêng thay đổi checklist của report dựa trên HEAD; deadline và bảng thành viên do người dùng đang sửa vẫn để ngoài commit. Manifest của commit dùng đúng report được stage. Bản kiểm chứng riêng chứa HEAD cộng các thay đổi thuộc nhiệm vụ, không sửa bản report đang làm của người dùng để chạy kiểm tra.

## Bằng chứng đã đối chiếu

| Thành phần | Kết quả |
|---|---|
| Baseline/PoC metrics | `reports/metrics_baseline.json`, `reports/metrics_poc.json` khớp tính lại bằng evaluator chung; Recall@20 lần lượt 0.85 và 0.95 trên nhãn nội bộ đã khai báo. |
| Ít nhất một failure case | Mục 06 có `img_03_2` (glare nhẹ, PoC rank 21); ảnh gốc tồn tại. `reports/failure_gallery.html` có 5 ảnh nhúng và mô tả lỗi. |
| Reviewer evidence | `tools.t02_cvat_review.verify_import()` PASS: đủ 20 frame, XML/API, CSV, hành động cuối, audit và biên nhận khớp nhau. |
| Decision log | `reports/decision_log.csv` có 5 sự kiện; sự kiện cuối khớp `reports/evidence/poc/decision.json` về status, reason_code và owner: HOLD / HUMAN_REVIEW_REQUIRED. |

## Tệp thay đổi

- `reports/group_report.md`: đánh dấu đúng mục checklist được yêu cầu.
- `tools/t02_fill_report.py`: đồng bộ câu checklist trong preview sinh từ mẫu.
- `tests/test_t02_report.py`: cập nhật test hiện có để kiểm dấu tick và giữ xác nhận người học ở trạng thái chờ tại mục 07.
- `reports/evidence_manifest.json`: checksum của report trong commit.
- Nhật ký này và `docs/README.md`.

## Xác minh

- Trước sửa, `.venv/bin/python -m tools.t02_verify` trên working tree: FAIL `report line count changed` và `evidence hash mismatch: reports/group_report.md`. Đây là các thay đổi report đã có trước nhiệm vụ (bỏ dòng Member 2–6 và sửa nội dung), không phải thiếu bốn bằng chứng của checklist.
- Script đối chiếu độc lập: PASS cả bốn phần nêu trên. Hai lần nhập script tạm bị lỗi escape newline, chưa thực thi kiểm tra; đã sửa và chạy lại thành công.
- Lần chạy toàn bộ test đầu trên snapshot: **1 failed, 102 passed, 39 skipped in 6.88s**. Test report còn buộc câu nhắc người thật ở ghi chú checkbox đã bỏ. Đã cập nhật test đó: checkbox đã tick, mục 07 vẫn phải có `HOLD / HUMAN_REVIEW_REQUIRED`, `n_human_reviewed=0`, `human_review_confirmed=false` và câu xác nhận người học còn chờ. Không thay validator cấu trúc hoặc tiêu chuẩn provenance.
- Trong lúc làm, người dùng tiếp tục sửa câu “Kế hoạch cải tiến”. Phép đối chiếu toàn report với bản trước nhiệm vụ báo khác biệt; xác định đúng dòng này và giữ nguyên ngoài commit, cùng deadline/bảng thành viên. Không ghi đè thao tác đang làm của người dùng.
- Snapshot `/tmp/t004-checklist-validation-41eyc76_` được tạo từ `git archive HEAD` rồi chép đúng phần nhiệm vụ; dùng interpreter `.venv/bin/python` của repository, không chép chỉnh sửa riêng của người dùng. `python -m pytest -o addopts= -q`: **103 passed, 39 skipped in 6.35s**; skip do thiếu GT/overlay giảng viên.
- Trên snapshot, `python -m tools.t02_verify --write-manifest` và kiểm lại `python -m tools.t02_verify`: PASS cấu trúc report, metric, freeze, đủ 20 frame và checksum. Manifest chỉ đổi hash report tương ứng dòng checklist; các bằng chứng metric/CVAT/audit không đổi.
- Trên repo gốc, `make preflight`: **0 FAIL, 2 WARN** (data/model tùy chọn); `make verify`: **14 manifests, 0 failing**. `python -m compileall -q tools/t02_fill_report.py tests/test_t02_report.py` và `git diff --check`: PASS.
- Report hiện tại ở dòng 130 đã có `[x]` cho mục được yêu cầu. Chỉ stage dòng checklist và các tệp thuộc nhiệm vụ; không stage deadline, bảng thành viên, câu kế hoạch đang sửa hay `.obsidian/`.

## Hạn chế / bước tiếp

Mục checklist bằng chứng đã hoàn tất. Review trực tiếp của người học vẫn là bước riêng. Report trong working tree giữ nguyên chỉnh sửa sẵn của người dùng nên kiểm cấu trúc toàn bộ file vẫn cần xử lý riêng; không coi verifier working tree là PASS và không đổi validator để bỏ qua lỗi mẫu.
