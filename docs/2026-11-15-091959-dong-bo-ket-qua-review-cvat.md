# Đồng bộ kết quả sau review CVAT

## Mục tiêu

Theo yêu cầu tiếp theo sau demo, đưa kết quả 20 frame CVAT vào CSV review/pipeline, audit và báo cáo; sửa tên hiện hành thành Vũ Duy Khanh, cập nhật trạng thái/tài liệu và kiểm thử toàn bộ.

## Hiện trạng và quyết định

- HEAD đầu nhiệm vụ: `28092af`. Git/workflow đã đủ. Có hai dòng định dạng References do người dùng sửa trong `reports/group_report.md` và `.obsidian/` chưa track. Báo cáo nay thuộc phạm vi cần cập nhật sau review: giữ định dạng bảng của người dùng, kiểm cấu trúc template rồi cập nhật manifest cho báo cáo hiện tại. `.obsidian/` vẫn ngoài phạm vi.
- Đọc lại AGENTS, hướng dẫn hoàn tất, report, importer/demo, review contract, pipeline và tests. API CVAT local xác nhận job completed, 20 tag; annotations và thứ tự frame không đổi so với snapshot/export đã lưu. Không cần thay ảnh hoặc xuất lại XML.
- Chuyển tag KEEP/RECAPTURE thành approve/edit theo gợi ý queue. Giữ nguyên image_id/rank/score và ghi chú CVAT. `review_source` vẫn Vũ Duy Khanh; reviewer pipeline dùng `AI:Codex` theo operator thật. Không thêm AI vào review_note. Xác nhận người học còn chờ nên giữ `human_review_confirmed: false`.
- Sửa owner hiện hành trong `configs/lab.yaml`; giữ nguyên toàn bộ tham số/protocol đã freeze. Các tên cũ trong protocol và audit lịch sử được giữ nguyên, tên hiện hành được sửa ở cấu hình/report/contributions/hướng dẫn.
- Review cũ được sao lưu trong `out/poc/review_history/`. Chạy pipeline offline với 20 quyết định CVAT rồi đồng bộ bằng chứng. Audit/decision log giữ nguyên prefix cũ và thêm sự kiện mới. Kết quả 19 RECAPTURE / 1 KEEP, hai override img_19_2 và img_06_3. HOLD / HUMAN_REVIEW_REQUIRED, n_reviewed=20, n_human_reviewed=0.
- Thêm biên nhận nhập liên kết checksum XML/queue/CSV/raw predictions, metadata nguồn, overrides và quyết định. Verifier kiểm CSV/hành động/audit thật, không chỉ cờ imported. Công cụ tái lập dùng review CVAT khi chưa có CSV review đích.
- Báo cáo giữ câu hỏi, đề mục, số dòng/cột và checklist thực tế; cập nhật phần data flow, Human & decision, tên, bằng chứng CVAT và kết quả test. Demo/hướng dẫn đổi trạng thái chưa nhập thành đã nhập. Không thay nhãn evaluator/score/metric để tăng điểm.

## Tệp thay đổi

- `tools/t02_cvat_review.py`, `tools/t02_cvat_demo.py`, `tools/t02_verify.py`, `tools/t02_submission.py`: chuyển đổi/sync/kiểm review CVAT và tái lập.
- `configs/lab.yaml`, `tools/t02_fill_report.py`, `reports/group_report.md`, `reports/team_contributions.csv`: tên đã xác nhận và báo cáo sau review.
- `reports/cvat_review_import.json`, CSV review, audit/decision log, decision và run_info PoC: bằng chứng pipeline sau import.
- `tools/t02_artifacts.py`, slides HTML, `demo/cvat/evidence.json`, showcase, README, hướng dẫn và mục lục docs: trạng thái import và quy trình tiếp theo.
- Tests import CVAT, test demo/report và `reports/verification.json`, evidence manifest: kiểm tính nhất quán và kết quả mới.

## Xác minh

- API live: state completed, 20 tag, annotations/order bằng snapshot đã commit.
- `python -m tools.t02_cvat_review --output out/poc/review_queue_reviewed.csv`: export đủ 20 dòng.
- `python -m src.main --input fixtures/t02_raw_qc --config configs/lab.yaml --output out/poc --run-name poc --offline --seed 42`: status 0, runtime 0.7575s.
- `python -m tools.t02_cvat_review --sync-output out/poc` và `python -m tools.t02_cvat_review`: PASS, 20/20, HOLD / HUMAN_REVIEW_REQUIRED. So raw predictions với bản freeze và kiểm toàn bộ ghi chú/audit.
- `.venv/bin/python -m pytest -o addopts= -q`: **103 passed, 39 skipped in 7.12s**. Các skip cần GT/overlay giảng viên. Có test cho đủ 20 ghi chú/hành động, backup review AI, từ chối ghi đè review người thật, score bất biến, audit thiếu/sai, lịch sử bị cắt và xác nhận người thật sai.
- `make preflight`: **0 FAIL, 2 WARN** do thiếu dữ liệu thật và pretrained model tùy chọn. `make verify`: **14 manifests, 0 failing**.
- `.venv/bin/python -m compileall -q tools/t02_cvat_review.py tools/t02_cvat_demo.py tools/t02_verify.py tools/t02_submission.py tools/t02_fill_report.py tools/t02_artifacts.py tests/test_t02_cvat_review.py tests/test_t02_cvat_demo.py` và `git diff --check`: PASS.
- `.venv/bin/python -m tools.t02_submission --output out/post-cvat/reproduce --reports out/post-cvat/reproduce/reports`: **exit 0**, tái lập vào output mới. So bốn raw rankings, toàn bộ mảng metric evaluator và analysis/bootstrap summary: trùng bằng chứng đã lưu. CSV PoC trùng đủ 20 quyết định CVAT, audit hợp lệ, HOLD; runtime/timestamp khác theo lần chạy.
- Kiểm giao diện bằng Playwright/Chromium đã được cho phép: trang 5 sau import hiển thị đúng, ảnh kiểm ở `/tmp/t004-post-cvat-slide5.png`; năm section đều cao 1000px, không tràn ngang. Trang 1 và preview không đổi; giữ ảnh CVAT đã chụp.
- Kiểm câu hỏi, đề mục, số dòng/cột của report và liên kết tài liệu: PASS. Đã sửa mô tả thứ tự bốn lệnh xác minh/sinh demo và giải thích sync cần giữ lịch sử cũ; bản clone mới dùng tái lập riêng.
- `reports/verification.json` và câu trả lời mục 08 đã dùng kết quả 103/39 hiện tại. Kết quả `clean_committed_source` 69/39 là lịch sử ở commit ghi sẵn, không relabel thành kiểm tra hiện tại.
- `.venv/bin/python -m tools.t02_verify --write-manifest`: PASS. Lỗi hash report cũ được giải quyết bằng việc cập nhật báo cáo trong phạm vi nhiệm vụ, giữ nguyên hai dòng References của người dùng, kiểm cấu trúc rồi ghi hash đúng file hiện tại.
- Protocol đã freeze, raw/ranked predictions PoC, nhãn evaluator, analysis summary và bốn file metric giữ nguyên từng byte so với HEAD đầu nhiệm vụ; audit/decision log cũ còn nguyên prefix. Chỉ thay kết quả review và bằng chứng liên quan. Không thêm test cho thay đổi câu chữ tài liệu; đã kiểm liên kết, cấu trúc và nội dung tương ứng.

## Hạn chế / bước tiếp

Phần đồng bộ kỹ thuật sau review CVAT đã hoàn tất. Không có xác nhận người học đã trực tiếp review, không có GT giảng viên, deadline lớp hay yêu cầu push. Giữ các trạng thái này đúng thực tế, không thay tag phát hành. Bước tiếp theo của bài nộp là xác nhận review của người học theo hướng dẫn hoàn tất; không cần làm lại phần nhập CVAT. `.obsidian/` không thuộc commit.
