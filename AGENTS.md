# Quy trình làm việc của dự án

## Git và commit
- Dự án phải được quản lý bằng Git. Trước mỗi nhiệm vụ kiểm tra `git status` và gốc repository; không tạo repository lồng nhau nếu chưa hỏi người dùng.
- Sau mỗi nhiệm vụ hoặc nhóm thay đổi hoàn chỉnh tạo commit gồm mã nguồn, test và tài liệu; nhiệm vụ chỉ khảo sát cũng ghi kết quả trong `docs/` và commit.
- Chỉ stage/commit phần thuộc nhiệm vụ; không ghi đè, hoàn tác hoặc đưa thay đổi không liên quan của người dùng vào commit.
- Commit rõ mục đích, ưu tiên `feat:`, `fix:`, `test:`, `docs:`, `chore:`. Không tự push, force-push, sửa lịch sử hoặc dùng Git gây mất dữ liệu.
- Không tự đặt danh tính hay thay đổi cấu hình Git toàn cục; nếu commit bị chặn báo nguyên nhân và xin quyền/thông tin bằng cơ chế môi trường.
- Duy trì `.gitignore`: không theo dõi bí mật, token, API key, `.env`, dependencies, cache, build artifacts; chỉ `.env.example` không bí mật được theo dõi.

## Kiểm thử và xác minh
- Mỗi thay đổi mã nguồn/hành vi có test mới hoặc cập nhật test liên quan; nếu chưa có hệ thống test thì thiết lập tối thiểu, không tạo test giả.
- Tài liệu/cấu hình không cần test tự động phải giải thích lý do và xác minh phù hợp.
- Trước commit/bàn giao chạy test liên quan, toàn bộ test, lint/typecheck/build phù hợp. Chỉ xác nhận hoàn tất khi kiểm tra bắt buộc pass.
- Ghi lệnh, kết quả thật, lỗi/trở ngại trong `docs/`; không tuyên bố pass khi chưa có bằng chứng, không tắt test/hạ tiêu chuẩn hay sửa ngoài phạm vi để pass.
- Khi bị chặn chỉ commit tiến độ chưa hoàn tất nếu người dùng cho phép, ghi rõ trong nhật ký và commit.

## Tài liệu trong docs/
- Luôn duy trì `docs/` và `docs/README.md` làm mục lục tới mọi nhật ký.
- Mọi nhiệm vụ (kể cả thiết lập/khảo sát/test/cấu hình) có nhật ký `docs/YYYY-MM-DD-HHMMSS-mo-ta-ngan.md`; nhiệm vụ đang tiếp tục chỉ cập nhật nhật ký của chính nó.
- Ghi mục tiêu, việc đã làm/quyết định, tệp thay đổi, lệnh xác minh và kết quả, hạn chế/bước tiếp; không ghi bí mật/dữ liệu nhạy cảm.
- Cập nhật nhật ký trong quá trình làm và trước commit; tài liệu cùng commit với thay đổi; tổng hợp theo nhiệm vụ, không cần ghi mỗi lần đọc file.
- Không ghi hash của chính commit vào tài liệu; báo hash khi bàn giao.

## Khởi tạo và bàn giao
- Nếu đã có đủ Git, ignore, AGENTS, mục lục và nhật ký khởi tạo thì chỉ kiểm tra, không tạo trùng. Chỉ bổ sung phần thiếu; hỏi nếu có xung đột quy định.
- Trước commit khởi tạo kiểm AGENTS, ignore, liên kết, diff và staged files để tránh bí mật/phần không liên quan. Commit: `chore: initialize project workflow and documentation`.
- Bàn giao tóm tắt thay đổi, trạng thái test thật, liên kết nhật ký, hash/thông điệp commit và trở ngại/phần chưa hoàn tất.

## Phạm vi bài nộp T004 / T02
- Đọc `HUONG_DAN_HOC_VIEN.html`, `README.md`, `docs/tracks/T02.md`; giữ nguyên câu hỏi, đề mục, cấu trúc và bảng của report, chỉ điền câu trả lời/ô trống/checklist đúng thực tế.
- Không đọc GT giảng viên trong pipeline; không tune eval; số liệu phải do script tạo. Nhãn tự kiểm phải khai báo nguồn, không trình bày thành GT chính thức.
- Không giả người review: AI review phải ghi AI; phần con người cần xác nhận phải hướng dẫn cụ thể và để trạng thái chờ.
