# Chạy công cụ review và demo T004

## Mở giao diện và slides mới

Tại gốc repository:

```bash
make demo
omarchy launch browser "file://$PWD/reports/contact_sheet.html"
omarchy launch browser "file://$PWD/demo/t004_demo.html"
```

`make demo` dựng lại giao diện và 5 slide từ bằng chứng đã lưu, không cần web server hoặc mạng. Trên Linux khác dùng `xdg-open` với hai đường dẫn trên. Cách mở qua launcher Omarchy tránh khởi động thêm một Chromium không cần thiết; [lần kiểm tra lỗi zygote trước đó](2026-11-15-101326-kiem-tra-loi-mo-chromium.md) không xác định nguyên nhân gốc của log broken pipe.

Slides dùng phím **→ / ←**, **PageDown / PageUp**, **Home / End**, hoặc hai nút ở cuối màn hình. Bấm ảnh để mở ảnh gốc. [Ảnh 5 slide mới](../demo/slides/) và [ảnh thao tác UI](../demo/ui/) được chụp bằng Chromium. Bản preview cũ đã xóa.

## Thao tác công cụ review

1. Giao diện mở đủ **20 frame**, người review **Vũ Duy Khanh**, **2 override**, **0 frame cần xem tiếp**.
2. Tìm mã ảnh, nhận xét hoặc nhóm; lọc “Đã sửa đề nghị” để thấy `img_19_2` và `img_06_3`.
3. Bấm ảnh để phóng to; Esc hoặc Đóng để quay lại. Xem thông tin điểm/lý do trong “Thông tin và tín hiệu”.
4. `Đồng ý đề nghị` giữ hành động gợi ý. `Sửa hành động` / `Từ chối đề nghị` cần KEEP hoặc RECAPTURE và nhận xét. `Cần xác minh` / `Bỏ qua` chưa được tính hoàn tất.
5. Nháp tự lưu trên trình duyệt. Dùng “Bỏ bản nháp” để trở lại dữ liệu gốc. Nếu trình duyệt chặn lưu nháp, giao diện thông báo và vẫn xuất CSV được.
6. “Xuất CSV” xuất **toàn bộ 20 frame**, kể cả khi đang lọc. “Nhập CSV” chỉ nhận đủ frame, không trùng ID, không đổi điểm hoặc thông tin queue. File tải về giữ định dạng `review_queue_reviewed.csv`.

Xuất CSV không tự sửa file trong repository. Nháp và thao tác thử không thay bản ký duyệt đã lưu.

## Chạy lại pipeline với review đã xác nhận

```bash
make t02-submission OUT=out/demo-new
cat out/demo-new/reproduce/poc/decision.json
```

Lệnh tái tạo baseline, PoC, review đã xác nhận, ablation và OOD ở thư mục riêng. PoC phải có `n_human_reviewed=20`, **REWORK / QUALITY_RECAPTURE_REQUIRED**. Thư mục có sẵn review sẽ giữ nguyên; để kiểm tra sạch dùng tên thư mục mới.

Chỉ chạy scoring bằng `make run OUT=out/scoring` vẫn tạo đủ output. Nếu chưa có CSV review trong thư mục đó, decision là HOLD vì thiếu review. Mở giao diện đã ký duyệt bằng `make review-ui` thay vì nhầm với queue trống của lần scoring mới.

## Chạy CSV vừa xuất qua pipeline

```bash
mkdir -p out/review-new
cp ~/Downloads/review_queue_reviewed.csv out/review-new/review_queue_reviewed.csv
.venv/bin/python -m src.main --config configs/lab.yaml --output out/review-new --offline --seed 42
cat out/review-new/decision.json
```

Chỉ dùng tên/thời điểm của người đã trực tiếp review; không ghi đè bằng chứng cũ khi luyện thao tác. Lệnh trên chạy ở thư mục mới và không cập nhật report chính. Score/ranking giữ nguyên; kết quả vẫn REWORK khi còn yêu cầu thu lại ảnh.

## Kiểm chứng

```bash
make test
make preflight verify
.venv/bin/python -m tools.t02_cvat_review
.venv/bin/python -m tools.t02_human_review
.venv/bin/python -m tools.t02_verify
```

Kiểm thử UI bằng Node và Playwright có sẵn trên máy:

```bash
PLAYWRIGHT_MODULE=/home/dzerok/lemo-opuscar/node_modules/playwright-core node tools/test_review_ui.cjs
```

Máy khác đặt `PLAYWRIGHT_MODULE` tới package Playwright đã cài và `CHROMIUM_PATH` tới Chromium. Script kiểm tra thật trong trình duyệt, ghi CSV thử vào `out/ui-test/` và cập nhật ảnh trong `demo/ui/`. Sau khi chụp lại, chạy `make demo` và kiểm tra diff trước cập nhật manifest.
