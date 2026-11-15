# Kịch bản showcase 5 phút và debate

Khởi động `make web`, mở **http://127.0.0.1:8765**. Mở `t004_demo.html` để trình chiếu; phím mũi tên hoặc PageDown chuyển trang. Ảnh demo lấy từ lần thực thi HTTP và CVAT local, số liệu từ bằng chứng đã lưu.

1. Trang 1 (50 giây): giới thiệu T004/T02, Vũ Duy Khanh và 96 ảnh synthetic. Sang ứng dụng web, tạo lượt mới, bấm **Nạp dữ liệu**, **Chạy Process**, **Xếp hạng queue**. Chỉ bảng 96 tín hiệu, pool 40 eval và queue 20 ảnh. Mỗi nút có thời gian thực thi và output tải về.
2. Trang 2 (70 giây): mở ảnh CVAT sau Save, `review_source=Vũ Duy Khanh` và nhận xét lỗi nén trong `review_note`. So gợi ý KEEP với tag RECAPTURE ở `img_19_2`. Gallery có đủ 20 frame. Nhắc xác nhận trực tiếp đã bao phủ 19 RECAPTURE và 1 KEEP.
3. Trang 3 (70 giây): ở web Review, đi qua các frame, phóng to ảnh, chỉ hai override `img_19_2` và `img_06_3`. Bấm **Nạp 20 quyết định đã xác nhận** để dùng đúng biên nhận đã lưu. Chỉ trạng thái 20/20, reviewer và audit. Nếu muốn thử sửa mới, dùng lượt khác; sửa form sẽ bỏ dấu xác nhận, phải lưu trước Decide. XML export và ảnh CVAT Requests Finished vẫn có link để đối chiếu.
4. Trang 4 (60 giây): giải thích Recall@20 và Precision@20, so baseline/PoC cùng budget. CI chênh lệch chứa 0. Chỉ glare nhẹ `img_03_2` còn bỏ sót; mở failure gallery khi cần giải thích night/cam_B. Nhãn tự kiểm là nhãn quan sát nội bộ, chưa phải điểm chính thức.
5. Trang 5 (50 giây): bấm **Chạy Decide**. Chỉ REWORK / QUALITY_RECAPTURE_REQUIRED và 20 review trực tiếp. Tải `decision.json`, `review_queue_reviewed.csv`, mở lịch sử và tải lại trang để chứng minh kết quả đã lưu. Thu lại 19 ảnh trong queue, giữ `img_23_1`. Các lượt mới giữ cùng thuật toán và không ghi đè report đã ký duyệt.

Nếu chưa khởi động server, bấm link web trên slides sẽ chưa mở được. Dùng [gallery ảnh năm bước](web/index.html) để trình bày ảnh chụp; gallery không thực thi pipeline.

## Câu hỏi phản biện và cách trả lời

- Vì sao không lấy random làm baseline chính? Đề T02 yêu cầu global Laplacian; random chỉ kiểm nối dây.
- Có dùng GT để rank không? Pipeline chỉ đọc input và config; annotations chỉ vào evaluator/công cụ review sau inference. GT guard và test kiểm soát đường đọc.
- Vì sao score nhỏ hơn 0.5 vẫn vào queue? Budget là top20 tương đối; ngưỡng quyết định hành động gợi ý.
- CVAT completed có nghĩa người học đã review? Đây là trạng thái job gán nhãn. Bài này có thêm xác nhận trực tiếp của Vũ Duy Khanh, ghi riêng với thời điểm và checksum, nên lần chạy hiện tại có `human_review_confirmed=true`.
- Có phải 19 RECAPTURE là metric chính thức? Đó là số quyết định trong demo CVAT. Metric dùng dữ liệu tự kiểm và evaluator đã freeze, không thay theo tag vừa nhập.
- PoC có chắc tốt hơn? Chỉ cải thiện quan sát trên 40 nhãn nội bộ; CI chứa 0, còn sai nhãn và domain shift.
- 10 ảnh OOD có đủ không? Chỉ smoke test synthetic từ T13 256×144, tất cả clean theo quan sát nội bộ; không có lỗi để đo recall và chưa thay cho dữ liệu thực.
- Web có tự nhận xác nhận của lượt trước không? Lượt mới chưa xác nhận. Nút nhập kiểm đúng queue, điểm và ảnh trước khi dùng bản CVAT đã duyệt. Sửa quyết định không tự kế thừa xác nhận.
- Nếu sai ID/score review hoặc thiếu frame thì sao? Test pipeline từ chối ID lạ/trùng và stale score. Verifier CVAT kiểm đủ 20 frame, mapping, ảnh gốc, tag, thuộc tính, snapshot API và screenshot.

Chưa diễn ra showcase/debate với người khác; đây là kịch bản luyện tập. Không khai báo bonus hoặc phản biện thực tế đã hoàn thành.
