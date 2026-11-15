# Hoàn tất demo CVAT local cho đủ 20 frame

## Mục tiêu và phạm vi

Bổ sung phần còn thiếu trong `demo/`: ảnh chụp thao tác thật trên CVAT local và tích hợp vào bộ 5 slides offline. Yêu cầu cuối của người dùng là làm đủ 20 frame, dùng đúng tên **Vũ Duy Khanh** ở `review_source`, chỉ ghi nhận xét chất lượng trong `review_note`.

Repository gốc đúng thư mục dự án, HEAD đầu nhiệm vụ `351fdf3`. Git, ignore, AGENTS và nhật ký khởi tạo đã đủ nên không khởi tạo trùng. Giữ nguyên chỉnh sửa định dạng bảng References có sẵn trong `reports/group_report.md` và `.obsidian/` chưa track, không đưa vào commit nhiệm vụ này.

Đã đọc `AGENTS.md`, `README.md`, `HUONG_DAN_HOC_VIEN.html`, `docs/tracks/T02.md`. Dùng hướng dẫn thiết kế/kiểm tra của skill Presentations để bổ sung bộ HTML 5 trang hiện có. Không tạo bộ PowerPoint khác với định dạng demo đang dùng.

## Thao tác và quyết định

- Phiên đầu chỉ tới trang đăng nhập. Shell trong sandbox không truy cập được localhost/Docker socket. Computer Use tiếp tục báo `browser access host is unavailable` cả sau khi người dùng kết nối lại. Người dùng cho phép chuyển sang Playwright/Chromium, sau đó môi trường full access truy cập localhost thành công.
- Tiếp tục task **#17** `T004_T02_AI_DEMO`, job **#17**, CVAT **2.82.1**. Input là 20 JPEG synthetic trong queue PoC đã freeze, tên prefix 01–20. Byte ảnh giữ nguyên, SHA-256 bundle `0294bee490ecb7f475ada8247ba4f7e3681bb53da9a985d945473203ff7bb918`.
- Xem đủ 20 ảnh, gán tag cấp ảnh và Save qua giao diện. Cả 20 frame 0–19 có đúng một tag. Kết quả **19 RECAPTURE / 1 KEEP**; KEEP là frame 18 / rank 19 / `img_23_1`. Hai override từ KEEP: `img_19_2`, `img_06_3`.
- Người dùng xác nhận cách viết **Vũ Duy Khanh**. Đã cập nhật đủ 20 tag và default của cả hai label. `review_note` chỉ có lỗi/nhận xét quan sát. Không còn “AI” trong hai trường này.
- Trợ lý AI thực hiện thao tác. Ghi provenance riêng trong tài liệu và `evidence.json`: `operator: AI:Codex`, `human_review_confirmed: false`. Tên thuộc tính được điền theo chỉ định, không tự xác nhận học viên đã trực tiếp review.
- Chỉ Finish the job sau khi đủ 20/20; API trả `state=completed`. Mở lại kiểm nhãn, chụp riêng từng frame. Trạng thái CVAT này không đổi HOLD của pipeline.
- Export lại toàn bộ job bằng **CVAT for images 1.1**, tắt Save images, đợi Requests Finished 100% và Download. Bản cuối thay bản 3 frame tạm của giai đoạn đầu. XML 20 image/20 tag khớp toàn bộ annotation và thứ tự ảnh trong API.
- Đóng gói XML đã bỏ metadata owner/assignee, mapping, snapshot API đã chọn trường, metadata và gallery. Giữ SHA-256 ZIP/XML gốc để truy xuất, không commit file tài khoản/phiên đăng nhập. Gói ZIP gốc và output chuẩn bị nằm trong `out/`, được ignore.
- Sửa generator và sinh lại đúng 5 slides: task/pipeline, review sau Save, export, metric/failure case, tổng kết và bàn giao. Screenshot thật được embed vào HTML, có link bản đầy đủ và gallery 20 frame. Preview là ảnh chụp trang đầu đã cập nhật.
- Không sửa thuật toán/ngưỡng/score/metric, không đọc GT giảng viên. Annotation CVAT chưa nhập vào pipeline. Không sửa report hay release tag có sẵn, không push.

## Tệp thay đổi

- `demo/cvat/`: 20 ảnh từng frame, 7 ảnh thao tác/tổng kết, XML, mapping, snapshot API, evidence JSON, gallery HTML.
- `tools/t02_cvat_demo.py`: đóng gói export, loại metadata tài khoản, kiểm khớp API và frozen queue, đủ frame/tag/thuộc tính, checksum ảnh gốc và screenshot.
- `tools/t02_artifacts.py`: sinh 5 slides có bằng chứng CVAT từ package đã xác minh; giữ metric đọc từ summary.
- `tools/t02_verify.py`: tích hợp kiểm package CVAT vào kiểm tra bài nộp.
- `tests/test_t02_cvat_demo.py`: kiểm package hợp lệ và các tình huống thiếu/trùng frame, sai nguồn/ghi chú, lệch mapping/hash, thiếu screenshot, metadata/API không nhất quán, loại metadata tài khoản, và HTML nhúng đúng screenshot.
- `demo/t004_demo.html`, `demo/t004_demo_preview.png`, `demo/SHOWCASE_SCRIPT.md`: bộ trình chiếu và kịch bản cập nhật.
- `README.md`, `docs/HUONG_DAN_DEMO_CVAT_LOCAL.md`, `docs/HUONG_DAN_CHAY_DEMO_T004.md`, `docs/README.md`, nhật ký này: trạng thái 20/20, cách mở và kiểm bằng chứng, phần còn chờ người học.
- `reports/evidence_manifest.json`: chỉ cập nhật/thêm hash `demo/`, giữ nguyên hash mọi `reports/`, đặc biệt report đang được người dùng sửa ngoài phạm vi.

## Xác minh thực tế

- Chuẩn bị input: đối chiếu top20, ID/rank/split và SHA-256 ảnh; ZIP round-trip **PASS**. Queue score làm tròn 6 chữ số theo `src/common/review.py`; giữ raw score riêng, không thay dữ liệu/score.
- CVAT UI/API sau Save: **20 frame riêng biệt, 20 tag**, đúng tên, không “AI” trong review fields, job completed. Export Download trả `failure: null`.
- `.venv/bin/python -m tools.t02_cvat_demo --export out/cvat-demo/t004_cvat_local_final.zip`: **PASS**, 20/20 frame, 19 RECAPTURE / 1 KEEP. So XML với snapshot API đã lưu.
- `.venv/bin/python -m tools.t02_artifacts`: **PASS**, sinh 5 slides và giữ nguyên failure gallery/số liệu cũ.
- Chromium offline: 5 section, 6 ảnh slide decode thành công, chuyển sang slide 2 bằng ArrowRight, 20 ảnh gallery decode thành công, **0 HTTP(S) request**. Cả 5 slide rộng 1425, cao 1000 ở viewport 1440×1000, không tràn ngang. Đã xem trực tiếp từng slide và phần đầu/cuối gallery, screenshot task/export/save/tổng kết. Chữ chú thích rõ; click ảnh mở kích thước gốc. Một số ảnh từng frame còn toast nhắc tiếp tục phiên cũ của CVAT, không che trường review.
- `.venv/bin/python -m pytest -o addopts= -q tests/test_t02_cvat_demo.py` trước khi thêm test tích hợp verifier: **22 passed in 0.59s**.
- `.venv/bin/python -m compileall -q tools/t02_cvat_demo.py tools/t02_artifacts.py tools/t02_verify.py tests/test_t02_cvat_demo.py`: **PASS**. `git diff --check`: **PASS**. Repo không cấu hình lint/typecheck hoặc build khác cho Python/HTML; generator là bước build artifact.
- Toàn bộ test trên working tree: `.venv/bin/python -m pytest -o addopts= -q`: **1 failed, 91 passed, 39 skipped in 6.07s**. Lỗi duy nhất: hash `reports/group_report.md` khác manifest do chỉnh sửa định dạng có sẵn. Không sửa report hay đổi hash của nó để che lỗi.
- `.venv/bin/python -m tools.t02_verify` trên working tree: exit 1, chỉ báo `evidence hash mismatch: reports/group_report.md`.
- Snapshot tạo bằng `git checkout-index --all --prefix=...` tại `/tmp/t004-cvat-final-fqAkIo`, gồm đúng các tệp đã stage và bản report đã commit, không kèm chỉnh sửa report/.obsidian ngoài nhiệm vụ. Dùng interpreter `.venv/bin/python` tuyệt đối của dự án, chạy từ snapshot:
  - `-m pytest -o addopts= -q`: **92 passed, 39 skipped in 6.69s**. 39 test bỏ qua vì thiếu GT/overlay giảng viên theo điều kiện có sẵn.
  - `-m tools.t02_verify`: **PASS**, protocol/metric/score/report/liên kết/contribution/hash và 20 frame CVAT đều hợp lệ.
  - `-m tools.t02_cvat_demo`: **PASS**, 20/20 frame, 19 RECAPTURE / 1 KEEP, đúng tên.
- `make preflight`: **0 FAIL, 2 WARN** (data/real và models_optional không có, cả hai tùy chọn). `make verify`: **14 manifests, 0 failing**.
- Kiểm liên kết Markdown/HTML cục bộ và screenshot assets: **PASS**. Kiểm staged: **45 tệp** thuộc nhiệm vụ, không có report/.obsidian/output tạm; hash mọi tệp `reports/` cũ giữ nguyên. Snapshot API không có trường tài khoản/phiên đăng nhập. Sau lần chạy snapshot chỉ cập nhật kết quả xác minh trong nhật ký này.

Các kết quả 69 passed / 39 skipped của snapshot tài liệu ở đầu phiên là lịch sử, đã được thay bằng kiểm tra triển khai hiện tại nêu trên. Lỗi kết nối ban đầu đã xử lý xong, không còn trạng thái chờ đăng nhập.

## Hạn chế và bước tiếp

Demo CVAT đã đủ 20 frame, lưu và export xong. Xác nhận review người thật, điểm GT giảng viên, thời điểm lớp và nộp remote vẫn chưa được xác minh. Người học có thể mở gallery/job, tự kiểm lại rồi thực hiện hướng dẫn hoàn tất nếu muốn chuyển trạng thái review của pipeline. Không tự suy ra GO từ trạng thái completed của CVAT.
