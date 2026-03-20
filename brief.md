# 🛡️ Project Brief: CyberSentinel AI 
**Automated OSINT Threat Hunter - Tác nhân AI săn lùng rò rỉ dữ liệu tự động**

**Track tham dự:** Tiny Fish + AWS (Giải quyết bài toán doanh nghiệp quy mô lớn).
**Quy mô nhóm:** 2 thành viên (Tập trung 100% vào Core Logic & System Architecture, không dùng UI phức tạp).

---

## 1. Tổng quan dự án (Executive Summary)
CyberSentinel AI là một hệ thống tác nhân trí tuệ nhân tạo (AI Agent) hoạt động 24/7, chuyên rà soát các nguồn thông tin tình báo mở (OSINT) để phát hiện sớm các rò rỉ dữ liệu nhạy cảm của doanh nghiệp (như API Key, Source Code, Mật khẩu nội bộ). Hệ thống kết hợp khả năng điều hướng web động của **Tiny Fish** và sức mạnh phân tích ngôn ngữ tự nhiên của **AWS Bedrock**.

## 2. Bài toán thực tế (The Problem)
* **Nguy cơ rò rỉ cao:** Lỗi do con người (nhân viên vô tình push code chứa API Key lên GitHub công khai, lộ credential trên Pastebin hoặc các diễn đàn công nghệ).
* **Hạn chế của công cụ cũ:** Các công cụ quét tự động truyền thống thường bị chặn bởi Captcha, không xử lý được giao diện web động (dynamic rendering), và thường xuyên báo động giả (False Positive) do không hiểu ngữ cảnh của đoạn code bị lộ.

## 3. Giải pháp cốt lõi (The Solution)
Xây dựng một quy trình Tự động hóa Không gian làm việc (Workspace Automation) cho bộ phận An ninh mạng (SOC/IT Security):
1. Dùng bot giả lập người dùng lách qua các rào cản kỹ thuật của website để thu thập dữ liệu rò rỉ.
2. Ứng dụng AI để phân tích ngữ cảnh của tệp dữ liệu, phân loại mức độ rủi ro.
3. Kích hoạt quy trình cảnh báo khẩn cấp (Incident Response) hoàn toàn tự động.

## 4. Kiến trúc hệ thống (System Architecture & Data Flow)
Hệ thống được thiết kế theo kiến trúc Serverless, tối ưu hóa băng thông mạng và bảo mật luồng dữ liệu.

* **Bước 1 - Data Collection (Tiny Fish):** Script điều khiển bot tự động truy cập `github.com/search` hoặc `pastebin.com`, nhập từ khóa mục tiêu (ví dụ: `Tên_Doanh_Nghiệp + "password"`), lọc bỏ HTML tags và trích xuất raw text.
* **Bước 2 - API Gateway (AWS):** Dữ liệu thô được đóng gói thành JSON và gửi qua HTTP POST request đến cổng API bảo mật trên đám mây.
* **Bước 3 - Threat Analysis (AWS Lambda + Bedrock):** * Lambda nhận dữ liệu, gọi model AI (Claude/Llama) trên Bedrock.
    * AI đánh giá đoạn text dựa trên System Prompt chuẩn an toàn thông tin, trả về kết quả định dạng: `{is_threat: true/false, threat_type: "API_Key_Leak", severity: "CRITICAL"}`.
* **Bước 4 - Alerting (AWS SNS):** Nếu `severity == CRITICAL`, hệ thống mạng nội bộ tự động kích hoạt Amazon SNS bắn cảnh báo SMS/Email trực tiếp đến quản trị viên hệ thống.

## 5. Ngăn xếp công nghệ (Tech Stack)
* **Thu thập dữ liệu:** Tiny Fish Web Agent API.
* **Hạ tầng mạng & Xử lý sự kiện:** AWS API Gateway, AWS Lambda.
* **Trí tuệ nhân tạo (LLM):** Amazon Bedrock.
* **Hệ thống cảnh báo:** Amazon SNS (Simple Notification Service).

## 6. Điểm nổi bật của dự án (Key Differentiators)
* **Zero-Cost & Serverless:** Vận hành hoàn toàn trên hạ tầng đám mây Serverless, chi phí duy trì gần như bằng 0 khi không có sự kiện phát sinh. Khả năng mở rộng (scalability) vô hạn.
* **Vượt rào cản Web tĩnh:** Khác biệt hoàn toàn so với việc cào dữ liệu (scraping) thông thường, hệ thống dùng Tiny Fish để tương tác như con người, giải quyết triệt để điểm mù của các hệ thống giám sát bảo mật truyền thống.
* **Độ chính xác cao:** Thay vì dùng Regex (biểu thức chính quy) cứng nhắc, việc dùng LLM (AWS Bedrock) giúp hệ thống "hiểu" được đâu thực sự là một API Key đang hoạt động và đâu chỉ là một đoạn code ví dụ (dummy data), giảm thiểu tối đa báo động giả.