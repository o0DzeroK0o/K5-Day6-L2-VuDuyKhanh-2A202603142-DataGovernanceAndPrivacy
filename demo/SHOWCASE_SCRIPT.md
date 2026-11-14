# Kịch bản showcase 5 phút và debate

Mở `t004_demo.html` offline. Phím mũi tên hoặc PageDown chuyển trang; có thể in từ trình duyệt. Mọi con số trên demo do script lấy từ metrics, không sửa tay.

1. Trang 1 (30 giây): giới thiệu T004/T02, nhóm 1 người, pipeline ưu tiên 20 ảnh. Nêu ngay nhãn nội bộ do AI, chờ người học xác nhận.
2. Trang 2 (60 giây): trình bày 5 bước load/process/rank/review/decide. Show manifest SHA256, split theo scene, protocol freeze trước eval. Baseline là Laplacian toàn ảnh; random chỉ demo wiring.
3. Trang 3 (60 giây): giải thích TP/denominator và so baseline/PoC cùng budget. Bỏ ROI / dùng threshold chung làm giảm recall nội bộ. Bootstrap chứa 0 nên chưa suy rộng độ hơn kém.
4. Trang 4 (60 giây): mở gallery, chỉ rõ glare nhẹ chưa cháy trắng nên bỏ sót. Cam_B/night là hard negatives. PoC cũng chọn một ảnh sạch do quota top20.
5. Trang 5 (90 giây): chạy lệnh PoC thực tế, mở contact sheet; sửa một hành động hợp lý, export CSV, chạy lại và mở audit. Nếu chưa tự review thật, nói rõ đây là AI simulation; không dùng tên mình để giả đã xem. Kết thúc bằng HOLD/REWORK đúng policy, không ép GO.

## Câu hỏi phản biện và cách trả lời

- Vì sao không lấy random làm baseline chính? Đề T02 yêu cầu global Laplacian; random chỉ kiểm nối dây.
- Có dùng GT để rank không? Pipeline chỉ đọc input và config; annotations chỉ vào evaluator/công cụ review sau inference. GT guard và test đảm bảo đường đọc tách biệt.
- Vì sao score nhỏ hơn 0.5 vẫn vào queue? Budget là top20 tương đối; ngưỡng chỉ quyết định hành động gợi ý. Đây là hai khái niệm khác nhau.
- Tại sao chưa nói người thật đã review? Agent không phải học viên. Cần học viên tự xem, export và xác nhận để audit mang tên thật.
- PoC có chắc tốt hơn? Chỉ cải thiện quan sát trên 40 nhãn AI nội bộ; CI chênh lệch chứa 0, còn sai nhãn, cùng generator và domain shift.
- 10 ảnh OOD có đủ không? Chỉ smoke test synthetic từ T13 256x144, tất cả clean theo AI; không có lỗi để đo recall và chưa thay cho dữ liệu thực.
- Nếu gian lận score/ID review thì sao? Test hiện có từ chối stale score, ID lạ/trùng, reviewer trống, override không hợp lệ. Đầu vào thay hash và đường dẫn vượt root cũng bị từ chối.

Chưa diễn ra showcase/debate với người khác; đây là kịch bản luyện tập, không khai báo điểm bonus hay phản biện thực tế đã hoàn thành.
