# reports/

| File | Ai tạo | Cách tạo |
|---|---|---|
| `group_report.md` | nhóm | điền template |
| `metric_contract.md` | nhóm | điền ở phút 30 |
| `metrics_baseline.json` | **script** | `python -m src.evaluate --track tXX --pred out/baseline/<file> --run-name baseline --out reports/metrics_baseline.json` |
| `metrics_poc.json` | **script** | `python -m src.evaluate --track tXX --pred out/poc/<file> --run-name poc --out reports/metrics_poc.json` |
| `table1_baseline_vs_poc.md` | **script** | `python -m src.compare reports/metrics_baseline.json reports/metrics_poc.json --out reports/table1_baseline_vs_poc.md` |
| `review_queue.csv` | pipeline + reviewer | đồng bộ từ `evidence/human_review/review_queue_reviewed.csv`; đủ 20 quyết định đã xác nhận, ghi chú nguyên văn |
| `decision_log.csv` | pipeline | đồng bộ từ `evidence/human_review/decision_log.csv`, giữ lịch sử trước xác nhận |
| `team_contributions.csv` | nhóm | khớp với `git shortlog -sne --all` |

Các file metrics/table **không được sửa tay** — giảng viên sẽ chạy lại lệnh để đối chiếu.

## Review hiện tại và lịch sử CVAT

**Vũ Duy Khanh đã xác nhận trực tiếp xem đủ 20 frame** của task/job #17 và đồng ý 19 RECAPTURE, 1 KEEP (`img_23_1`), gồm hai override `img_19_2`, `img_06_3`. [Bản xác nhận](human_review_confirmation.json) lưu nguyên văn câu hỏi/câu trả lời và checksum. `review_source` trong CVAT và `reviewer` trong CSV hiện tại đều là Vũ Duy Khanh; `review_note` chỉ chứa nhận xét chất lượng ảnh.

Đọc kết quả hiện tại tại [evidence/human_review/decision.json](evidence/human_review/decision.json): **REWORK / QUALITY_RECAPTURE_REQUIRED**, `n_human_reviewed=20`. Các đường dẫn `review_queue.csv`, `audit_log.jsonl` và `decision_log.csv` ở thư mục này khớp bản đã xác nhận. Metrics và nhãn tự kiểm giữ nguyên; xác nhận 20 frame không chứng nhận toàn bộ 40 nhãn eval.

[Biên nhận nhập CVAT](cvat_review_import.json) và `evidence/poc/` lưu lần nhập trước khi có xác nhận trực tiếp; trạng thái **HOLD / HUMAN_REVIEW_REQUIRED** ở đó là lịch sử. Nguồn thao tác và thời điểm của các sự kiện cũ được giữ nguyên, audit hiện tại nối tiếp lịch sử này.

Chạy `.venv/bin/python -m tools.t02_human_review` để kiểm bản xác nhận hiện tại; `.venv/bin/python -m tools.t02_cvat_review` kiểm lần nhập lịch sử. Dùng `make t02-submission OUT=out/check-final` vào thư mục mới để tái lập cả baseline, PoC và review, giữ nguyên metrics bài nộp. [Hướng dẫn đồng bộ](../docs/HUONG_DAN_DEMO_CVAT_LOCAL.md) và [nhật ký kiểm tra repo/report](../docs/2026-11-15-111055-kiem-tra-repo-va-report.md) ghi chi tiết.
