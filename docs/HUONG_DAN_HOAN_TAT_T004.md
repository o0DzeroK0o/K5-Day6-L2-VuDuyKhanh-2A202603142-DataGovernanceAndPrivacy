# T004 / T02 — kiểm tra và hoàn tất bài nộp

Bài có 1 thành viên. Tên Vũ Duy Khánh được suy từ tên thư mục, Git author hiện có là Duy Khanh. Agent đã thực hiện code, chạy kiểm thử, gán nhãn nội bộ bằng quan sát AI, điền review AI, áp override, lưu audit, tạo metrics/ablation/OOD, report và demo. **Chưa có người thật review; chưa push/nộp; chưa biết deadline lớp.** Không có yêu cầu bạn làm lại phần kỹ thuật đã hoàn thành.

## Checklist trước khi nộp — đối chiếu nguyên ý hướng dẫn

| Mục trong HUONG_DAN_HOC_VIEN.html | Trạng thái thực tế | Bằng chứng / việc còn lại |
|---|---|---|
| Đã chọn 1 track và đọc hết đề docs/tracks/TXX.md | Đã xong | T02, nhật ký và metric contract |
| Đã sửa configs/lab.yaml (group_id, owner, track) | Đã điền | T004, 1 người; tên/owner cần bạn xác nhận |
| Setup + test chạy ổn | Đã chạy | requirements-lock.txt; kết quả đầy đủ trong nhật ký và reports/verification.json |
| PoC chạy ra file đúng contract trong out/poc/ | Đã xong | ranked_review.csv, review queue, contact sheet, decision, audit; snapshot reports/evidence/poc/ |
| Có baseline + PoC + giải thích trong report | Đã xong ở đánh giá nội bộ | Baseline Laplacian và PoC cùng pool, budget, seed; GT chính thức do giảng viên giữ |
| Có vòng review người thật (queue / audit) | **CHỜ BẠN** | AI đã review 20 ảnh, có 2 override. Không thể gọi đó là người thật. Làm mục 1 bên dưới |
| Có group_report.md + team_contributions.csv | Đã điền | Giữ cấu trúc/câu hỏi của mẫu, ghi nhóm 1 người và hỗ trợ AI minh bạch |
| Đã tag demo / final theo mốc thời gian | Có tag cục bộ khi bàn giao; **không chứng nhận đúng giờ lớp** | Tag ghi thời điểm tạo thực tế. Bạn đối chiếu deadline và push khi sẵn sàng |

Checklist riêng T02: đã có threshold theo camera/ánh sáng, ROI glare, phân tích night/glare/cam_B và đã xem 10 ảnh proxy OOD (synthetic T13). Chưa phải 10 ảnh đời thực và tập proxy này không có ảnh lỗi nên recall không xác định. Không đánh dấu review người thật hoặc deadline là đạt khi chưa có bằng chứng.

## 1. Làm vòng review người thật (khoảng 10–15 phút)

1. Tại gốc repo, chạy `source .venv/bin/activate` và lệnh PoC:

   ```bash
   python -m src.main --input fixtures/t02_raw_qc --config configs/lab.yaml --output out/poc --offline --seed 42
   ```

2. Mở `out/poc/contact_sheet.html` bằng trình duyệt. Ảnh được nhúng, không cần mạng. Đọc `reports/failure_gallery.html` để hiểu các trường hợp night, cam_B, lóa và nén.
3. Nhập **tên thật của bạn** trong ô Reviewer. Với từng ảnh trong 20 ảnh, tự quan sát rồi chọn:

   - `approve`: đồng ý `suggested_action`; để trống override.
   - `edit` hoặc `reject`: điền đúng `KEEP` hoặc `RECAPTURE`, kèm lý do cụ thể.
   - `escalate`: không chắc chắn, cần xem lại hoặc hỏi chủ dữ liệu; batch vẫn HOLD.
   - `skip`: chưa review, không được tính là đã hoàn tất.

4. Bấm **Export decisions CSV**. Sao lưu review AI nếu cần rồi chép file tải về thành `out/poc/review_queue_reviewed.csv`. Không chỉ thay tên AI bằng tên bạn khi chưa thật sự xem ảnh.
5. Sau khi bạn đã review đủ và chịu trách nhiệm, đổi `human_review_confirmed: false` thành `true` trong `configs/lab.yaml`. Xác nhận `owner` ghi đúng tên/vai trò. Không đổi các `params` đã freeze.
6. Chạy lại đúng lệnh ở bước 1. Mở `out/poc/audit_log.jsonl`, `out/poc/item_decisions.csv`, `out/poc/decision.json`. Dòng audit mới phải mang tên bạn và `human_confirmed: true`. Điểm score/ranking không thay đổi vì review chỉ sửa hành động.
7. Nếu có RECAPTURE, kết quả REWORK là đúng: bài chứng minh triage, không bắt buộc batch phải GO. Thiếu review / escalation / domain lạ sẽ HOLD. GO chỉ nói về phạm vi triage đã review, không bảo đảm toàn bộ dữ liệu sạch.
8. Chép bằng chứng người thật vào report bằng các lệnh sau, giữ audit append-only:

   ```bash
   cp out/poc/review_queue_reviewed.csv reports/review_queue.csv
   cp out/poc/audit_log.jsonl reports/audit_log.jsonl
   cp out/poc/decision_log.csv reports/decision_log.csv
   cp out/poc/item_decisions.csv reports/evidence/poc/item_decisions.csv
   cp out/poc/ranked_review.csv reports/evidence/poc/ranked_review.csv
   cp out/poc/review_queue_reviewed.csv reports/evidence/poc/review_queue_reviewed.csv
   cp out/poc/audit_log.jsonl reports/evidence/poc/audit_log.jsonl
   cp out/poc/decision_log.csv reports/evidence/poc/decision_log.csv
   cp out/poc/decision.json reports/evidence/poc/decision.json
   cp out/poc/run_info.json reports/evidence/poc/run_info.json
   ```

9. Sửa **câu trả lời** ở mục 07, checklist Bảng 3 và thông tin cá nhân của report theo thực tế; giữ câu hỏi/mẫu. Nếu thêm file/hash snapshot, tái tạo `reports/evidence_manifest.json` bằng lệnh trong mục 4. Không sửa tay metrics. AI review cũ trong audit được giữ để truy vết.

## 2. Xác nhận nhãn nội bộ và thông tin cá nhân

- `reports/annotations/internal_eval_labels.csv` gồm 40 nhận xét thị giác AI, **không phải GT chính thức**. Nếu muốn dùng làm gold set nội bộ, tự xem 40 ảnh và ghi tên reviewer, ngày, lý do sửa nhãn; giữ lịch sử Git. Chú ý `img_03_2` glare nhẹ, `img_19_2` nén nhẹ, cam_B mềm và night còn hữu ích.
- Không sửa nhãn chỉ để tăng điểm. Không tune lại ngưỡng trên 40 ảnh này. Nếu nghiên cứu tiếp, lập protocol/split mới.
- Kiểm tra tên Vũ Duy Khánh, mã học viên 2A202603142 theo tên thư mục, Group T004, nhóm 1 người, Git author/email trong `reports/team_contributions.csv`. Không tự giả danh nhiều thành viên.
- Điền deadline chính thức ở Header report. Giữ các dòng Member 2–6 là “Không áp dụng”; nhãn “Thành viên (5–6)” thuộc mẫu nên chưa sửa.
- Report đã ghi AI hỗ trợ code và draft. Bạn cần đọc, hiểu và chịu trách nhiệm khi trình bày. Có thể tập theo `demo/t004_demo.html` và `demo/SHOWCASE_SCRIPT.md`.

## 3. Chạy lại từ đầu và chấm

Trong repo đã có `.venv`:

```bash
source .venv/bin/activate
make preflight
make verify
python -m tools.t02_submission --output out/reproduce --reports out/reproduce/reports
python -m pytest -q
```

Công cụ tái lập tạo thư mục riêng, không sửa report hay review thật đã lưu ở `out/poc`. Nó chạy inference trước rồi mới đọc nhãn qua evaluator/AI-review trong công cụ điều phối. Không cần GT ẩn, không tải mạng. CI là bootstrap theo scene của ranking cố định, chưa bao gồm sai số gán nhãn.

Nếu máy mới: cài Python 3.12, tạo `.venv`, cài `requirements-lock.txt` từ mạng hoặc wheelhouse đã chuẩn bị. Không tuyên bố cài máy mới offline khi chưa có đủ wheels. Runtime đã chạy offline trên máy hiện tại.

Giảng viên có overlay đầy đủ sẽ chạy:

```bash
python -m src.evaluate --track t02 --gt fixtures/t02_raw_qc/gt/labels.csv --pred out/poc/ranked_review.csv --out out/metrics_official.json
```

Không có overlay thì lệnh này exit 2 là đúng. Không chép nhãn AI vào `fixtures/*/gt/` để giả kết quả chính thức. Không tạo riêng một thư mục GT của T02 vì test starter yêu cầu overlay đầy đủ.

## 4. Git, tag và nộp

Agent đã tạo commit và tag cục bộ, không push. Bạn kiểm tra:

```bash
git status --short
git log -5 --oneline
git show --no-patch demo-180m
git show --no-patch final-24h
git shortlog -sne --all
```

Sau review thật, tạo nhật ký mới theo AGENTS.md; chỉ stage các file bạn vừa sửa, chạy test rồi commit có mục đích. Nếu cần hash manifest bằng chứng cập nhật:

```bash
python -m tools.t02_verify --write-manifest
python -m tools.t02_verify
```

Giữ tag đã phát hành. Nếu có chỉnh sửa sau `final-24h`, tạo tag mới ví dụ `final-reviewed` và dùng tag mới trong report/README theo quy định lớp; không force-push hoặc tự đổi lịch sử. Nếu lớp buộc tên tag chính xác, hỏi giảng viên trước khi thay tag cũ.

Khi bạn đã sẵn sàng và đã xác nhận remote đúng repo, tự push các commit/tag cần nộp:

```bash
git push origin main
git push origin demo-180m final-24h
# Nếu có bản review bổ sung:
# git push origin final-reviewed
```

Mở GitHub, kiểm tra tag chứa report, contributions, code, tests, evidence rồi nộp link tag theo cổng lớp. Không đưa dữ liệu thật chưa được phép lên public. Không tuyên bố đã đạt pháp luật/GDPR từ PoC này.
