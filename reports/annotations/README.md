# Nhãn kiểm tra nội bộ, không phải GT giảng viên

`internal_eval_labels.csv` gồm 40 nhãn quan sát sau commit freeze `6c525dc`, không dùng điểm dự đoán khi gán nhãn. Nguồn cụ thể giữ trong cột `annotator`, phương pháp ở `annotation_basis`, thời điểm ở `annotated_at`; các trường nguồn gốc không thay đổi trong nhiệm vụ giao diện/review.

Nhãn dựa trên khả năng nhìn rõ xe/người/biển synthetic. Cam_B hơi mềm và night còn hữu ích được giữ. Severity là ước lượng bằng quan sát. Không lấy nhãn từ tên file, thứ tự ảnh hay GT ẩn. Một nguồn nhãn, chưa có đồng thuận độc lập hoặc GT chính thức; các metric mô tả trên proxy và chưa bao gồm sai số gán nhãn.

Vũ Duy Khanh đã xác nhận trực tiếp 20 frame trong review queue. Xác nhận này không chứng nhận toàn bộ 40 nhãn eval; `human_verified` của tập eval không được đổi. Không sửa nhãn để làm đẹp số.

`ood_visual_labels.csv` gồm 10 ảnh đầu theo image_id của T13, protocol chọn trước eval. Dữ liệu 256×144 cùng họ generator, tất cả clean theo nhãn quan sát; chỉ kiểm thử khác track/độ phân giải, không đủ để đo recall lỗi hoặc chứng minh OOD đời thực.

Pipeline không đọc các file nhãn này. Evaluator và công cụ đóng gói bằng chứng dùng chúng sau inference. Review hiện tại và lịch sử được phân biệt bằng [bản xác nhận](../human_review_confirmation.json).
