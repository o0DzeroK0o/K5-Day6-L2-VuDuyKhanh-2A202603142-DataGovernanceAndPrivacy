# Làm sạch repo và push GitHub

## Mục tiêu và phạm vi

Người dùng yêu cầu đạt mốc repo sạch, sau đó push lên GitHub. Phạm vi gồm nhánh `main` và hai tag đang có; không di chuyển tag hoặc sửa lịch sử. Bản mới nhất dùng nhánh `main`; mốc giờ lớp và việc gửi link qua cổng nộp là các việc riêng chưa được xác nhận.

## Ban đầu và quyết định

- HEAD `9490610`; Git chỉ báo `.obsidian/` chưa theo dõi. Remote `main` ở `b0ce8bf`, chưa có tag.
- Bốn tệp `.obsidian/` là cấu hình cá nhân. Thêm mẫu ignore tương ứng vào nhóm OS/IDE; giữ nguyên nội dung trên máy, đối chiếu SHA-256 trước/sau, không đưa chúng vào GitHub.
- Cấu hình Git, danh tính commit và quy trình dự án đã có đủ; không khởi tạo lại.
- Người dùng đã yêu cầu push trực tiếp trong phiên này. Push bình thường, chỉ fast-forward `main` và thêm hai tag lịch sử chưa có trên remote.
- Đồng bộ lời dẫn README/report/hướng dẫn để dùng nhánh `main` cho bản hiện hành; giữ các kết luận kiểm tra ngày trước như dữ liệu lịch sử. Không đánh dấu hoàn tất mốc tag theo giờ lớp chỉ vì đã push.

## Thay đổi

- `.gitignore`: bỏ qua `.obsidian/` cùng các cấu hình IDE khác.
- `README.md`, `HUONG_DAN_HOC_VIEN.html`, `docs/HUONG_DAN_HOAN_TAT_T004.md`: làm rõ nhánh hiện hành và trạng thái tag/cổng nộp.
- `tools/t02_fill_report.py`, `tests/test_t02_report.py`, `reports/group_report.md`: đồng bộ phần trả lời và kiểm thử, giữ cấu trúc mẫu.
- `reports/evidence_manifest.json`: chỉ cập nhật hash tài liệu đã sửa sau đối chiếu.
- Nhật ký này và mục lục `docs/README.md`.

## Kiểm tra và push

| Lệnh / thao tác | Kết quả thực tế |
|---|---|
| `git check-ignore -v .obsidian/app.json .obsidian/appearance.json .obsidian/core-plugins.json .obsidian/workspace.json` | Cả bốn tệp được ignore bởi `.gitignore`; không có tệp Obsidian được tracked. |
| Đối chiếu SHA-256 trước/sau của `.obsidian/` | Bốn tệp giữ nguyên nội dung. Chỉ thêm ignore, không xóa dữ liệu cá nhân. |
| `.venv/bin/python -m pytest -o addopts= -q` | **149 passed, 39 skipped in 54.02s**. Skip do thiếu GT giảng viên; test report cập nhật đã chạy trong full suite. |
| `make preflight verify` | **0 FAIL / 2 WARN** về dữ liệu/model tùy chọn; **14 manifests, 0 failing**. |
| `.venv/bin/python -m tools.t02_human_review` | Pass: Vũ Duy Khanh xác nhận 20/20, REWORK / QUALITY_RECAPTURE_REQUIRED. |
| `.venv/bin/python -m compileall -q src tools tests`; `node --check src/web_ui/app.js`; `node --check tools/test_web_ui.cjs` | Pass. Dự án không có cấu hình lint/typecheck/build riêng. |
| `.venv/bin/python -m tools.t02_verify --write-manifest` sau khi xem diff | Pass; manifest chỉ đổi hash `reports/group_report.md`. Toàn bộ metric, protocol, ảnh và review giữ nguyên. |
| Đối chiếu template/generator và liên kết bằng Python | Pass, 75 liên kết Markdown local hợp lệ ở các tài liệu liên quan. |
| Kiểm danh sách tracked và hash tag | Không có `.obsidian`, dependencies, output, dữ liệu thật, `.env` hoặc GT giảng viên trong tracked files. Hai tag giữ nguyên commit lịch sử. |
| `git fetch --no-tags origin main`; `git merge-base --is-ancestor origin/main main` | Pass; nhánh local có thể push fast-forward. |
| `git -c push.followTags=false push --dry-run origin refs/heads/main:refs/heads/main refs/tags/demo-180m:refs/tags/demo-180m refs/tags/final-24h:refs/tags/final-24h` | Pass quyền push; kế hoạch cập nhật main và thêm hai tag chưa có trên remote, không dùng force. Đây mới là dry-run. |
| `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check` | Pass; giữ CRLF của hướng dẫn HTML. |

Phần ignore là cấu hình, xác minh bằng Git và checksum; không tạo test giả. Logs kiểm tra nằm ở `out/github-20261115-111835/` (gitignored).

## Kết quả push và xác minh

- Commit nội dung `c64d7d6` — `chore: ignore local workspace and prepare GitHub publication`. Ngay sau commit, `git status --porcelain=v1 --untracked-files=all` trả chuỗi trống: không còn thay đổi tracked, staged hoặc untracked.
- `GIT_TERMINAL_PROMPT=0 git -c push.followTags=false push --atomic -u origin refs/heads/main:refs/heads/main refs/tags/demo-180m:refs/tags/demo-180m refs/tags/final-24h:refs/tags/final-24h` thành công: remote main cập nhật fast-forward từ `b0ce8bf` đến `c64d7d6`, hai tag được thêm. Nhánh `main` theo dõi `origin/main`.
- Kiểm trực tiếp bằng `git ls-remote --heads --tags origin`: main là `c64d7d67eff94a60e044ac924814cd095bdecfeb`; commit của tag demo là `1d2d4a6bd0587ed2b2531c42572cda72a43d1e5b`, tag final là `83ca5ccc9868bfee89a8f285c3564784c174056b`, đều khớp local.
- `git rev-list --left-right --count main...origin/main` trả `0 0`; `git status --short --branch` chỉ có `## main...origin/main`.
- Mốc **repo sạch và push GitHub đã đạt**. [Bản hiện hành trên main](https://github.com/o0DzeroK0o/K5-Day6-L2-VuDuyKhanh-2A202603142-DataGovernanceAndPrivacy/tree/main) có mã nguồn, report, demo web/CVAT và bằng chứng review đã xác nhận.

## Giới hạn

Không đổi thuật toán, metric, nhãn, protocol, review đã xác nhận hay demo. Hai tag giữ nguyên commit lịch sử; `main` chứa bản hiện hành. Chưa xác nhận deadline của lớp, chưa gửi link qua cổng nộp, chưa khai báo showcase/debate đã diễn ra.
