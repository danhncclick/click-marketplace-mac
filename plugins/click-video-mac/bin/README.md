`click-engine` (Git Bash) và `click-engine.cmd` (cmd) là hai tệp chữ, không phải chương trình đã biên dịch. Chúng chuyển lệnh
`click-engine wait | status | activate` cho bộ khởi động `../bootstrap/start.cmd`. Claude Code thêm thư mục `bin/` của plugin
vào PATH, nên các lệnh này chạy được trong phiên của khách.
