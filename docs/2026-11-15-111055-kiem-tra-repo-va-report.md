# Kiểm tra repo sạch và report hoàn chỉnh

## Mục tiêu

Đối chiếu trạng thái Git, nội dung report, tag và bằng chứng với yêu cầu “Repo sạch + report hoàn chỉnh”; chạy lại kiểm chứng và sửa hướng dẫn tái lập nếu cần.

## Trạng thái đầu nhiệm vụ

- HEAD `bd0aa67` (`feat: add live five-step pipeline web workspace`); không có thay đổi tracked. Git báo bốn tệp cài đặt trong `.obsidian/` chưa theo dõi. Đây là dữ liệu cá nhân đã có trước nhiệm vụ, không xóa, stage hay thêm ignore trong lần kiểm tra này.
- Quy trình khởi tạo đã đủ Git, `.gitignore`, `AGENTS.md`, mục lục và nhật ký; không tạo commit khởi tạo trùng.
- Report đủ mục 00–11, không còn ô trống; có baseline/PoC, failure cases, review 20 frame, decision và đóng góp một thành viên. Các chỉ số dùng nhãn nội bộ, không phải điểm GT giảng viên.
- `demo-180m` trỏ `1d2d4a6bd0587ed2b2531c42572cda72a43d1e5b`; `final-24h` trỏ `83ca5ccc9868bfee89a8f285c3564784c174056b`. Sau tag final có 11 commit. Cả hai tag thiếu CVAT, xác nhận review mới và ứng dụng web hiện tại.
- Kiểm remote bằng `GIT_TERMINAL_PROMPT=0 timeout 25 git ls-remote --heads --tags origin`: chỉ có `main` tại `b0ce8bfd972315448aace86185c1a3e075754b93`, không có hai tag. Chưa push hay nộp bài.

## Phát hiện và quyết định

- Lệnh evaluate trong mục 08 đang ghi đè `reports/metrics_poc.json`; lệnh run chưa kích hoạt `.venv`, chưa giải thích kết quả HOLD khi chưa nạp review. Sửa phần trả lời qua generator, dùng output riêng và nêu rõ cách tái lập bản đã xác nhận.
- Điền hash tag thực và ghi rõ tag lịch sử; bỏ dấu đạt ở checklist “tag cuối cùng” vì tag chưa bao gồm bản hiện tại. Giữ nguyên câu hỏi, đề mục, cấu trúc và bảng mẫu.
- Làm rõ `6c525dc` là commit của snapshot đo runtime, không phải HEAD hiện tại. Không thay số liệu hoặc tạo một lần xác nhận con người mới.
- `reports/README.md` vẫn mô tả CSV hiện hành theo lần nhập trước xác nhận. Đã sửa đường dẫn hiện tại sang `evidence/human_review/`, ghi rõ xác nhận trực tiếp của Vũ Duy Khanh và REWORK; giữ bản nhập HOLD làm lịch sử.
- Giữ nguyên pipeline/baseline, scoring params, protocol, nhãn, metrics, bằng chứng CVAT và biên nhận review. Không di chuyển tag hay push.

## Kết quả xác minh

| Lệnh / thao tác | Kết quả thực tế |
|---|---|
| `.venv/bin/python -m pytest -o addopts= -q` | **149 passed, 39 skipped in 56.28s**. Skip vì thiếu GT giảng viên; không tắt hay hạ tiêu chuẩn test. |
| `.venv/bin/python -m pytest -o addopts= -q tests/test_t02_report.py` sau khi cập nhật report và manifest | **9 passed in 6.85s**. Report đúng template, khớp generator; bằng chứng và các kiểm tra chống sửa sai đều đạt. |
| Test mới chạy nguyên lệnh run/evaluate trong mục 08 ở thư mục tạm | Pass: kích hoạt đúng venv, không mạng, metric khớp; output mới chưa nạp review là HOLD / HUMAN_REVIEW_REQUIRED. File metrics bài nộp được giữ nguyên. |
| `make t02-submission OUT=out/audit-20261115-111055` | Exit 0; tái lập baseline, PoC, hai ablation và OOD ở thư mục mới. |
| Đối chiếu output tái lập với snapshot bằng Python/JSON/Pandas | Cả bốn `raw_predictions.csv` trùng byte; tất cả mảng metrics và analysis/bootstrap khớp. CSV 20 review khớp bản đã xác nhận; ranked predictions khớp bản ký duyệt. Decision **REWORK / QUALITY_RECAPTURE_REQUIRED**, `n_human_reviewed=20`. |
| `.venv/bin/python -m tools.t02_human_review` | Pass trước và sau sửa: Vũ Duy Khanh xác nhận 20/20; REWORK / QUALITY_RECAPTURE_REQUIRED. |
| `make preflight verify` | **0 FAIL / 2 WARN** về dữ liệu và model tùy chọn; **14 manifests, 0 failing**. |
| `.venv/bin/python -m compileall -q src tools tests`; `node --check src/web_ui/app.js`; `node --check tools/test_web_ui.cjs` | Pass. Không có cấu hình linter/typecheck/build riêng trong dự án; không thêm test giả cho phần văn bản. |
| `make -n setup` | Dùng Python 3.12 và requirements-lock.txt đúng môi trường đã kiểm tra. |
| `.venv/bin/python -m tools.t02_verify` trước sửa; `--write-manifest` sau khi đối chiếu diff | Pass protocol, evaluator metrics, score bất biến, template, liên kết, CVAT 20 frame, demo web và checksum. Manifest chỉ đổi ba mục: README của reports, group_report và verification. |
| Kiểm cấu trúc report, placeholder và liên kết local bằng Python | Đủ 12 mục 00–11, không còn ô trống/TODO/TBD. **85 liên kết Markdown local** hợp lệ ở các tài liệu chính, gồm README của reports và nhật ký này. |
| `git show` các SHA trong team_contributions.csv; `git shortlog -sne --all` | Bốn commit đóng góp được nêu tồn tại, tác giả khớp Duy Khanh. Các tác giả starter không bị khai thành thành viên nhóm. |
| So Git diff với bản đầu nhiệm vụ | Không đổi pipeline, baseline, cấu hình, nhãn, metrics, protocol, bằng chứng review hoặc demo. Không chụp lại ảnh; verifier đối chiếu bằng chứng trình duyệt đã lưu. |
| `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check` | Pass; giữ nguyên CRLF của hướng dẫn HTML. |

Log lệnh và output tái lập nằm ở `out/audit-20261115-111055/` (gitignored). Kết quả mới được ghi vào [verification.json](../reports/verification.json); kết quả phiên web trước đó vẫn lưu ở trường lịch sử. Nội dung test mới kiểm hành vi chạy lệnh thật và bảo toàn metrics, cùng việc report không lệch generator.

## Tệp thay đổi

- `tools/t02_fill_report.py`, `tests/test_t02_report.py`: sửa phần trả lời và thêm kiểm thử tái lập/đồng bộ.
- `reports/group_report.md`, `reports/README.md`, `reports/verification.json`, `reports/evidence_manifest.json`: hướng dẫn đúng trạng thái, hash tag, kết quả kiểm tra và checksum tương ứng.
- `README.md`, `HUONG_DAN_HOC_VIEN.html`, `docs/HUONG_DAN_HOAN_TAT_T004.md`: ghi rõ tag cũ chưa chứa bài hiện tại. Câu chữ checklist trong report và hướng dẫn học viên được giữ nguyên.
- Nhật ký này và `docs/README.md`: ghi kết quả, mục lục và phần còn lại.

## Kết luận kiểm tra

Nội dung report và bằng chứng kỹ thuật đã đầy đủ, tái lập được. Checklist report hiện **4/5**; checklist hướng dẫn học viên **7/8**. Mục tag cuối cùng còn chờ vì bản gắn tag không chứa bằng chứng mới. Không đánh dấu đã nộp chỉ vì report không còn ô trống.

## Hạn chế và phần còn lại

Repo chưa sạch hoàn toàn do bốn tệp `.obsidian/` chưa được theo dõi; cần quyết định cách quản lý cấu hình cá nhân này trước khi yêu cầu `git status` hoàn toàn trống. Mốc tag chưa bao gồm thay đổi hiện hành; cần chốt phiên bản nộp/tag theo yêu cầu lớp, push và gửi link nộp. Đúng giờ lớp và showcase/debate chưa được xác nhận. Không có GT giảng viên để kết luận điểm chính thức. Nhiệm vụ kiểm tra và sửa tài liệu đã hoàn tất; không thực hiện các bước nộp bài ngoài phạm vi yêu cầu.
