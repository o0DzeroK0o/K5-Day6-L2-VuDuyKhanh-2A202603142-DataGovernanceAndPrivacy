# Khởi tạo quy trình dự án

## Mục tiêu
Bổ sung phần thiếu của quy trình Git/tài liệu trước khi làm T02 cho T004.

## Thực hiện và quyết định
- Repository độc lập đúng cwd, working tree sạch, HEAD ban đầu `b0ce8bf`; không init lại và không sửa lịch sử.
- Có `.gitignore`, chưa có AGENTS/mục lục/nhật ký khởi tạo: thêm các phần thiếu và ignore secrets/caches.
- Khôi phục nguyên byte `HUONG_DAN_HOC_VIEN.html` từ bản cùng tên dự án trong Trash, không đọc/khôi phục lời giải cũ.
- Git identity sẵn có, giữ nguyên. Python hệ thống 3.14 thiếu pip; dùng Python 3.12.16 đã cài và uv cache để cài requirements offline vào `.venv`.
- Đây là thay đổi quy trình/tài liệu, không đổi hành vi mã nguồn nên chưa thêm test.

## Tệp thay đổi
`AGENTS.md`, `.gitignore`, `HUONG_DAN_HOC_VIEN.html`, `docs/README.md`, nhật ký này.

## Xác minh
- `MPLCONFIGDIR=/tmp/t004-matplotlib .venv/bin/python -m pytest -q`: exit 0, test yêu cầu GT tự skip đúng quy định sẵn có.
- `MPLCONFIGDIR=/tmp/t004-matplotlib .venv/bin/python -m tools.preflight`: exit 0, 0 FAIL / 2 WARN (không có dữ liệu thật và model tùy chọn, không cần cho T02).
- Đối chiếu HTML khôi phục bằng bytes: khớp. Liên kết mục lục và ignore secrets/cache: hợp lệ. `git diff --check`: pass.

## Hạn chế / bước tiếp
Không có GT overlay của giảng viên. Tiếp tục triển khai T02 và tự kiểm minh bạch; không giả xác nhận người review hay thời hạn lớp.
