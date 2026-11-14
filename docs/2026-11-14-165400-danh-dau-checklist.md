# Đánh dấu checklist đã đạt — T004

## Mục tiêu
Đánh dấu rõ các mục đã đạt để học viên nhận ra việc còn phải xử lý.

## Hiện trạng trước nhiệm vụ
- HEAD `83ca5cc`; repository độc lập, đã có workflow, không khởi tạo lại.
- Người dùng có thay đổi định dạng bảng References trong `reports/group_report.md` và thư mục `.obsidian/` chưa track. Giữ nguyên, không stage vào commit nhiệm vụ này.
- Report đã tích 4/5 mục; mục reviewer còn chờ người thật. Không sửa report.

## Thực hiện và quyết định
- Đối chiếu config, output 96 ảnh, 20 quyết định AI, `n_human_reviewed=0`, kết quả 69 passed / 39 skipped và hai annotated tag cục bộ.
- `HUONG_DAN_HOC_VIEN.html`: checkbox hiển thị trực tiếp 6/7 mục riêng T02 và 6/8 mục trước khi nộp, giữ nguyên câu chữ tiêu chí, thêm lý do ở mục chưa đạt.
- Checklist Markdown dùng `[x]` / `[ ]`, tách rõ việc tạo tag đã xong khỏi việc xác nhận thời điểm lớp; giữ review người thật, thông tin/deadline và push/nộp chưa hoàn tất.
- Không thay code pipeline, metric, số liệu, tag cũ hoặc lịch sử Git.

## Tệp thay đổi
`HUONG_DAN_HOC_VIEN.html`, `docs/HUONG_DAN_HOAN_TAT_T004.md`, `docs/README.md`, nhật ký này.

## Xác minh
Chỉ thay tài liệu và hiển thị trạng thái nên không thêm test hành vi thuật toán.

- Parser `html.parser.HTMLParser`: PASS, đúng trạng thái 6/7 và 6/8; toàn bộ câu chữ tiêu chí gốc còn nguyên. Các liên kết trong mục lục docs đều tồn tại.
- SHA-256 của report khớp bản ghi đầu nhiệm vụ: PASS. Không sửa hoặc stage report/thư mục `.obsidian/` của người dùng.
- Chromium headless chụp phần checklist trước khi nộp tại `/tmp/t004-checklist.png`: exit 0; đã xem ảnh, đủ 8 mục, dấu tích và ghi chú rõ, không tràn chữ.
- `git diff --check` mặc định ban đầu exit 2 vì ký tự CR cuối dòng của HTML vốn dùng CRLF. Giữ nguyên kiểu xuống dòng của bản gốc; `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check -- HUONG_DAN_HOC_VIEN.html docs/HUONG_DAN_HOAN_TAT_T004.md docs/README.md`: exit 0. Kiểm riêng bằng Python xác nhận toàn bộ HTML vẫn CRLF và cả bốn tệp nhiệm vụ không có dấu cách/tab thừa cuối dòng. Không đổi cấu hình Git.
- Tạo snapshot bằng `git archive HEAD` tại `/tmp/t004-checklist-validation-6icl8532`, chép đè đúng bốn tệp tài liệu nhiệm vụ. Không đưa report đã sửa của người dùng vào snapshot; kết quả dưới đây áp dụng cho bản commit dự kiến, không chứng nhận hash của report đang sửa trong workspace.
- Từ snapshot, dùng interpreter `.venv/bin/python` tuyệt đối của repository và `MPLCONFIGDIR=/tmp/t004-matplotlib`: `-m pytest -o addopts= -q` → **69 passed, 39 skipped in 5.56s**. Các skip cần GT giảng viên.
- Cùng snapshot: `-m tools.t02_verify` → PASS, exit 0; `-m compileall -q src tools tests` → exit 0. Dự án không có lint/typecheck/build riêng.

## Hạn chế / bước tiếp
Chưa thể xác nhận review người thật hoặc mốc giờ lớp. Chưa push/nộp. Report người dùng đã thay định dạng nên không cập nhật hash bằng chứng theo thay đổi không thuộc nhiệm vụ; kiểm bộ test trên snapshot commit cộng đúng các tài liệu của nhiệm vụ, không hoàn tác report để làm test pass.
