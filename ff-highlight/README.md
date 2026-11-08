# Free Fire Highlight – tự động dựng video

Đưa video quay màn hình vào, công cụ tự tìm các pha đấu súng và dựng thành video highlight.

## Tự động làm gì
- **Tìm pha hay**: nghe tiếng súng/nổ (xung âm thanh dồn dập, giàu tần số cao) và đo chuyển động màn hình mạnh.
- **Cắt đoạn**: lấy 4s trước và 2s sau mỗi khoảnh khắc đỉnh, gộp các pha gần nhau.
- **Hiệu ứng**: slow-motion 0.5x quanh khoảnh khắc đỉnh, chuyển cảnh chớp trắng, chữ tiêu đề, fade đầu/cuối.
- **Âm thanh**: chuẩn hoá âm lượng; nhạc nền tự nhỏ lại khi có tiếng súng.
- **Xuất**: 1920x1080 (YouTube) hoặc 1080x1920 (TikTok/Shorts/Reels, nền mờ), 60fps.

## Cách dùng
Cần `ffmpeg` và `python3` + `numpy`.

```bash
# Cơ bản: video 60s, 16:9
python3 ff-highlight/ffhl.py quay_man_hinh.mp4 -o highlight.mp4

# TikTok dọc 30s, có nhạc nền và tiêu đề riêng
python3 ff-highlight/ffhl.py tran1.mp4 tran2.mp4 --vertical --length 30 \
    --music nhac.mp3 --title "BOOYAH! 12 KILL"

# Chỉ xem các đoạn phát hiện được (không dựng)
python3 ff-highlight/ffhl.py quay_man_hinh.mp4 --analyze

# Tự chọn đoạn
python3 ff-highlight/ffhl.py quay_man_hinh.mp4 --segments "01:12-01:20,03:05-03:15"
```

Tuỳ chọn khác: `--pre`, `--post`, `--gap`, `--no-slowmo`, `--music-vol`, `--fps`.

Mẹo: bật âm thanh game khi quay màn hình — phát hiện pha bắn chính xác hơn nhiều so với chỉ dùng hình.

## Chế độ kể chuyện (`--story`)
Giữ liền mạch một đoạn (ví dụ từ lúc đồng đội hồi sinh tới hết pha highlight). Đoạn giao tranh giữ tốc độ thường và có slow-mo, đoạn đi lại/loot tự tua nhanh (hiện ">> x2.5") để vừa `--length`.

```bash
python3 ff-highlight/ffhl.py tran.mp4 --story 03:20-05:45 --length 60 --vertical \
    --title "" --caption "Khi đồng đội hồi sinh|một con hổ"
```
