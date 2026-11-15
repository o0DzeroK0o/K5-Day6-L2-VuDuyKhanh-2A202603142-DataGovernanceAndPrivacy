# Web app chạy thật năm bước pipeline

## Mục tiêu
Thay luồng chỉ mở HTML bằng ứng dụng HTTP trên localhost: Load → Process → Rank → Review → Decide đều gọi xử lý máy chủ và lưu kết quả. Người dùng thao tác ngay trên trình duyệt.

## Ban đầu và quyết định
- HEAD `d133c47`; working tree chỉ có `.obsidian/` không thuộc nhiệm vụ. Quy trình Git/docs đã đủ.
- Thuật toán `src/pipeline.py`, baseline, tham số và protocol đã khóa: không sửa. Gọi trực tiếp năm hàm qua worker riêng; giữ GT guard/offline guard trong worker, HTTP phục vụ giao diện local.
- Mỗi lượt chạy có output riêng trong `out/web/`, không ghi đè báo cáo đã ký duyệt. Các revision giữ lịch sử; kiểm phiên bản trước khi lưu để tránh ghi đè giữa hai tab.
- Xác nhận 20 frame hiện có được nhập từ biên nhận đã kiểm chứng. Một lượt mới không tự được xác nhận chỉ vì có tên người review.
- Dùng Python HTTP server tiêu chuẩn và HTML/CSS/JS có sẵn; không thêm dịch vụ cloud, dependency hoặc đăng nhập.

## Thực hiện và kiểm chứng
- Đã xây dựng `src/web_app.py`, `src/web_worker.py` và `src/web_ui/`: API tạo/chọn lượt, thực thi từng stage, xem ảnh, tải artifact; giao diện đủ năm bước, 20 frame, phóng to, lưu form, nhập xác nhận, history/audit và màn hình nhỏ.
- Mỗi bước chạy worker có GT/offline guard; input được đối chiếu hash trước các stage sau Load. Revision bất biến và pointer cập nhật nguyên tử; khóa theo lượt, kiểm revision chống ghi đè từ tab cũ. Review lỗi không thay trạng thái đã lưu.
- Chạy thật qua backend: 96 ảnh load/process, pool 40 eval, queue 20; import đúng biên nhận đã ký, Decide REWORK. Byte của `raw_predictions.csv` khớp bằng chứng freeze.
- Thêm `make web`, hướng dẫn thao tác HTTP, thay liên kết chính trong README. Đồng bộ hai checkbox review còn cũ trong hướng dẫn học viên theo xác nhận đã có; giữ nguyên đề mục và câu checklist.
- Cập nhật năm slide bằng ảnh web và CVAT, tạo gallery `demo/web/` với output tải trực tiếp từ server. Không tạo dữ liệu minh họa giả. Lượt demo sạch có đúng năm bước và 20 sự kiện review đã xác nhận; các thử nghiệm HOLD, nhập sai và mất kết nối nằm trong lượt khác. Bản trình chiếu trước được thay tại cùng đường dẫn, giữ bằng chứng CVAT gốc.
- Kiểm thử Python chuyên biệt ban đầu: 23 test pass; sau đó bổ sung kiểm audit khi xóa quyết định để chạy cùng full suite.
- Chromium đã chạy đủ năm bước, mở 20/20 frame, kiểm zoom, nhập sai, partial review HOLD, nhập xác nhận, conflict, bỏ xác nhận khi sửa, tải lại trang, tải file và năm view ở 390px. Lượt kiểm chứng cuối lưu trong `demo/web/verification.json`; đã pass cả chế độ server đang chạy và server test tự khởi động riêng.


## Kết quả xác minh cuối

| Lệnh / thao tác | Kết quả thực tế |
|---|---|
| `.venv/bin/python -m pytest -o addopts= -q` | **147 passed, 39 skipped in 54.72s**. Skip do thiếu GT giảng viên như trước; không tắt test. |
| `PLAYWRIGHT_MODULE=/home/dzerok/lemo-opuscar/node_modules/playwright-core WEB_BASE_URL=http://127.0.0.1:8765 WEB_CAPTURE_DIR=demo/web node tools/test_web_ui.cjs` | Pass đủ năm bước, 20 frame, lưu/khôi phục/tải kết quả; không lỗi JavaScript, không request ra dịch vụ ngoài. |
| Cùng browser test, bỏ `WEB_BASE_URL`/`WEB_CAPTURE_DIR` | Pass với server cổng tạm do script tự khởi động rồi đóng; bằng chứng test riêng nằm trong `out/web-ui-test/`. |
| Dừng và khởi động lại server thật, GET lượt đã lưu | Revision, 20 review và decision khớp trước khi restart. |
| `make demo` và `node tools/test_demo.cjs` với Playwright | Pass. 5 slide 1440×1000 không tràn; ảnh tải đủ, nút/phím chuyển slide và 390px pass. Đã xem ảnh render. |
| `make preflight verify` | **0 FAIL / 2 WARN** (data/model tùy chọn), **14 manifests, 0 failing**. |
| `.venv/bin/python -m compileall -q src tools tests`; `node --check` hai tệp JS mới | Pass. Dự án không có cấu hình linter/typecheck riêng. |
| `.venv/bin/python -m tools.t02_human_review` | 20/20 xác nhận của Vũ Duy Khanh, REWORK / QUALITY_RECAPTURE_REQUIRED. |
| `.venv/bin/python -m tools.t02_verify --write-manifest` | Pass protocol, metrics/evaluator, ảnh CVAT, pipeline web, template report và hash evidence. Chỉ cập nhật manifest sau khi đối chiếu thay đổi. |
| Đối chiếu Git HEAD và raw prediction | Pipeline, baseline, tham số, khai báo protocol giữ nguyên; prediction của web trùng byte với snapshot. |
| Kiểm liên kết Markdown | 74 liên kết local tồn tại; link slide cũng được kiểm trong Chromium. |
| `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check` | Pass; giữ CRLF gốc của hướng dẫn HTML. Lệnh diff mặc định trước đó báo CR cuối dòng ở bốn dòng vừa sửa; không có khoảng trắng thừa trong nội dung. |

Kiểm thử đã phát hiện ảnh gallery bị chụp trước khi tải xong; sửa bộ chụp đợi ảnh thực tải và giao diện tránh dựng lại gallery khi chỉ đổi bước. Kiểm thêm nội dung nhận xét dạng số: giữ chuỗi, không mất số 0 đầu khi lưu CSV rồi tải lại. Xóa quyết định cũ có sự kiện audit riêng và quay về HOLD nếu thiếu review.

Sau khi cập nhật số liệu kiểm thử vào report: `.venv/bin/python -m pytest -o addopts= -q tests/test_t02_report.py` pass **7 tests**; verifier và manifest pass lại.

## Tệp thay đổi và bàn giao

- Backend: `src/web_app.py`, `src/web_worker.py`; frontend: `src/web_ui/`; `Makefile` thêm `web`.
- Test: `tests/test_web_app.py`, test report/demo liên quan và `tools/test_web_ui.cjs`; verifier mới `tools/t02_web_demo.py`.
- Hướng dẫn: README, hướng dẫn chạy/hoàn tất, checklist học viên, mục lục docs. Report cập nhật phần trả lời qua generator, giữ câu hỏi/đề mục/bảng/checklist.
- Demo: thay nội dung `demo/t004_demo.html` và ảnh `demo/slides/`, thêm `demo/web/` (ảnh gốc và file tải từ server), cập nhật kịch bản showcase, verification và manifest. Bằng chứng CVAT và xác nhận gốc giữ nguyên.

Server bàn giao chạy tại **http://127.0.0.1:8765**. Khởi động lại bằng `make web`; trong Review có nút nhập đúng 20 quyết định đã được xác nhận. Lượt web mới không tự sửa report đã ký duyệt. Các file output trong `out/` không đưa vào Git; chỉ sao chép bằng chứng demo đã xác minh vào `demo/web/`.

Phạm vi hiện tại là HTTP localhost với fixture T02 sẵn có, chưa public hosting. GT chính thức, giờ tag theo lớp và việc nộp remote vẫn chưa xác minh; không thay tag, không push. `.obsidian/` không thuộc nhiệm vụ và không stage.
