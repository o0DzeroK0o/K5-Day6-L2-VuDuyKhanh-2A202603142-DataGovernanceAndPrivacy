# Kịch bản showcase 5 phút và debate

Mở `t004_demo.html` offline. Phím mũi tên hoặc PageDown chuyển trang. Bấm ảnh trên slide để mở screenshot gốc. Số liệu do script lấy từ evidence đã lưu.

1. Trang 1 (50 giây): giới thiệu T004/T02 và Vũ Duy Khanh, 96 ảnh synthetic. Đi qua 5 bước pipeline. Chỉ giao diện offline mới: 20 frame, 2 override và tên người review. Giải thích split theo scene và freeze trước eval.
2. Trang 2 (80 giây): chỉ ảnh mở lại frame 17 sau Save, `review_source=Vũ Duy Khanh` và nhận xét lỗi nén trong `review_note`. So gợi ý KEEP với tag RECAPTURE. Mở gallery để xem đủ 20 frame, gồm frame 18 KEEP và frame 19 override do quầng lóa. Score/ranking giữ nguyên.
3. Trang 3 (50 giây): chỉ định dạng CVAT for images 1.1 và Requests Finished. Mở XML và mapping, đối chiếu 20 image/20 tag với 19 RECAPTURE + 1 KEEP. Nêu export đã kiểm khớp API sau lưu.
4. Trang 4 (60 giây): giải thích Recall@20, TP/denominator, so baseline/PoC cùng budget. CI chênh lệch chứa 0. Chỉ glare nhẹ `img_03_2` còn bị bỏ sót; mở gallery failure cases khi cần giải thích night và cam_B. Các nhãn tự kiểm là nhãn quan sát nội bộ, nguồn trong reports/annotations/README.md; chưa là điểm chính thức.
5. Trang 5 (60 giây): chỉ tổng 20 tag trong CVAT Info và các đường dẫn evidence. Nêu xác nhận trực tiếp của Vũ Duy Khanh cho đủ 20 frame. Pipeline REWORK / QUALITY_RECAPTURE_REQUIRED; 19 ảnh cần thu lại, 1 KEEP. Mở bộ lọc hai override trên giao diện mới và chỉ bản xác nhận, CSV, audit. Mở hướng dẫn chạy nếu muốn trình diễn `make run OUT=out/demo-live` và contact sheet.

## Câu hỏi phản biện và cách trả lời

- Vì sao không lấy random làm baseline chính? Đề T02 yêu cầu global Laplacian; random chỉ kiểm nối dây.
- Có dùng GT để rank không? Pipeline chỉ đọc input và config; annotations chỉ vào evaluator/công cụ review sau inference. GT guard và test kiểm soát đường đọc.
- Vì sao score nhỏ hơn 0.5 vẫn vào queue? Budget là top20 tương đối; ngưỡng quyết định hành động gợi ý.
- CVAT completed có nghĩa người học đã review? Đây là trạng thái job gán nhãn. Bài này có thêm xác nhận trực tiếp của Vũ Duy Khanh, ghi riêng với thời điểm và checksum, nên lần chạy hiện tại có `human_review_confirmed=true`.
- Có phải 19 RECAPTURE là metric chính thức? Đó là số quyết định trong demo CVAT. Metric dùng dữ liệu tự kiểm và evaluator đã freeze, không thay theo tag vừa nhập.
- PoC có chắc tốt hơn? Chỉ cải thiện quan sát trên 40 nhãn nội bộ; CI chứa 0, còn sai nhãn và domain shift.
- 10 ảnh OOD có đủ không? Chỉ smoke test synthetic từ T13 256×144, tất cả clean theo quan sát nội bộ; không có lỗi để đo recall và chưa thay cho dữ liệu thực.
- Nếu sai ID/score review hoặc thiếu frame thì sao? Test pipeline từ chối ID lạ/trùng và stale score. Verifier CVAT kiểm đủ 20 frame, mapping, ảnh gốc, tag, thuộc tính, snapshot API và screenshot.

Chưa diễn ra showcase/debate với người khác; đây là kịch bản luyện tập. Không khai báo bonus hoặc phản biện thực tế đã hoàn thành.
