# Đối chiếu triển khai năm bước pipeline T02

## Mục tiêu và phạm vi

Trả lời việc `process + review + decide` đã được viết đúng luồng năm bước trong `HUONG_DAN_HOC_VIEN.html` hay chưa, dựa trên code, test và lần chạy mới.

HEAD đầu nhiệm vụ: `919d0f5`. Đã kiểm Git và AGENTS; workflow đã đủ. Các thay đổi sẵn tại `reports/group_report.md`, `reports/metric_contract.md`, `reports/team_contributions.csv` và `.obsidian/` nằm ngoài nhiệm vụ. Không sửa chúng, không thay thuật toán/ngưỡng/nhãn, không push hoặc đổi tag.

## Đối chiếu yêu cầu và code

[Hướng dẫn học viên, mục Năm bước pipeline](../HUONG_DAN_HOC_VIEN.html#pipeline) yêu cầu `load → process → rank → review → decide`. [Đề T02](tracks/T02.md) và [README](../README.md) mô tả input, output, review và lệnh chạy tương ứng.

Các bước đều có trong [src/pipeline.py](../src/pipeline.py); `run_pipeline()` tại dòng 198 gọi đúng thứ tự. `src.main` mặc định nạp module `src.pipeline` và gọi `run(ctx)`. Commit triển khai code pipeline là `6c525dc` (`feat: implement offline T02 triage and freeze dev protocol`).

| Bước | Vị trí | Hành vi đã triển khai |
|---|---|---|
| load | `src/pipeline.py:27` | Đọc metadata/manifest, kiểm SHA-256, ID/path trùng hoặc thiếu, đường dẫn ra ngoài thư mục và độ bao phủ manifest. |
| process | `src/pipeline.py:105`; feature/score tại dòng 56/73 | Đọc pixel ảnh, tính Laplacian sharpness, brightness, glare ROI và JPEG blockiness; dùng ngưỡng theo camera/ánh sáng để sinh score, loại lỗi và KEEP/RECAPTURE. |
| rank | `src/pipeline.py:124` | Lấy top B=20 từ pool eval theo score; ghi `review_queue.csv` và contact sheet có ảnh. |
| review | `src/pipeline.py:139` | Đọc `review_queue_reviewed.csv`, kiểm ID/score/suggestion và override, áp hành động review, ghi audit actor/before/after/reason; giữ nguyên score/type dùng đánh giá và tránh ghi lặp quyết định. |
| decide | `src/pipeline.py:183` | Policy HOLD khi có escalation, chưa đủ xác nhận người thật hoặc domain lạ; REWORK khi còn RECAPTURE; GO khi các điều kiện triage đã hoàn tất. Ghi reason_code, owner, evidence và thống kê. |

`run_pipeline()` ghi `raw_predictions.csv`, `ranked_review.csv`, `item_decisions.csv`, `decision.json`, `decision_log.csv`; audit được runner gắn vào context. Đây là triển khai hoạt động, không còn hàm stub cho T02.

## Xác minh thực tế

1. Chạy `.venv/bin/python -m pytest -o addopts= -q tests/test_t02_pipeline.py tests/test_t02_cvat_review.py`: **24 passed in 3.67s**. Bao phủ chạy offline lặp lại, xử lý pixel, điều kiện camera/light, manifest lỗi, override/audit bất biến score, review sai và các nhánh chờ xác nhận/escalation/rework; thêm kiểm đồng bộ đủ 20 quyết định CVAT.
2. Tạo output riêng `out/pipeline-five-steps-20261115-100709/`, dùng `tools.t02_cvat_review.export_review()` nhập các quyết định CVAT đã lưu vào CSV review của output này. Không đồng bộ ngược vào bằng chứng báo cáo.
3. Chạy:

   ```bash
   .venv/bin/python -m src.main --input fixtures/t02_raw_qc --config configs/lab.yaml --output out/pipeline-five-steps-20261115-100709 --run-name poc --offline --seed 42
   ```

   **Exit 0**, runtime **0.7452s**. Xử lý 96 ảnh, pool eval 40, queue 20; áp đủ 20 quyết định và hai override `img_19_2`, `img_06_3`; 19 RECAPTURE / 1 KEEP trong queue; có 20 sự kiện audit review.
4. `tools.t02_cvat_review.check_run()` đối chiếu output mới với bằng chứng CVAT: PASS. So `image_id/score/pred_defect_type` giữa raw/final: giữ nguyên. Output mới có `n_reviewed=20`, `n_human_reviewed=0`, `HOLD / HUMAN_REVIEW_REQUIRED`.
5. Kiểm liên kết nhật ký/mục lục và `git diff --check` cho hai tệp tài liệu trước commit. Nhiệm vụ không đổi source nên không thêm test; chỉ chạy bộ test trực tiếp liên quan và lần chạy thực tế, không tuyên bố kiểm toàn bộ working tree chứa các chỉnh sửa riêng đang làm.

## Tệp thay đổi

Chỉ nhật ký này và `docs/README.md`. Output kiểm tra ở `out/` được ignore, không đưa vào commit hoặc thay số liệu đã freeze.

## Kết luận / phần còn lại

Đã triển khai và nối đủ cả năm bước, bao gồm `process`, `review`, `decide`. Điều còn chờ là xác nhận review trực tiếp của người học, không phải thiếu code bước review/decide. Giữ `human_review_confirmed=false`, reviewer/operator thực tế và HOLD đúng với bằng chứng; không tự ký thay.

## Tiếp nối: cách chạy trên máy hiện tại

Theo câu hỏi tiếp theo của người dùng, đã đối chiếu `Makefile`, `run.sh` và hướng dẫn demo. Máy đã có `.venv/bin/python` và `xdg-open`. `make -n run` xác nhận lệnh gọi `src.main` cho T02, output `out/poc`, offline, seed 42. CSV review hiện có ở `out/poc/review_queue_reviewed.csv` khớp từng byte với 20 quyết định CVAT đã lưu trong `reports/evidence/poc/`.

Mở Terminal ở gốc repository và chạy:

```bash
make run
xdg-open out/poc/contact_sheet.html
```

`make run` tự chạy đủ năm bước; bước review đọc CSV đã có. Không cần activate `.venv` vì Makefile dùng `.venv/bin/python`. Contact sheet là giao diện HTML xem 20 ảnh và nhập review. Kết quả của lần chạy nằm trong `out/poc/`; xem quyết định bằng:

```bash
cat out/poc/decision.json
```

`status=0` trong Terminal là chương trình thành công; HOLD trong JSON là quyết định nghiệp vụ chờ xác nhận người học. Muốn mở slides đã lưu, chạy `xdg-open demo/t004_demo.html`; job CVAT thật ở `http://localhost:8080/tasks/17/jobs/17` khi server local đang chạy.

Phần tiếp nối chỉ bổ sung hướng dẫn, không chạy lại pipeline hoặc test đã kiểm ngay trước đó. Kiểm `make -n`, CSV đầu vào, đường dẫn HTML và `git diff --check`; giữ nguyên ba tệp reports đang được người dùng sửa và `.obsidian/`.
