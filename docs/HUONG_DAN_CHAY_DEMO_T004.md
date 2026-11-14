# Chạy demo T004 / T02

Mở Terminal tại thư mục gốc dự án. Máy hiện tại đã có `.venv` và dependency; các lệnh dưới đây chạy offline.

## 1. Mở bản trình chiếu 5 trang

```bash
xdg-open demo/t004_demo.html
```

Dùng phím **→ / ←** hoặc **PageDown / PageUp** để chuyển trang, **F11** để bật toàn màn hình trình duyệt. Có thể mở file bằng trình quản lý tệp rồi chọn Chrome/Chromium. Không cần chạy web server.

Lời thuyết trình có trong [SHOWCASE_SCRIPT.md](../demo/SHOWCASE_SCRIPT.md). Các trang và liên kết trong bản trình chiếu là bằng chứng đã lưu; để xem lần chạy mới, mở contact sheet ở bước 2.

## 2. Chạy pipeline thật và xem ảnh

```bash
make run OUT=out/demo-live
xdg-open out/demo-live/poc/contact_sheet.html
```

`make` dùng `.venv/bin/python`, không cần activate môi trường. Kết quả nằm trong `out/demo-live/poc/`:

- `ranked_review.csv`: xếp hạng ảnh theo điểm nghi lỗi.
- `contact_sheet.html`: giao diện xem 20 ảnh ưu tiên và nhập review.
- `review_queue.csv`: danh sách 20 ảnh.
- `decision.json`: quyết định HOLD/REWORK/GO cùng lý do.
- `audit_log.jsonl`: nhật ký thao tác.
- `run_info.json`: trạng thái chạy, seed, runtime và kiểm tra output.

Lần chạy sạch hiện tại xử lý 96 ảnh, lấy pool eval 40 ảnh và chọn 20 ảnh review. Terminal báo `status=0` nghĩa là chương trình chạy thành công. `HOLD / HUMAN_REVIEW_REQUIRED` trong quyết định là trạng thái chờ người thật review.

## 3. Trình diễn thao tác review

Trong contact sheet, điền Reviewer, tự xem ảnh rồi chọn quyết định. `approve` đồng ý gợi ý; `edit`/`reject` cần override `KEEP` hoặc `RECAPTURE` và ghi lý do. Bấm **Export decisions CSV**.

Chép file tải về vào `out/demo-live/poc/review_queue_reviewed.csv`, rồi chạy lại:

```bash
make run OUT=out/demo-live
cat out/demo-live/poc/decision.json
tail -n 5 out/demo-live/poc/audit_log.jsonl
```

Audit ghi quyết định; ranking/score giữ nguyên. Nếu đang luyện thao tác mà chưa thực sự review toàn bộ queue, giữ `human_review_confirmed: false` và kết quả HOLD. Để hoàn tất mục review người thật của bài nộp, làm đầy đủ [hướng dẫn hoàn tất, mục 1](HUONG_DAN_HOAN_TAT_T004.md#1-làm-vòng-review-người-thật-khoảng-1015-phút), sử dụng thư mục bài nộp `out/poc/`.

## 4. Tái chạy toàn bộ so sánh (tùy chọn)

```bash
make t02-submission OUT=out/demo-comparison
```

Lệnh tạo baseline Laplacian, PoC, review AI, ablation và số liệu tự kiểm trong `out/demo-comparison/reproduce/`; báo cáo nằm ở thư mục con `reports/`. Số liệu dùng nhãn AI nội bộ, chưa phải điểm GT giảng viên. Bản trình chiếu không tự cập nhật theo lần chạy mới.
