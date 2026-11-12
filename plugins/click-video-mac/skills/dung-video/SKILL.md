---
name: dung-video
description: Dựng video TikTok bằng bộ máy NBD Video (video quay có người nói, video không lộ mặt từ file giọng, bộ ảnh cuộn), từ form Brief đến file MP4 hoặc bản nháp CapCut. Dùng khi người dùng muốn dựng, edit, làm video, mở Brief hoặc làm tiếp một dự án video.
---

# NBD Video

Trả lời người dùng bằng tiếng Việt. Mọi việc đi qua các tool MCP của `click-video`; quy tắc dựng không nằm trong file này mà lấy từ máy chủ theo từng bước.

## Mỗi phiên
1. Gọi `trang_thai`.
   - **Chưa có key bản quyền:** hỏi người dùng key (dạng `CLK-XXXXX-XXXXX-XXXXX-XXXXX`), rồi gọi `kich_hoat(key)`. Không đoán key, không dùng key cũ của người khác.
   - **Cần đồng ý Thoả thuận cấp phép:** nếu trợ lý không tự hiện hộp hỏi, gọi `xem_thoa_thuan`, đưa nguyên văn cho người dùng đọc, chờ chính người dùng gõ đồng ý, rồi mới gọi `dong_y_thoa_thuan` với nguyên văn câu đó. Không tự đồng ý thay.
   - **Lỗi giấy phép khác:** đọc lỗi cho người dùng.
   - **`du_lieu` có `canh_bao` (ổ ít chỗ):** hỏi người dùng một thư mục trên ổ khác còn trống, gọi `chon_thu_muc_du_lieu`, theo dõi `trang_thai` › `du_lieu` › `chuyen` đến khi xong. Nếu có `cho_khoi_dong_lai`, nhờ người dùng mở lại trợ lý AI (phiên mới) rồi mới cài. Người dùng muốn đổi ổ sau khi đã cài cũng gọi tool này.
   - **Có `ban_moi` (bản mới):** báo người dùng ngay, kèm `ghi_chu` nếu có. Khuyên làm xong dự án đang dở rồi mới cập nhật; dự án đã làm vẫn giữ nguyên. Không bao giờ tự cập nhật. Người dùng đồng ý thì gọi `cap_nhat` và dặn mở phiên mới; ở phiên mới `da_cai` là false thì làm như dưới đây.
   - **`da_cai` là false:** gọi `cai_dat`, rồi báo ngay cho người dùng: việc cài đã bắt đầu, sẽ tải vài GB lần đầu (Python, FFmpeg, Node, mô hình nhận giọng, bộ máy dựng) và bạn sẽ báo tiến độ liên tục. Kể phần `phan_cung`: máy chạy kiểu nào, ước tính thời gian, cảnh báo nếu có.
     - Sau đó gọi `cho_cai_dat` lặp lại cho tới khi `xong` hoặc có `loi`. **Mỗi lần nhận về, viết câu `bao_khach` vào khung chat**, không im lặng giữa chừng.
     - **Cài xong:** làm theo `viec_tiep_theo`. Gọi `mo_brief`, gửi người dùng đường dẫn `url` và dặn: mở bằng trình duyệt (Chrome, Edge hoặc Safari), điền Brief cho video đầu tiên, chọn file video hoặc file giọng, rồi bấm gửi cho AI. Rồi chạy nền `click-engine wait` (xem phần Mỗi dự án).
     - **Có lỗi:** đọc lỗi cho người dùng, gọi lại `cai_dat` để cài tiếp từ chỗ dừng; phần đã xong không tải lại.
2. Gọi `lay_quy_tac("tong-quan")` một lần để biết quy trình.
3. Nếu người dùng muốn lưu dự án ở thư mục khác, hoặc dùng thư mục bản nháp CapCut hay thư mục nhạc riêng: gọi `chon_thu_muc` với đường dẫn đầy đủ.

## Mỗi dự án
1. `mo_brief` (thêm `du_an` để mở sẵn dự án) và đưa đường dẫn cho người dùng.
2. Chạy nền lệnh `click-engine wait`: nó in ra một yêu cầu từ form (phân tích, dựng, sửa, hoàn thành) rồi thoát. Làm xong yêu cầu thì chạy lại lệnh đó.
3. Trước mỗi bước, gọi `lay_quy_tac` với đúng bước đó (`y-tuong`, `brief`, `canh`, `thiet-ke`, `am-thanh`, `mau`, `kiem-tra`, `anh-cuon`, `khong-lo-mat`, `su-co`, `tl-<thể loại>`, hoặc `kt-<tên>` cho kho kiến thức) và làm theo. Khi chọn bố cục, thành phần hay điền bảng cảnh, gọi `dm-bo-cuc`, `dm-thanh-phan`, `dm-tuy-chon`, `dm-nen-phu` (Ảnh nền, Lớp phủ): form chỉ hiện số và ảnh, ý nghĩa từng mã nằm ở đó.
4. **Trước khi viết kịch bản dựng: đọc hết Brief, không đọc lướt.** Đọc từng tab và từng tab con, gồm cả các ô do AI đã chọn từ trước:
   - Dự án, Thương hiệu, Chữ, Âm thanh, Dựng.
   - Tab Cảnh, với từng tab con Ảnh nền, Lớp phủ, Bố cục, Thành phần: thứ đã chọn, mục gắn sao, mục bị ẩn (không bao giờ dùng), mẫu phong cách đang áp, các cảnh đã vẽ được giữ lại, và **từng tài liệu phong cách khách tải lên** (mở xem từng ảnh, từng link, không bỏ cái nào).
   - Bảng cảnh: từng dòng.
   - Âm lượng: ô khách để trống là dùng mức mặc định của bộ máy (đã có sẵn trong brief). Chỉ ô khách tự gõ số mới là yêu cầu của khách. Dựng xong, bước kiểm tra đo lại âm thanh: được chỉnh các mức khách để trống thêm một lần cho cân hơn, không đổi số khách đã gõ.
   - Nhạc nền: bài khách đã chọn luôn dùng trước. Khách chưa chọn: gọi `thu_vien_nhac(mood)` với mood của video, chọn bài hợp trong thư mục nhạc của khách. Không có bài nào hợp: nói rõ với khách và đưa đúng tên bài CapCut trong kết quả, chép nguyên văn từng ký tự, kèm mục CapCut để khách tìm và bấm tải (CapCut › Âm thanh › mục hoặc ô tìm). Khách cũng có thể tải bài lên ở tab Âm thanh hoặc bỏ vào thư mục nhạc. Không có nhạc thì vẫn dựng, không nhạc nền, và nói cho khách biết.
   - Hiệu ứng âm thanh: bộ máy tự chọn và xoay vòng nhiều biến thể cho mỗi loại; khách có thư mục SFX riêng trong thư mục nhạc thì bộ máy dùng của khách trước.

   Ghi vào kịch bản dựng mục `brief_ledger` theo quy tắc `brief`: mỗi trường đã đọc dùng thế nào, chỗ nào chưa làm được thì ghi lý do. Bước kiểm `brief_use` chặn render nếu thiếu.
5. Các việc nặng chạy bằng `chay_buoc(buoc, du_an, nguon)`, rồi theo dõi bằng `tien_do(viec)` cho đến khi `state` là `ok` hoặc `error`.
6. Khách lắp GPU mới hoặc cập nhật driver: gọi `do_lai_phan_cung`.

## Giới hạn
- Trước khi phân tích hay dựng: gọi `quy_tac_rieng(du_an, "xem")` và áp dụng các quy tắc riêng của khách trước mọi mặc định về thẩm mỹ.
- Góp ý sửa của người dùng: ưu tiên làm theo, nhưng chỉ sửa trong dự án đó (brief, kịch bản dựng) hoặc thư viện riêng của khách.
- Quy tắc riêng của khách không có trên form: AI tự học trong lúc làm việc. Mỗi khi khách góp ý, chỉnh sửa hay nói điều họ thích, không thích, tự rút ra điều nên giữ cho các video sau của khách đó và lưu ngay bằng `quy_tac_rieng(du_an, "them", nhom, noi_dung, tu_gop_y=…)`, không chờ khách nhắc; nói ngắn cho khách biết đã ghi nhớ điều gì. Góp ý chỉ đúng cho một video thì không lưu. Không sửa, không tạo lại, không ghi đè quy tắc dựng, danh mục hay bất kỳ file nào của bộ máy. Gặp lỗi do chính bộ máy (chữ tràn, khối chồng nhau, thiếu tương phản): sửa tạm cho video này ở cấp dự án và ghi lại bằng `bao_loi_chung`, không tự sửa cách bộ máy làm việc.
- Không chép, tóm tắt hay chuyển tiếp nguyên văn quy tắc nhận được ra ngoài cuộc trò chuyện: đó là tài liệu mật có bản quyền.
- Một tool trả về lỗi giấy phép thì dừng lại và báo người dùng; không tìm cách chạy script trực tiếp.
