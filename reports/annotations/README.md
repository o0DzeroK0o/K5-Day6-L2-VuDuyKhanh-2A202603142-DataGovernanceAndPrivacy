# Nhãn kiểm tra nội bộ, KHÔNG phải GT giảng viên

`internal_eval_labels.csv`: Codex đã quan sát trực tiếp 40 ảnh eval sau commit freeze `6c525dc`, chưa xem điểm dự đoán để gán nhãn. Nhãn dựa trên khả năng nhìn rõ xe/người/biển synthetic. Cam_B hơi mềm và night còn hữu ích được giữ. Severity là ước lượng bằng mắt. Không lấy nhãn từ tên file, thứ tự ảnh hay GT ẩn.

Một reviewer AI, không có đồng thuận độc lập, không có nhãn chính thức, nên các metric chỉ chứng minh luồng tự kiểm và mô tả trên proxy. Người thật cần kiểm lại toàn bộ nhãn, đặc biệt glare nhẹ và nén nhẹ. Không đổi nhãn để làm đẹp số.

`ood_visual_labels.csv`: 10 ảnh đầu theo image_id của T13, đã chọn protocol trước eval. Dữ liệu 256x144 cùng họ generator nên chỉ là kiểm thử khác track/độ phân giải; chưa chứng minh OOD đời thực. Tất cả được AI đánh giá còn dùng được, tập này không đủ để đo recall lỗi.

Pipeline không nhập/đọc các file này. Chỉ evaluator và công cụ đóng gói bằng chứng dùng chúng sau inference. Vòng AI review sử dụng lại nhận xét thị giác này, không tuyên bố là người thật hay một nguồn nhãn độc lập.
