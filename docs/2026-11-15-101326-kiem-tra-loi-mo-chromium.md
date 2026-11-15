# Kiểm tra log Chromium khi mở contact sheet

## Mục tiêu và hiện trạng

Người dùng báo hai dòng `Failed sending zygote boot message` và `write: Ống dẫn bị hỏng (32)` sau hướng dẫn chạy pipeline/mở HTML. Mục tiêu là xác định kết quả pipeline và có cách mở trang kết quả hoạt động trên máy hiện tại.

HEAD đầu nhiệm vụ: `4ab4f4e`; đã kiểm Git/AGENTS. Các thay đổi có sẵn ở `reports/group_report.md`, `reports/metric_contract.md`, `reports/team_contributions.csv` và `.obsidian/` giữ ngoài nhiệm vụ. Dùng hướng dẫn skill Omarchy để đọc launcher hiện có; không sửa file hệ thống hoặc cấu hình trình duyệt.

## Kết quả kiểm tra và quyết định

- `out/poc/run_info.json` do lần chạy của người dùng ghi lúc 10:12:57 ngày 2026-11-15: `status=0`, runtime `0.6079s`, output tồn tại, `missing_columns=[]`. `decision.json` là HOLD / HUMAN_REVIEW_REQUIRED. Đây là kết quả pipeline thành công, tách với log tiến trình trình duyệt.
- `out/poc/contact_sheet.html` tồn tại, có 20 card và 20 ảnh nhúng `data:image/...`; không cần web server để tải ảnh.
- Chromium cài trên máy: `155.0.8059.84 Arch Linux`. Handler HTML là `chromium.desktop`, default web browser qua `omarchy-browser.desktop`.
- `hyprctl clients -j`, lọc riêng cửa sổ thuộc bài: đã có cửa sổ mapped `T004 / T02 — poc — eval — review - Chromium`, PID 167846. Vì vậy hai dòng log không ngăn trang này mở trong lần được kiểm tra; không kết luận mọi lỗi zygote đều vô hại.
- Đọc `omarchy-launch-browser`, `omarchy-cmd-browser-handoff` và `omarchy-cmd-default-browser` trong `/usr/share/omarchy/bin/`: launcher có cơ chế gửi URL tới Chromium đang chạy và đưa cửa sổ lên trước. Dùng lệnh Omarchy thay cho việc gọi mở HTML trực tiếp qua handler.
- Chạy `omarchy launch browser "file://$PWD/out/poc/contact_sheet.html"`: exit 0, không có stderr. `hyprctl activewindow -j` sau lệnh xác nhận đúng cửa sổ review đang active, PID 167846, mapped true.

## Tệp thay đổi

- `docs/HUONG_DAN_CHAY_DEMO_T004.md`: thêm mục 6 và chỉ dẫn mở HTML bằng launcher Omarchy, gồm cả đường dẫn `out/poc/`, `out/demo-live/poc/` và slides.
- Nhật ký này và liên kết trong `docs/README.md`.

## Xác minh

- Đọc JSON kết quả chạy: status 0, output đủ cột.
- Parser HTML: PASS 20 card / 20 ảnh nhúng.
- Lệnh mở contact sheet: PASS exit 0; cửa sổ review trở thành cửa sổ hoạt động.
- Kiểm liên kết tài liệu/mục lục và `git diff --check` trước commit.
- Chỉ bổ sung tài liệu và kiểm cách mở trang, không thay source pipeline; không thêm test tự động hoặc chạy lại toàn bộ test thuật toán.

## Hạn chế / bước tiếp

Đã có cách mở trang hoạt động và đã đưa cửa sổ kết quả lên trước. Chưa xác định nguyên nhân chính xác khiến tiến trình zygote của lần gọi cũ mất pipe; không gọi đây là bản sửa Chromium toàn cục. Tra cứu nguồn Chromium qua công cụ web không khả dụng (route 404); kết luận ở trên dựa trên trạng thái máy, output thật và source launcher cài sẵn. Nếu trang không mở ở lần khác, cần lấy log mới cùng trạng thái tiến trình thay vì coi riêng hai dòng log là lỗi pipeline.
