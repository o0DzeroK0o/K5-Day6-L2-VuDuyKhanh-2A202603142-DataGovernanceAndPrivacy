# T004 / T02 — kiểm tra bài nộp

Vũ Duy Khanh đã xác nhận trực tiếp xem đủ 20 frame và đồng ý 19 RECAPTURE, 1 KEEP (`img_23_1`), gồm hai override `img_19_2`, `img_06_3`. [Bản xác nhận](../reports/human_review_confirmation.json) lưu câu hỏi, câu trả lời, thời điểm và checksum. Batch hiện tại **REWORK / QUALITY_RECAPTURE_REQUIRED**.

## Checklist theo hướng dẫn

**Đã đạt 7/8 mục kỹ thuật và tài liệu.** Bản hiện hành dùng nhánh `main`; hai tag giữ mốc cũ. Mốc tag theo giờ lớp và việc gửi link qua cổng nộp chưa được xác nhận. [Nhật ký repo sạch và push GitHub](2026-11-15-111835-lam-sach-repo-va-push-github.md) ghi trạng thái đồng bộ; [kiểm tra report](2026-11-15-111055-kiem-tra-repo-va-report.md) ghi kết quả đối chiếu nội dung.

- [x] Đã chọn T02, đọc đề và lập metric contract.
- [x] `configs/lab.yaml`: T004, owner Vũ Duy Khanh, seed 42, xác nhận review hiện tại.
- [x] Setup, test, preflight và manifests: kết quả trong [verification.json](../reports/verification.json).
- [x] Pipeline đủ load → process → rank → review → decide; output đúng contract.
- [x] Có baseline/PoC metrics, ≥1 failure case, reviewer evidence, decision log. Các chỉ số tự kiểm chưa phải điểm chính thức.
- [x] Có review trực tiếp 20/20 frame, người review Vũ Duy Khanh; audit mới có `human_confirmed: true`.
- [x] Có report đúng cấu trúc và bảng đóng góp một thành viên; Git author khớp lịch sử.
- [ ] Tag demo/final đúng mốc lớp và nộp remote: `demo-180m` → `1d2d4a6`, `final-24h` → `83ca5cc`; cả hai thiếu CVAT, review đã xác nhận và web hiện tại. Bản hiện hành dùng nhánh `main`; đúng giờ lớp và việc gửi link qua cổng nộp chưa được xác nhận.

Hạn do học viên điền: **11:00 15/11/2026**, giờ Việt Nam. Nhóm thực tế một người; các hàng thành viên còn lại giữ theo template và ghi không áp dụng.

## Bằng chứng hiện hành

| Nội dung | Đường dẫn |
|---|---|
| Review hiện tại | [review_queue.csv](../reports/review_queue.csv) |
| Xác nhận của học viên | [human_review_confirmation.json](../reports/human_review_confirmation.json) |
| Pipeline sau xác nhận | [evidence/human_review/](../reports/evidence/human_review/) |
| Lịch sử nhập CVAT trước xác nhận | [cvat_review_import.json](../reports/cvat_review_import.json), [evidence/poc/](../reports/evidence/poc/) |
| Ứng dụng web | `make web` → http://127.0.0.1:8765; [ảnh đủ năm bước](../demo/web/index.html), [kiểm thử trình duyệt](../demo/web/verification.json) |
| Demo mới và ảnh chụp | [5 slides](../demo/t004_demo.html), [ảnh slide](../demo/slides/), [ảnh web](../demo/web/index.html), [20 frame CVAT](../demo/cvat/index.html) |

Các sự kiện cũ giữ thời điểm và nguồn gốc của chúng. Biên nhận nhập trước đó có HOLD; lần ký duyệt mới có REWORK. Dùng `evidence/human_review/decision.json` để đọc trạng thái hiện tại.

## Mở và tái lập

```bash
make web
# Terminal khác: xdg-open http://127.0.0.1:8765
# Slides riêng: make demo && xdg-open demo/t004_demo.html
make t02-submission OUT=out/check-final
.venv/bin/python -m tools.t02_human_review
.venv/bin/python -m tools.t02_verify
```

Chạy lại cùng thư mục sẽ giữ file review đã có. Dùng thư mục mới để kiểm tra tái lập từ đầu. Không cần xác nhận lại hoặc ghi một lần ký duyệt giả; công cụ dùng bản xác nhận đã lưu.

Nếu đổi quyết định sau này, dùng Review trên web để lưu phiên bản mới và chạy Decide. Mỗi lần lưu giữ audit và phiên bản trước. Lượt chạy web không tự cập nhật bằng chứng bài nộp đã ký duyệt. [Hướng dẫn thao tác](HUONG_DAN_CHAY_DEMO_T004.md).

## Phần còn lại trước khi nộp

1. Chốt phiên bản cần nộp và cách xử lý tag theo yêu cầu lớp: tag cục bộ hiện tại là mốc lịch sử, chưa bao gồm thay đổi mới. Không tự di chuyển tag hay sửa lịch sử.
2. Gửi link nhánh `main` và phiên bản được lớp chấp nhận qua cổng nộp. Push lên GitHub và gửi bài qua cổng lớp là hai bước riêng; [nhật ký đồng bộ GitHub](2026-11-15-111835-lam-sach-repo-va-push-github.md) ghi kết quả push.
3. Trình bày theo [kịch bản showcase](../demo/SHOWCASE_SCRIPT.md); chưa khai báo buổi trình bày/debate đã diễn ra.

Không có GT giảng viên trong repo. Nhãn eval nội bộ chưa được kiểm định độc lập toàn bộ. OOD gồm 10 ảnh synthetic T13, 0 positive, không đo recall OOD và không thay dữ liệu thực.
