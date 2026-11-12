# Thành phần bên thứ ba

NBD Video © 2026 Nguyễn Bá Duy. Phần mềm dùng các thành phần dưới đây. Mỗi thành phần thuộc về chủ sở hữu của nó và tuân theo giấy phép riêng. Thoả thuận cấp phép của NBD Video không thay đổi các giấy phép đó.

## A. Tự tải về máy khách khi cài (không nằm trong gói NBD Video)

| Thành phần | Nguồn | Giấy phép |
|---|---|---|
| Python 3.12 (bản embeddable), tcl/tk | python.org | PSF License |
| pip | pypa.io | MIT |
| faster-whisper | PyPI | MIT |
| CTranslate2 | PyPI | MIT |
| Mô hình Whisper large-v3 (bản CTranslate2 của Systran), máy có GPU NVIDIA | Hugging Face | MIT |
| Mô hình Whisper large-v3-turbo (bản CTranslate2 của Mobius Labs), máy không có GPU NVIDIA | Hugging Face | MIT |
| NVIDIA cuBLAS, cuDNN | PyPI (NVIDIA) | Giấy phép NVIDIA, khách đồng ý khi tải |
| MediaPipe | PyPI | Apache 2.0 |
| NumPy | PyPI | BSD-3-Clause |
| OpenCV (headless) | PyPI | Apache 2.0 |
| Pillow | PyPI | MIT-CMU (HPND) |
| fontTools | PyPI | MIT |
| PyAV | PyPI | BSD-3-Clause; thư viện FFmpeg đi kèm theo LGPL |
| soundfile | PyPI | BSD-3-Clause |
| cryptography | PyPI | Apache 2.0 hoặc BSD |
| FFmpeg (bản GPL của BtbN) | github.com/BtbN/FFmpeg-Builds | GPL v3. Chạy như một chương trình riêng, không liên kết vào NBD Video. Mã nguồn có tại ffmpeg.org |
| Node.js | nodejs.org | MIT |
| LUT DJI D-Log, D-Log2 | dji.com | Theo điều khoản của DJI |
| LUT Sony S-Log3 (Look Profile) | pro.sony | Theo điều khoản của Sony |

## B. Đi kèm trong gói NBD Video

| Thành phần | Giấy phép | Ghi chú |
|---|---|---|
| Remotion và các gói @remotion | Remotion License | **Cần xác nhận với Remotion trước khi bán**, xem `HUONG-DAN-PHAP-LY.md` mục 4 |
| React, React DOM | MIT | Nằm trong bundle Remotion |
| Remix Icon | Apache 2.0 | `assets/icons/remixicon` |
| Unicons (IconScout) | Apache 2.0 | `assets/icons/unicons` |
| Phông Google Fonts: Anton, Barlow Condensed, Be Vietnam Pro, Chakra Petch, Dancing Script, Great Vibes, Inter, Manrope, Montserrat, Mulish, Noto Serif, Nunito, Open Sans, Oswald, Plus Jakarta Sans, Space Grotesk, Unbounded | SIL Open Font License 1.1 | Phải kèm file OFL.txt của từng phông |
| Roboto | Apache 2.0 (bản mới: OFL 1.1) | Kèm giấy phép theo bản đang dùng |
| Mô hình MediaPipe selfie_multiclass_256x256 | Apache 2.0 | `assets/models` |
| Khung iPhone (`assets/frames/iphone_*`) | **Chưa rõ nguồn** | Xác minh nguồn hoặc thay bằng khung tự vẽ trước khi bán |
| Âm thanh hiệu ứng `assets/sfx` | Do NBD Video tự tổng hợp (`make_sfx.ps1`) | Thuộc Nguyễn Bá Duy |

## C. Dịch vụ và nhãn hiệu

Các tên dưới đây thuộc chủ sở hữu tương ứng. NBD Video không liên kết với họ và không được họ bảo trợ:

- Claude, Anthropic;
- Codex, ChatGPT, OpenAI;
- CapCut, TikTok, ByteDance;
- DJI, Osmo;
- Sony, S-Log3, S-Gamut3.Cine;
- Apple, iPhone;
- Google Fonts.

---

Văn bản đầy đủ của từng giấy phép trong mục B được chép vào thư mục `licenses/` khi đóng gói.

## D. Ý tưởng tham khảo, đã vẽ lại (không chép mã)

| Thành phần | Nguồn ý tưởng | Giấy phép |
|---|---|---|
| K01–K07 (quanh người nói) | claude-video-effects (gói "aidesign-video-skills", AI Design) | MIT |
| K08–K14 (chữ và nhịp kể) | video-shotcraft (gói "aidesign-video-skills", AI Design) | Apache-2.0 |

Các thành phần K được viết mới bằng ngôn ngữ thiết kế của NBD Video, không chứa mã của hai nguồn trên; ghi ở đây để ghi công ý tưởng.
