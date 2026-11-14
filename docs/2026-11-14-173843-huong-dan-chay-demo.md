# Hướng dẫn chạy demo T004

## Mục tiêu
Hướng dẫn mở bản trình chiếu và chạy pipeline thật trên máy hiện tại.

## Hiện trạng và quyết định
- HEAD đầu nhiệm vụ `3dbd27a`; có thay đổi của người dùng tại `reports/group_report.md` và thư mục `.obsidian/` chưa track. Giữ nguyên, không stage.
- Đọc Makefile, config, CLI, kịch bản showcase và hướng dẫn review hiện có.
- Dùng `make run OUT=out/demo-live` để luyện demo ở thư mục output riêng; bản trình chiếu mở trực tiếp bằng trình duyệt.
- Chỉ thêm tài liệu; không sửa report, code, cấu hình, bằng chứng hay tag.

## Tệp thay đổi
`docs/HUONG_DAN_CHAY_DEMO_T004.md`, nhật ký này và `docs/README.md`.

## Xác minh
- `.venv/bin/python --version`: Python 3.12.16.
- `make run OUT=out/demo-live`: exit 0, runtime pipeline 0.6232 giây, offline, 96 ảnh / pool eval 40 / queue 20. `run_info.json`: output tồn tại, không thiếu cột. `decision.json`: HOLD / HUMAN_REVIEW_REQUIRED, 0 human review.
- Parser HTML: PASS, 5 trang, ảnh nhúng, các liên kết cục bộ tồn tại và có mã điều hướng bằng mũi tên/PageUp/PageDown. Không mở cửa sổ trình duyệt mới trong nhiệm vụ hỏi cách chạy này.
- Chỉ thay tài liệu, không thêm test thuật toán. Snapshot `git archive HEAD` cộng đúng ba tệp tài liệu nhiệm vụ tại `/tmp/t004-demo-guide-validation-0fn5ovpz`: dùng interpreter `.venv/bin/python` tuyệt đối chạy `-m pytest -o addopts= -q`, **69 passed, 39 skipped in 5.03s**. Các skip cần GT giảng viên. Snapshot không lấy report đang sửa của người dùng; kết quả test áp dụng cho bản dự kiến commit.
- Kiểm tra output bằng Pandas: 96 dòng ranking, 40 dòng eval, queue đúng top20 của eval; ID/score khớp snapshot bằng chứng. Review state khác vì lần chạy luyện demo chưa có quyết định review. Assertion kiểm tra ban đầu nhầm ranking chỉ có 40 dòng và thất bại; đọc lại contract/mã rồi kiểm đúng 96 đầu vào, 40 eval. Không thay pipeline hay output để làm kiểm tra pass.
- Kiểm liên kết tài liệu và whitespace: PASS. `make -n t02-submission OUT=out/demo-comparison`: exit 0, trỏ đúng thư mục riêng; đây là kiểm tra lệnh, không chạy lại toàn bộ so sánh trong nhiệm vụ này. `git diff --check`: exit 0. Không có lint/typecheck/build riêng cho thay đổi tài liệu.

## Hạn chế / bước tiếp
Người dùng mở demo và tự thao tác review theo hướng dẫn. Chưa xác nhận review người thật, deadline hay push/nộp. Các file output luyện demo được ignore, không đưa vào commit. Report người dùng đang sửa nằm ngoài nhiệm vụ; không cập nhật hash bằng chứng để hấp thụ thay đổi đó.
