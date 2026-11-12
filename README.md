# NBD Video cho Mac

© 2026 Nguyễn Bá Duy. Bảo lưu mọi quyền. Nghiêm cấm sao chép, phân phối, dịch ngược.

Bản cho máy Mac. Máy Windows: xem `danhncclick/click-marketplace`.

## Cách cài

### Bước 1. Cài Claude

Tải ở https://claude.ai/download, cài, đăng nhập. Mở Claude, chọn tab **Code**.

### Bước 2. Cài Git

Gửi cho Claude tin nhắn này:

```
Chạy lệnh này giúp tôi: xcode-select --install
```

Hiện hộp thoại: bấm **Cài đặt**, chờ cài xong. Máy đã có Git thì Claude sẽ báo, chuyển sang bước 3.

### Bước 3. Tắt hẳn Claude rồi mở lại

Bấm vào cửa sổ Claude, nhấn **Cmd + Q** để thoát hẳn. Sau đó mở lại Claude, chọn tab **Code**.

### Bước 4. Thêm NBD Video

Gửi cho Claude dòng này:

```
/plugin marketplace add danhncclick/click-marketplace-mac
```

- Hiện cửa sổ **Thêm marketplace**: bấm **Đồng bộ**.
- Hiện danh sách: bấm dấu **+** ở **NBD Video (Mac)**. Dấu + đổi thành bánh răng là xong.

(Dùng Claude trong cửa sổ dòng lệnh: gõ thêm `/plugin install click-video-mac@click-media`.)

### Bước 5. Nhập key

Bấm **Tạo mới**. Gửi tin nhắn này (thay bằng key của bạn):

```
Cài NBD Video với key CLK-XXXXX-XXXXX-XXXXX-XXXXX rồi mở Brief cho tôi.
```

- Claude hiện Thoả thuận: trả lời **đồng ý**.
- Claude hỏi cho phép: bấm **Luôn cho phép**.
- Chờ cài (10–30 phút). Xong, Claude gửi một đường dẫn: bấm vào để mở form Brief.

Xong. Lần sau chỉ cần mở Claude, tab **Code**, nhắn "Mở Brief cho tôi".

## Cập nhật bản mới

1. Khi có bản mới, trên form Brief hiện thanh vàng "Có bản NBD Video mới". Bấm **Cập nhật ngay**. (Không thấy thanh vàng: nhắn Claude "Cập nhật NBD Video".)
2. Claude báo đã tải bản mới: trong Claude bấm **Tạo mới**, nhắn: Mở Brief cho tôi
3. Chờ Claude cài nốt (vài phút, có báo tiến độ), rồi bấm đường dẫn Claude gửi để mở lại Brief. Dự án đang làm giữ nguyên.
4. Mỗi tháng một lần, cập nhật luôn phần plugin: gửi cho Claude dòng /plugin marketplace update click-media

## Tắt Claude thì sao

- Tắt Claude, form Brief vẫn mở và sửa được bình thường, kể cả Đọc video & phân tích.
- Bấm Dựng hoặc AI phân tích lúc Claude đang tắt: góc dưới hiện "AI chưa kết nối", yêu cầu nằm chờ, không mất.
- Mở Claude, bấm **Tạo mới**, nhắn: Mở Brief cho tôi. AI tự làm tiếp yêu cầu đang chờ, không cần bấm lại.

## Dùng Codex (ChatGPT) thay cho Claude

Làm như trên, chỉ khác:

- Bước 1: cài Codex của ChatGPT.
- Bước 4: gõ trong cửa sổ lệnh `codex plugin marketplace add danhncclick/click-marketplace-mac`, rồi `codex plugin add click-video-mac@click-media`.
- Bước 5: gõ `codex` để mở, rồi gửi tin nhắn có key.

## Cần giúp

Chụp màn hình chỗ bị lỗi, gửi cho bên bán.

Thoả thuận cấp phép: [LICENSE.md](LICENSE.md). Thành phần bên thứ ba: [THANH-PHAN-BEN-THU-BA.md](THANH-PHAN-BEN-THU-BA.md).
