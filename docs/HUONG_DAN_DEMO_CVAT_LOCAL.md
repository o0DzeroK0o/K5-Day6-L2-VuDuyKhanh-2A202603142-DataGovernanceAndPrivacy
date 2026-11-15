# Demo T004 / T02 trên CVAT local

## Kết quả thực tế

Ngày 2026-11-15, **đã xem, gán tag và lưu đủ 20/20 frame**, từ frame 0 đến 19, trên CVAT local **2.82.1** tại `http://localhost:8080`.

- Task **#17**, job **#17**, trạng thái **completed**.
- **19 RECAPTURE / 1 KEEP**. Frame 18, rank 19, `img_23_1` là KEEP.
- Hai thay đổi so với gợi ý KEEP của queue: `img_19_2` và `img_06_3` thành RECAPTURE.
- Cả 20 tag có `review_source = Vũ Duy Khanh`; `review_note` chỉ ghi nhận xét chất lượng ảnh. Default của cả hai label cũng dùng đúng tên đã xác nhận.
- Đã tải export **CVAT for images 1.1**, kiểm 20 ảnh/20 tag, tên ảnh và toàn bộ thuộc tính khớp dữ liệu API sau Save. Job đã được Finish khi đủ 20 frame.

[Mở 5 slides offline](../demo/t004_demo.html) · [Xem đủ 20 ảnh chụp](../demo/cvat/index.html) · [XML export](../demo/cvat/annotations.xml) · [Metadata kiểm chứng](../demo/cvat/evidence.json) · [Mở job local](http://localhost:8080/tasks/17/jobs/17).

## Nguồn và ý nghĩa của thuộc tính

**Vũ Duy Khanh xác nhận đã trực tiếp xem đủ 20 frame**, đồng ý 19 RECAPTURE / 1 KEEP và hai override. [Bản xác nhận hiện tại](../reports/human_review_confirmation.json) ghi nguyên văn câu hỏi/câu trả lời, thời điểm và checksum.

Pipeline sau xác nhận: **REWORK / QUALITY_RECAPTURE_REQUIRED**, `n_reviewed=20`, `n_human_reviewed=20`, `human_review_confirmed=true`. [Bằng chứng hiện tại](../reports/evidence/human_review/). `review_source` và `reviewer` hiện hành là Vũ Duy Khanh; ghi chú giữ nguyên nhận xét chất lượng.

`evidence.json`, [biên nhận nhập CVAT](../reports/cvat_review_import.json) và `reports/evidence/poc/` mô tả lần nhập trước khi có xác nhận mới. Chúng được giữ làm lịch sử, có liên kết checksum từ bản xác nhận mới. Nhãn chấm điểm, score, ranking, threshold và metric giữ nguyên.

## Bằng chứng đã lưu

| Tệp trong `demo/cvat/` | Nội dung thực tế |
|---|---|
| [01-task.jpg](../demo/cvat/01-task.jpg) | Task/job #17, hai label, 20 frame, range 0–19, completed. |
| [02-review.jpg](../demo/cvat/02-review.jpg) | Frame 0: ảnh mờ, RECAPTURE, đúng tên và nhận xét. |
| [03-save-verify.jpg](../demo/cvat/03-save-verify.jpg) | Mở lại frame 17 sau Save: `img_19_2`, RECAPTURE, ghi chú override. |
| [04-export.jpg](../demo/cvat/04-export.jpg) | Hộp thoại Export job dataset, CVAT for images 1.1, Save images tắt. |
| [04-export-dialog.jpg](../demo/cvat/04-export-dialog.jpg) | Chụp riêng chính hộp thoại export để chữ đọc được trên slide. |
| [05-export-finished.jpg](../demo/cvat/05-export-finished.jpg) | Requests của job #17: Finished, 100%, ngày 15/11. Cắt vùng trên để bỏ các request không liên quan. |
| [06-summary.jpg](../demo/cvat/06-summary.jpg) | Hộp thoại Info: 1 KEEP, 19 RECAPTURE, tổng 20 tag. |
| [frames/ và gallery](../demo/cvat/index.html) | 20 ảnh chụp thật, một ảnh cho mỗi frame, kèm quyết định và ghi chú. |
| [annotations.xml](../demo/cvat/annotations.xml) | Export cuối của đủ 20 frame, chỉ loại metadata tài khoản owner/assignee. Giữ nguyên ảnh, tag và thuộc tính. |
| [frame_mapping.csv](../demo/cvat/frame_mapping.csv) | Rank, tên CVAT, image_id, score, gợi ý ban đầu và SHA-256 ảnh gốc. |
| [server_snapshot.json](../demo/cvat/server_snapshot.json) | Snapshot API đã chọn trường: phiên bản, task/job, thứ tự ảnh, label và annotation đã lưu. Không chứa phiên đăng nhập. |
| [evidence.json](../demo/cvat/evidence.json) | Thời điểm chụp, số frame, kết quả, provenance và checksum export/XML/queue. |

Ảnh không được dựng lại bằng đồ họa hay công cụ sinh ảnh. Một số screenshot từng frame còn thông báo nhắc tiếp tục phiên làm việc của CVAT, không che thuộc tính review. Tên ảnh trong gallery dùng rank 01–20; số frame của CVAT bắt đầu từ 0.

## Dữ liệu và thao tác đã thực hiện

1. Lấy đúng 20 ảnh synthetic từ `reports/evidence/poc/review_queue.csv`, kiểm checksum nguồn và đóng ZIP không kèm nhãn. Tên có tiền tố `01_` đến `20_`, nhập theo thứ tự lexicographical vào task riêng #17.
2. Tạo hai label cấp ảnh `KEEP` và `RECAPTURE`, hai thuộc tính text `review_source`, `review_note`. T02 là QC cấp ảnh nên dùng tag.
3. Xem đủ 20 ảnh, chọn tag, điền nhận xét, Save từng frame; mở lại và so dữ liệu API. Chụp riêng toàn bộ 20 frame. Chỉ Finish the job sau khi xác nhận đủ 20 tag.
4. Menu → Export job dataset → CVAT for images 1.1, Save images tắt, tên `t004_cvat_local_final`. Đợi Requests báo Finished và Download ZIP.
5. Đối chiếu XML tải về với API, queue đã freeze và SHA-256 ảnh gốc. Bộ demo giữ XML đã loại metadata tài khoản; ZIP gốc nằm ở `out/cvat-demo/t004_cvat_local_final.zip`, không commit.

`out/cvat-demo/t004_top20_images.zip` là gói nhập gốc, SHA-256 `0294bee490ecb7f475ada8247ba4f7e3681bb53da9a985d945473203ff7bb918`. Queue score làm tròn 6 chữ số theo contract; mapping lưu thêm raw score. Gợi ý PoC không được coi là ground truth. Không đọc GT giảng viên.

## Đồng bộ vào pipeline sau review

Dùng `make t02-submission OUT=out/cvat-reproduction` để tái lập vào thư mục riêng. Công cụ lấy đủ 20 quyết định đã được Vũ Duy Khanh xác nhận. Bước nhập cũ được giữ để kiểm lịch sử và không được ghi đè lần ký duyệt mới.

```bash
.venv/bin/python -m tools.t02_cvat_review
.venv/bin/python -m tools.t02_human_review
make t02-submission OUT=out/cvat-reproduction
```

CSV, ghi chú, hành động cuối và audit phải khớp bản xác nhận; raw predictions không thay đổi. Hai override chỉ sửa hành động cuối. Audit mới nối sau toàn bộ lịch sử cũ.

## Tái kiểm tra offline

Từ gốc repository:

```bash
.venv/bin/python -m tools.t02_cvat_demo
.venv/bin/python -m tools.t02_artifacts
xdg-open demo/t004_demo.html
xdg-open demo/cvat/index.html
```

Verifier từ chối thiếu/trùng frame, tag thừa, sai mapping/ảnh gốc, sai tên hoặc ghi chú, screenshot thiếu/hỏng, XML lệch snapshot API và summary không nhất quán. Slides đọc số liệu từ `reports/analysis_summary.json`, thông tin CVAT từ package đã kiểm chứng.

Đóng gói lại từ ZIP và snapshot API của cùng một lần export:

```bash
.venv/bin/python -m tools.t02_cvat_demo \
  --export out/cvat-demo/t004_cvat_local_final.zip \
  --server out/cvat-demo/server-evidence.json \
  --mapping out/cvat-demo/frame_mapping.csv
```

Cần giữ đủ screenshot trước khi đóng gói. Snapshot chỉ gồm các trường cần kiểm chứng, tuyệt đối không ghi cookie/token. Nếu review lại trên CVAT thì cần lấy export, snapshot và ảnh mới cùng trạng thái. Công cụ này không gọi mạng hoặc thay đổi nhãn trên server.

## Tài liệu CVAT đã đối chiếu

Các trang đã đối chiếu trong nhiệm vụ ngày 2026-11-15; tên điều khiển còn được kiểm trực tiếp trên CVAT local 2.82.1:

- [Task và tạo task](https://docs.cvat.ai/docs/workspace/tasks-page/).
- [Tag cấp ảnh](https://docs.cvat.ai/docs/manual/advanced/annotation-with-tags/).
- [Định dạng CVAT for images](https://docs.cvat.ai/docs/dataset_management/formats/format-cvat/).
- [Export annotation/dataset](https://docs.cvat.ai/docs/dataset_management/export-datasets/).
