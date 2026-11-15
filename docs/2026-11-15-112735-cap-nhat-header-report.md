# Commit và push phần sửa header report

## Mục tiêu

Commit và push thay đổi học viên vừa thực hiện trong `reports/group_report.md`; bảo toàn nội dung được yêu cầu, cập nhật generator/checksum liên quan và xác minh trước khi đẩy `main`.

## Ban đầu

- HEAD `4fe0749`, nhánh `main`; chỉ report thay đổi, chưa có tệp stage hay untracked.
- Thay đổi của học viên: căn lại bảng Header, rút gọn Git URL, để trống ô tag demo, điền `4fe0749242ebdca5e8435ae2a1bc0b36ac057250` vào ô final và đổi deadline thành `11:40 15/11/2026`.
- Remote main khớp HEAD. Hai tag Git vẫn trỏ commit cũ: demo `1d2d4a6`, final `83ca5cc`. Việc sửa ô trong report không tự di chuyển tag Git.
- Học viên đã chọn: **“Điền đúng hai hash tag hiện có; giữ deadline 11:40”**. Bản report gốc được lưu tạm trong `out/report-edit-20261115-112735/` (gitignored) để đối chiếu.

## Thực hiện và xác minh

- Điền demo `1d2d4a6bd0587ed2b2531c42572cda72a43d1e5b`, final `83ca5ccc9868bfee89a8f285c3564784c174056b` từ Git. Giữ deadline **11:40 15/11/2026**, Git URL rút gọn, phần căn bảng và toàn bộ thân bài của học viên.
- Đồng bộ bốn giá trị Header trong `tools/t02_fill_report.py`; cập nhật deadline trong `docs/HUONG_DAN_HOAN_TAT_T004.md` để hướng dẫn và report nhất quán.
- Test so report với generator chỉ bỏ qua khoảng đệm ô bảng và độ dài hàng gạch phân cách Markdown; vẫn đối chiếu mọi giá trị, hàng, cột và phần văn bản. Có kiểm tra âm: sửa deadline hoặc metric phải làm so sánh thất bại. Không bỏ kiểm tra nội dung hay checksum.
- Manifest chỉ cập nhật hash `reports/group_report.md` sau khi đối chiếu diff; số liệu, bằng chứng và ảnh giữ nguyên.
- Kiểm thử ban đầu: `2 failed, 7 passed in 8.36s` do report không khớp generator và checksum cũ. Sau đồng bộ: `.venv/bin/python -m pytest -o addopts= -q tests/test_t02_report.py` đạt **9 passed in 6.78s**.
- `make preflight verify`: **0 FAIL / 2 WARN** (data/model tùy chọn); **14 manifests, 0 failing**.
- `.venv/bin/python -m tools.t02_human_review`: pass, Vũ Duy Khanh xác nhận đủ 20 frame; REWORK / QUALITY_RECAPTURE_REQUIRED.
- `.venv/bin/python -m compileall -q src tools tests`: pass sau sửa. Không có cấu hình lint/typecheck/build riêng; thay đổi không ảnh hưởng JavaScript.
- `.venv/bin/python -m tools.t02_verify --write-manifest`: pass protocol, metrics, template, link, review, demo và checksum.
- `.venv/bin/python -m pytest -o addopts= -q`: **149 passed, 39 skipped in 47.99s**. Các test skip cần GT giảng viên. Logs nằm trong `out/report-edit-20261115-112735/`.
- Đối chiếu bản học viên đã sửa: chỉ hai ô tag thay đổi theo xác nhận; toàn bộ thân bài giữ nguyên. Kiểm 56 liên kết local: pass. `git diff --check` với hỗ trợ CRLF: pass.
- Đã fetch `origin/main` và kiểm ancestor: nhánh có thể push fast-forward. Bước bàn giao là commit các tệp đã kiểm tra, push `main`, rồi đối chiếu HEAD local với remote và working tree.

## Tệp thay đổi

`reports/group_report.md`, `tools/t02_fill_report.py`, `tests/test_t02_report.py`, `reports/evidence_manifest.json`, `docs/HUONG_DAN_HOAN_TAT_T004.md`, nhật ký này và `docs/README.md`.

## Phạm vi

Không thay algorithm, nhãn, metrics, protocol, review đã xác nhận hoặc ảnh demo. Chỉ push nhánh `main`; không di chuyển hay force-push các tag lịch sử.
