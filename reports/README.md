# reports/

| File | Ai tạo | Cách tạo |
|---|---|---|
| `group_report.md` | nhóm | điền template |
| `metric_contract.md` | nhóm | điền ở phút 30 |
| `metrics_baseline.json` | **script** | `python -m src.evaluate --track tXX --pred out/baseline/<file> --run-name baseline --out reports/metrics_baseline.json` |
| `metrics_poc.json` | **script** | `python -m src.evaluate --track tXX --pred out/poc/<file> --run-name poc --out reports/metrics_poc.json` |
| `table1_baseline_vs_poc.md` | **script** | `python -m src.compare reports/metrics_baseline.json reports/metrics_poc.json --out reports/table1_baseline_vs_poc.md` |
| `review_queue.csv` | pipeline + reviewer | đồng bộ từ `out/poc/review_queue_reviewed.csv`; 20 quyết định từ CVAT, ghi chú nguyên văn |
| `decision_log.csv` | pipeline | copy từ `out/poc/decision_log.csv` |
| `team_contributions.csv` | nhóm | khớp với `git shortlog -sne --all` |

Các file metrics/table **không được sửa tay** — giảng viên sẽ chạy lại lệnh để đối chiếu.

## Kết quả sau review CVAT

Task/job #17 có đủ 20 tag: 19 RECAPTURE và 1 KEEP. `review_source` trong CVAT là Vũ Duy Khanh theo tên đã xác nhận. CSV pipeline giữ `reviewer=AI:Codex` để phản ánh người thao tác, `review_note` chỉ chứa nhận xét ảnh. Hai override là `img_19_2` và `img_06_3`.

[Biên nhận nhập](cvat_review_import.json) liên kết XML, queue, CSV và checksum. `audit_log.jsonl` giữ toàn bộ sự kiện cũ và thêm vòng review CVAT. `decision.json` trong `evidence/poc/` dùng owner đúng tên; HOLD / HUMAN_REVIEW_REQUIRED vẫn chờ người học xác nhận. Metric và nhãn tự kiểm không đổi.

Chạy `.venv/bin/python -m tools.t02_cvat_review` để kiểm đối chiếu XML với CSV, hành động cuối và audit. [Hướng dẫn đồng bộ](../docs/HUONG_DAN_DEMO_CVAT_LOCAL.md) có lệnh tái lập. Protocol config và log lịch sử giữ nguyên tên ở thời điểm cũ, không viết lại lịch sử.
