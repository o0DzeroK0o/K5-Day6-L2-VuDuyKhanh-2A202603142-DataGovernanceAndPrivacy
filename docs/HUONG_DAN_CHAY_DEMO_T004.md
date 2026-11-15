# Chạy pipeline web và demo T004

## Khởi động ứng dụng

Tại gốc repository, giữ terminal này chạy:

```bash
make web
```

Mở **http://127.0.0.1:8765** trong trình duyệt. Có thể dùng terminal khác:

```bash
xdg-open http://127.0.0.1:8765
```

Ứng dụng HTTP gọi Python để thực thi từng bước và lưu kết quả trên máy chủ local. Không cần Internet trong lúc xử lý. Đây là địa chỉ trên máy đang chạy lệnh, chưa triển khai lên hosting công khai. `out/poc/contact_sheet.html` và `reports/contact_sheet.html` là bản review HTML riêng, không có máy chủ để chạy năm bước.

Lệnh tương đương: `.venv/bin/python -m src.web_app --port 8765 --output out/web`. Nếu cổng đang được dùng, mở trang đang chạy hoặc chọn `make web PORT=8766 OUT=out/alternate` rồi mở cổng mới. Dừng bằng **Ctrl+C**; kết quả đã lưu vẫn còn. Khởi động lại với cùng `OUT` để mở lại lịch sử.

Máy mới cần Python 3.12 và dependency trước lần đầu:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
make web
```

## Thao tác đủ năm bước

1. **Lượt mới → Load → Nạp dữ liệu**: đọc 96 ảnh synthetic, metadata và kiểm manifest SHA-256. Gallery hiện ảnh đã nạp.
2. **Process → Chạy Process**: tính độ nét, độ sáng, lóa ROI, blockiness JPEG và score từ pixel. Xem 96 dòng tín hiệu; tải `raw_predictions.csv` để đối chiếu.
3. **Rank → Xếp hạng queue**: chọn top 20 trên pool 40 ảnh eval. Bấm mã ảnh để chuyển tới Review của frame đó.
4. **Review**: chọn từng frame 01–20, bấm ảnh để phóng to, nhập người review và quyết định. Sửa/từ chối phải có KEEP hoặc RECAPTURE cùng nhận xét. Bấm **Lưu review lên máy chủ**. Nếu đã trực tiếp xem và chịu trách nhiệm cho các quyết định đang nhập, tích ô xác nhận trước khi lưu.
5. **Decide → Chạy Decide**: áp policy trên review đã lưu và tạo decision, CSV, audit. Có thể tải file từ “Kết quả và lịch sử thực thi”.

Bản duyệt CVAT của **Vũ Duy Khanh** đã được xác nhận đủ 20 frame. Để trình diễn lại kết quả này, sau Rank bấm **Nạp 20 quyết định đã xác nhận**, rồi chạy Decide. Máy chủ kiểm queue, điểm, ảnh và biên nhận trước khi nhập. Kết quả: **19 RECAPTURE, 1 KEEP (`img_23_1`)**, hai override `img_19_2`, `img_06_3`, batch **REWORK / QUALITY_RECAPTURE_REQUIRED**. Không phải xác nhận lại cho cùng bằng chứng.

Một lượt mới bắt đầu chưa xác nhận. Review chưa đủ hoặc chưa xác nhận sẽ cho HOLD; `escalate` cũng cho HOLD. Sửa dữ liệu trong form bỏ dấu xác nhận và khóa Decide cho đến khi lưu. Bản review mới không tự kế thừa xác nhận CVAT. Máy chủ kiểm dữ liệu lần nữa, giữ nguyên nháp khi yêu cầu bị từ chối và báo khi tab đang dùng phiên bản cũ.

## Kết quả lưu ở đâu

Mỗi lượt có một thư mục `out/web/<run_id>/`. `current.json` trỏ tới phiên bản hiện hành trong `revisions/`; mỗi bước tạo một phiên bản mới. Chọn lượt ở góc trên bên phải để mở lại. Lịch sử bước, thời gian thực thi và audit hiện trên giao diện. Chỉ chạy một server cho mỗi thư mục output; dùng `OUT=out/thu-nghiem` nếu cần server riêng.

| Bước | File tải được sau khi hoàn tất |
|---|---|
| Load | `loaded_images.csv`, `loaded_manifest.csv` |
| Process | `raw_predictions.csv` |
| Rank | `review_queue.csv` |
| Review | `review_queue_reviewed.csv`, `ranked_review.csv`, `item_decisions.csv`, `review_confirmation.json`, `audit_log.jsonl` |
| Decide | `decision.json`, `decision_log.csv` |
| Mọi bước | `workflow.json`, `run_info.json` |

Review thay đổi sẽ làm decision hiện hành hết hiệu lực; bấm Decide để tính lại. Phiên bản cũ và decision log vẫn được giữ. Xóa `out/web/` sẽ xóa các lượt chạy local, vì vậy sao lưu các file cần nộp trước khi dọn thư mục.

Các lượt chạy web không tự ghi đè report đã ký duyệt, metric, nhãn hoặc cấu hình đã khóa. Xác nhận chỉ bao phủ 20 frame review, không phải toàn bộ 40 nhãn eval.

## Slides và ảnh demo

```bash
make demo
xdg-open demo/t004_demo.html
xdg-open demo/web/index.html
```

- [5 slides mới](../demo/t004_demo.html) dùng ảnh thực thi HTTP và CVAT local; phím **← / →**, **PageUp / PageDown**, **Home / End** để chuyển slide.
- [Ảnh đủ năm bước web](../demo/web/index.html), [kết quả kiểm thử trình duyệt](../demo/web/verification.json), [decision tải từ server](../demo/web/decision.json).
- [20 frame CVAT local](../demo/cvat/index.html), [XML export](../demo/cvat/annotations.xml), [xác nhận trực tiếp](../reports/human_review_confirmation.json).
- [Ảnh 5 slide](../demo/slides/). Bản trình chiếu cũ đã được thay tại cùng đường dẫn.

`make demo` dựng lại tài liệu minh họa từ bằng chứng đã lưu. `make web` khởi động ứng dụng tương tác.

## Tái lập và kiểm thử

```bash
make t02-submission OUT=out/demo-new
make test
make preflight verify
.venv/bin/python -m tools.t02_human_review
.venv/bin/python -m tools.t02_web_demo
.venv/bin/python -m tools.t02_verify
```

Kiểm thử web bằng Chromium, tự chạy một server riêng và lưu file vào `out/web-ui-test/`:

```bash
PLAYWRIGHT_MODULE=/home/dzerok/lemo-opuscar/node_modules/playwright-core node tools/test_web_ui.cjs
```

Máy khác đặt `PLAYWRIGHT_MODULE` tới package Playwright đã cài và `CHROMIUM_PATH` tới Chromium. Để chủ động cập nhật ảnh demo từ server đang chạy, dùng thêm `WEB_BASE_URL=http://127.0.0.1:8765 WEB_CAPTURE_DIR=demo/web`, kiểm tra ảnh/diff rồi `make demo`. Không cập nhật manifest trước khi đối chiếu kết quả.
