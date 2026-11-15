# Giao diện review và xác nhận trực tiếp của học viên

## Mục tiêu
Xây dựng lại công cụ web offline, kiểm thử thao tác thực tế, đồng bộ báo cáo và xác nhận của Vũ Duy Khanh cho đủ 20 frame.

## Trạng thái ban đầu
- HEAD `cf87457`. Quy trình Git/docs đã đầy đủ, không khởi tạo lại.
- Có sửa sẵn tại group_report.md, metric_contract.md, team_contributions.csv; đã lưu bản sao ngoài repository tại `/tmp/t004-review-ui-originals/`. `.obsidian/` không thuộc nhiệm vụ.
- CVAT task/job 17: 20 frame, 19 RECAPTURE / 1 KEEP; hai override img_19_2 và img_06_3. XML, ảnh chụp và lần nhập trước được giữ làm lịch sử.

## Xác nhận và quyết định
- Người học trả lời: “Đã xem đủ 20 frame và đồng ý kết quả này” cho câu hỏi xác nhận 19 RECAPTURE, 1 KEEP (img_23_1), hai override img_19_2 và img_06_3.
- Lập lần ký duyệt mới dưới tên Vũ Duy Khanh; không sửa lại danh tính của các sự kiện lịch sử.
- Không thay thuật toán, tham số, thứ tự queue, nhãn eval hay số liệu. Hoàn tất review vẫn cần REWORK nếu còn RECAPTURE.
- Giữ bản metric contract đã khóa tại reports/protocol_metric_contract.md, đối chiếu hash gốc không đổi. Bản hiện hành giữ trình bày đã sửa, sửa đúng tên và phân biệt ngày khóa protocol với ngày xác nhận review. Verifier so tất cả hàng khai báo kỹ thuật với bản gốc, chỉ cho phép thay dòng xác nhận.
- Giao diện offline dùng hướng dẫn Sites local-only; kiểm thử Chromium/Playwright đã được người dùng cho phép.

## Thay đổi và kiểm chứng
### Công cụ review
- `src/common/contact_sheet.py` và `src/common/review_ui/`: sidebar quy trình 5 bước, tiến độ, tìm kiếm/lọc, ảnh phóng to, ghi chú nhiều dòng, lưu/khôi phục nháp, nhập/xuất CSV và kiểm tra trước xuất.
- Giữ API dùng chung cho ảnh before/after, bounding box, đường dẫn không nhúng và trường metadata tùy chọn. Escape HTML/JSON để nội dung metadata không trở thành mã thực thi.
- Nhập CSV kiểm đủ ID/metadata gốc và xử lý nguyên tử; không thay một phần khi file không hợp lệ. Xuất đủ 20 dòng dù đang lọc. Nháp không tự sửa repository.
- `tools/t02_review_ui.py`, `make review-ui`, `make demo`: lệnh tạo UI và slides offline.

### Xác nhận, pipeline và report
- `tools/t02_human_review.py`: tạo/kiểm bản xác nhận mới, CSV hiện hành, checksum liên kết lần nhập trước. `reports/evidence/human_review/` là lần chạy hiện tại; `reports/evidence/poc/` và biên nhận nhập CVAT giữ nguyên.
- `configs/lab.yaml`: owner Vũ Duy Khanh, `human_review_confirmed=true`; params không đổi. Pipeline gốc và baseline giữ checksum freeze.
- `tools/t02_cvat_review.py`, `tools/t02_submission.py`: kiểm cả lịch sử và lần ký duyệt mới, tái lập review đã xác nhận, từ chối ghi đè công việc có sẵn.
- `reports/review_queue.csv`: 20 reviewer là Vũ Duy Khanh, 18 approve và 2 edit. Nhận xét giữ nguyên CVAT. Quyết định 19 RECAPTURE / 1 KEEP; `n_human_reviewed=20`; REWORK / QUALITY_RECAPTURE_REQUIRED.
- Audit/decision log giữ nguyên toàn bộ tiền tố lịch sử và thêm lần ký duyệt mới. Không đổi score, ranking, eval labels hay các metric.
- Report giữ câu hỏi/đề mục/bảng gốc. Giữ deadline học viên điền 11:00 15/11/2026 và kế hoạch cải tiến; phục hồi hàng Member 2–6 bằng “Không áp dụng” để đúng template nhóm một người.
- Sửa bảng đóng góp về đúng 8 cột: Git author Duy Khanh, GitHub handle o0DzeroK0o, member Vũ Duy Khanh. Không tự đổi Git identity.
- Cập nhật README, hướng dẫn chạy/CVAT/checklist, nguồn nhãn và generator; bỏ lời kể về tác giả thực hiện trong UI, slides và report hiện hành. Giữ metadata nguồn nhãn và sự kiện lịch sử chính xác.

### Demo thay thế
- Theo yêu cầu bổ sung, thay toàn bộ `demo/t004_demo.html` bằng bố cục 5 slide mới (màu sáng, xanh đậm/teal); xóa `demo/t004_demo_preview.png` cũ.
- `tools/t02_demo.py`, `tools/demo_assets/demo.css`: sinh deck từ số liệu đã lưu, bản xác nhận và screenshot thật.
- `demo/ui/`: 4 ảnh chụp Chromium mới — workspace, hai override, xuất CSV, mobile.
- `demo/slides/`: 5 ảnh chụp slide mới. Gallery 20 frame CVAT và XML gốc giữ để kiểm chứng; đây là bằng chứng Save/export, không phải bản trình chiếu cũ.
- Cập nhật kịch bản showcase và demo README. Không khai báo đã trình bày/debate khi chưa có xác nhận.

### Lệnh và kết quả thực tế
| Kiểm tra | Kết quả |
|---|---|
| `.venv/bin/python -m tools.t02_human_review --statement 'Đã xem đủ 20 frame và đồng ý kết quả này'` | Lần ghi ban đầu chạy pipeline exit 0, runtime 0.8067s; 20 human reviews, REWORK. Chạy lại chỉ kiểm bản đã lưu. |
| `PLAYWRIGHT_MODULE=/home/dzerok/lemo-opuscar/node_modules/playwright-core node tools/test_review_ui.cjs` | PASS 12 nhóm thao tác, mở đủ 20 ảnh; CSV nguyên vẹn; tìm kiếm/lọc, chặn thiếu tên/override sai, nháp, round-trip dấu phẩy/ngoặc kép/xuống dòng/Unicode, từ chối CSV khác queue; không lỗi JS; mobile 390px không tràn ngang. |
| `PLAYWRIGHT_MODULE=/home/dzerok/lemo-opuscar/node_modules/playwright-core node tools/test_demo.cjs` | PASS 5 slide 1440×1000, 17 liên kết local, ảnh đầy đủ, nút/phím chuyển slide, mobile 390px; không lỗi JS. Đã xem trực quan cả 5 ảnh chụp. |
| CSV tải từ trình duyệt → `python -m src.main --output out/ui-test/pipeline --run-name browser_csv --offline --seed 42` (trong .venv) | Exit 0; 20/20 human reviews, REWORK; verifier kiểm hành động/audit/score khớp. Các sửa thử UI chỉ ở out/ui-test. |
| `.venv/bin/python -m tools.t02_submission --output out/final-ui-reproduce --reports out/final-ui-reproduce/reports` | Exit 0; đối chiếu đúng 4 raw prediction tables, toàn bộ metric arrays và analysis/bootstrap; bản signed CSV giống từng byte; REWORK. Runtime/timestamp có thể khác. |
| `.venv/bin/python -m pytest -o addopts= -q` | **120 passed, 39 skipped in 8.64s**. Skip do không có overlay GT giảng viên. |
| `make preflight verify` | 0 FAIL / 2 WARN (dữ liệu thật và model tùy chọn chưa có); 14 manifests, 0 failing. |
| `.venv/bin/python -m compileall -q src tools tests`; `node --check` JS | PASS. Repo không cấu hình lint/typechecker riêng; HTML/JS buildless được kiểm cú pháp và trình duyệt. |
| `.venv/bin/python -m tools.t02_verify --write-manifest` | PASS sau khi rà diff: protocol, metric evaluator, score bất biến, template, liên kết, contributions, 20 frame CVAT, xác nhận mới và hash. CSV chuẩn hóa LF. |

Lỗi phát hiện trong quá trình kiểm và cách xử lý:
- Lần test tập trung trước cập nhật manifest: 55 passed / 1 failed vì hash artifact mới chưa được ghi. Đã rà diff rồi cập nhật manifest, full suite pass.
- Lần kiểm chuyển slide đầu đọc chỉ số trước khi sự kiện scroll hoàn tất; kiểm thử được sửa để chờ trạng thái hiển thị, sau đó cả nút và Home/End pass.
- `git diff --check` phát hiện CRLF ở dòng decision log mới; bước chuẩn hóa CSV LF của manifest đã xử lý, lịch sử/nội dung không đổi.
- Một lệnh so sánh dùng Python hệ thống thiếu pandas; chạy lại bằng `.venv/bin/python` thành công. Không thay dependency hoặc hạ kiểm tra.
- Sau cập nhật số test vào report, chạy lại 5 test report: 5 passed in 1.93s; kiểm staged diff không còn lỗi khoảng trắng.

## Hạn chế và bàn giao
- Review người học đã xác nhận, không còn chờ. Chưa có GT giảng viên; xác nhận 20 frame không xác nhận toàn bộ 40 nhãn eval.
- REWORK là kết quả đúng vì còn ảnh cần thu lại. OOD chỉ là 10 ảnh synthetic, không chứng minh dữ liệu thực.
- Chưa push/nộp remote; không đổi hai tag lịch sử. Cần người học quyết định tag/version nộp theo yêu cầu lớp và trình bày thực tế.
- `.obsidian/` giữ nguyên ngoài commit. Các bản sửa ban đầu được sao lưu trước khi chỉnh tài liệu.
- Mở: `make demo`, rồi `omarchy launch browser "file://$PWD/reports/contact_sheet.html"` và đường dẫn `demo/t004_demo.html` tương tự.
