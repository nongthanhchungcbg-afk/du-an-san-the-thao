# TÀI LIỆU THIẾT KẾ HỆ THỐNG & TỔNG HỢP TOÀN BỘ SƠ ĐỒ UML
## DỰ ÁN: HỆ THỐNG QUẢN LÝ SÂN THỂ THAO CÓ TÍCH HỢP TRÍ TUỆ NHÂN TẠO (AI)
**Học phần:** Ứng dụng Trí tuệ Nhân tạo (AIA331)  
**Nhóm thực hiện:** Nhóm 03  
**Tệp dự án StarUML đính kèm mở trực tiếp:** `F:\Du_An_San_The_Thao_StarUML.mdj`

---

# PHẦN 1. BÁO CÁO PHÂN TÍCH & PHẢN BIỆN CỦA CHUYÊN GIA THIẾT KẾ HỆ THỐNG

### 1.1. Đánh giá về các Tác nhân (Actors) - Đã đúng và đủ hay chưa?

#### A. Thực trạng trong file Word báo cáo hiện tại:
Trong tài liệu báo cáo `BAI DU AN_UNG DUNG AI_Nhom 03.docx` (Mục 2.2.1), nhóm chỉ liệt kê **3 tác nhân con người**:
1. `Admin` (Quản trị viên): Quản lý toàn bộ hệ thống sân, giá, nhân viên, báo cáo.
2. `Staff` (Nhân viên): Đặt sân, thanh toán, quản lý khách hàng, xem báo cáo cơ bản.
3. `Customer` (Khách hàng): Xem lịch trống và đặt sân (tài liệu ghi "trong tương lai mở rộng, hiện tại chưa cấp tài khoản").

#### B. Phản biện & Đánh giá chuyên sâu của Chuyên gia:
1. **THIẾU CÁC ACTOR HỆ THỐNG NGOẠI VI (Secondary / External System Actors):**
   - Hệ thống có tích hợp AI và cổng thanh toán tự động, do đó **bắt buộc** phải xác định các tác nhân ngoại vi tương tác trao đổi dữ liệu với hệ thống:
     * **`AI Service Engine (Google Gemini API / OpenAI LLM)`**: Tác nhân ngoại vi tiếp nhận prompt ngữ cảnh từ Backend, xử lý phân tích ngôn ngữ tự nhiên và trả về JSON gợi ý sân trống, nội dung thông báo, hoặc tóm tắt báo cáo.
     * **`Payment Gateway / Banking System (VietQR / MoMo / Napas)`**: Tác nhân ngoại vi cung cấp mã thanh toán QR động, xác thực giao dịch chuyển khoản và trả webhook/đối soát nạp tiền ví.
     * **`Notification Service (SMTP Email Server / Zalo OA API)`**: Tác nhân ngoại vi tiếp nhận yêu cầu gửi email hóa đơn và tin nhắn nhắc lịch tự động cho khách hàng.
2. **THIẾU QUAN HỆ KẾ THỪA GIỮA CÁC ACTOR (Generalization):**
   - Cả 3 tác nhân `Admin`, `Staff`, và `Customer` đều có các hành vi dùng chung: *Đăng nhập*, *Đổi mật khẩu*, *Xem danh sách sân*, *Xem bảng giá*.
   - Theo chuẩn thiết kế hướng đối tượng (OOAD), cần định nghĩa một Actor cha trừu tượng là **`User (Người dùng hệ thống)`**. Sau đó `Admin`, `Staff`, và `Customer` kế thừa (`Generalization`) từ `User`. Điều này giúp biểu đồ Use Case gọn gàng, mạch lạc, tránh lặp lại đường nối (associations).
3. **SỰ MÂU THUẪN GIỮA FILE BÁO CÁO VÀ CODEBASE THỰC TẾ:**
   - Trong file Word: Ghi `Customer` chưa có tài khoản, đặt sân qua nhân viên.
   - Trong mã nguồn thực tế (`F:\Du_An_San_The_Thao`): `Customer` đã có tài khoản riêng (`role = CUSTOMER`), có ví điện tử cá nhân (`wallet_balance`), tự nạp tiền qua VietQR, tự tìm kiếm sân với AI, tự đặt sân online, viết đánh giá 5 sao (`Review`) và đăng bài tìm đối giao lưu (`MatchPost`).
   - **Kết luận chuyên gia:** Cần cập nhật `Customer` thành **Primary Actor chính thức** trong Use Case để phản ánh đúng năng lực hệ thống thực tế.

---

### 1.2. Đánh giá về Mối quan hệ (Relationships) trong Hệ thống

#### A. Trong Biểu đồ Use Case:
1. **Mối quan hệ `<<include>>` (Bắt buộc):**
   - *Đặt sân (Booking)* `<<include>>` *Kiểm tra tính khả dụng & Chống trùng lịch (Check Availability)*: Không thể tạo đơn đặt sân nếu chưa qua bước kiểm tra trùng lịch.
   - *Thực hiện các tác vụ quản trị / đặt sân* `<<include>>` *Đăng nhập & Xác thực quyền (Authentication & Authorization)*.
   - *Hủy đặt sân hoàn tiền* `<<include>>` *Cập nhật số dư ví điện tử*.
2. **Mối quan hệ `<<extend>>` (Mở rộng tùy chọn / Có điều kiện):**
   - *Đặt sân* `<--<<extend>>--` *Gợi ý khung giờ bằng AI (AI Slot Suggestion)*: Khi khách hàng phân vân chưa biết chọn giờ nào hoặc giờ mong muốn đã kín, AI sẽ được kích hoạt để đưa ra gợi ý thay thế.
   - *Xác nhận đặt sân* `<--<<extend>>--` *Tự động sinh tin nhắn thông báo AI (AI Notification)*.
   - *Xem thống kê doanh thu* `<--<<extend>>--` *AI Tóm tắt công suất & Đề xuất voucher giờ thấp điểm*.
   - *Thanh toán* `<--<<extend>>--` *Nạp tiền ví tự động qua VietQR*.

#### B. Trong Mô hình Dữ liệu ERD & Class Diagram:
1. **Bất cập của bảng `TimeSlot` trong bản thiết kế Word cũ:**
   - Bản vẽ cũ trong Word thiết kế bảng `TimeSlot` lưu sẵn từng ô giờ cố định theo ngày. Điều này làm phát sinh hàng chục nghìn dòng dữ liệu rỗng và không hỗ trợ khách muốn thuê thời lượng linh hoạt (ví dụ 1.5 tiếng: 17:30 - 19:00).
2. **Chuẩn hóa theo mô hình Codebase thực tế:**
   - Dùng thực thể `Booking` lưu trực tiếp `start_time`, `end_time`, `booking_date` kết hợp truy vấn kiểm tra giao thoa động. CSDL cực kỳ tinh gọn, hiệu năng cao và đáp ứng mọi khung giờ thuê.
3. **Mối quan hệ thực thể chuẩn:**
   - `User` (1) ---- (0..*) `Booking`: Một người dùng có thể đặt nhiều đơn.
   - `Pitch` (1) ---- (0..*) `Booking`: Một sân tiếp nhận nhiều lượt đặt trong các khung giờ khác nhau.
   - `Booking` (1) ---- (1..*) `Payment`: Một đơn đặt sân có thể có nhiều đợt thanh toán (Đặt cọc -> Tất toán).
   - `Pitch` (1) ---- (0..*) `Maintenance`: Một sân có nhiều lịch bảo trì kỹ thuật.
   - `User` (1) ---- (0..*) `WalletTransaction`: Một người dùng có nhiều giao dịch biến động số dư ví.
   - `User` (1) ---- (0..*) `Review` & `MatchPost`: Tương tác cộng đồng thể thao.

---

# PHẦN 2. TỔNG HỢP TOÀN BỘ CÁC SƠ ĐỒ CHƯA VẼ TRONG BÁO CÁO

---

## 2.1. HÌNH 2.1 – SƠ ĐỒ USE CASE TỔNG QUÁT HỆ THỐNG

### Mã Mermaid:
```mermaid
flowchart TB
    %% Actors
    subgraph Human_Actors ["Tác nhân Người dùng"]
        User["fa:fa-user Người dùng (User)"]
        Admin["fa:fa-user-shield Quản trị viên (Admin)"]
        Staff["fa:fa-id-badge Nhân viên (Staff)"]
        Customer["fa:fa-running Khách hàng (Customer)"]
    end

    subgraph External_Actors ["Tác nhân Ngoại vi"]
        AI["fa:fa-robot AI Engine (Google Gemini)"]
        Bank["fa:fa-university Cổng VietQR / Ngân hàng"]
    end

    %% Generalization
    Admin --|> User
    Staff --|> User
    Customer --|> User

    %% Subsystems & Use Cases
    subgraph System_Boundary ["HỆ THỐNG QUẢN LÝ SÂN THỂ THAO CÓ TÍCH HỢP AI"]
        
        subgraph Auth_Subsystem ["Phân hệ Xác thực & Tài khoản"]
            UC_Login(["UC01: Đăng nhập & Xác thực JWT"])
            UC_Profile(["UC02: Quản lý thông tin cá nhân"])
            UC_ManageUser(["UC03: Quản lý tài khoản & Phân quyền"])
        end

        subgraph Pitch_Subsystem ["Phân hệ Quản lý Sân & Bảng giá"]
            UC_Pitch(["UC04: Quản lý thông tin & Trạng thái sân"])
            UC_Price(["UC05: Cấu hình giá (Thường & Cao điểm)"])
            UC_Maint(["UC06: Lập lịch & Quản lý bảo trì sân"])
        end

        subgraph Booking_Subsystem ["Phân hệ Đặt sân & Lịch thi đấu"]
            UC_ViewSlots(["UC07: Tra cứu lịch sân trống"])
            UC_Booking(["UC08: Đặt sân trực tuyến / Tại quầy"])
            UC_Conflict(["UC09: Kiểm tra chống trùng lịch"])
            UC_Cancel(["UC10: Hủy đặt sân & Hoàn tiền ví"])
        end

        subgraph Payment_Subsystem ["Phân hệ Tài chính & Ví điện tử"]
            UC_Pay(["UC11: Thanh toán đơn đặt sân"])
            UC_Deposit(["UC12: Nạp tiền ví qua VietQR tự động"])
            UC_Stats(["UC13: Xem thống kê & Doanh thu"])
        end

        subgraph AI_Subsystem ["Phân hệ Trí Tuệ Nhân Tạo (AI)"]
            UC_AISuggest(["UC14: AI Tư vấn & Gợi ý khung giờ"])
            UC_AINotif(["UC15: AI Tự động sinh tin nhắn thông báo"])
            UC_AIReport(["UC16: AI Tóm tắt công suất & Gợi ý voucher"])
        end

        subgraph Community_Subsystem ["Phân hệ Cộng đồng & Đánh giá"]
            UC_Review(["UC17: Đánh giá sân & Xếp hạng 5 sao"])
            UC_Match(["UC18: Đăng tin tìm đối giao lưu"])
        end
    end

    %% Relationships
    User --> UC_Login
    User --> UC_Profile
    User --> UC_ViewSlots

    Admin --> UC_ManageUser
    Admin --> UC_Pitch
    Admin --> UC_Price
    Admin --> UC_Maint
    Admin --> UC_Stats

    Staff --> UC_Pitch
    Staff --> UC_Maint
    Staff --> UC_Booking
    Staff --> UC_Cancel
    Staff --> UC_Pay

    Customer --> UC_Booking
    Customer --> UC_Cancel
    Customer --> UC_Deposit
    Customer --> UC_Review
    Customer --> UC_Match

    %% Include & Extend
    UC_Booking -.->|"<<include>>"| UC_Conflict
    UC_Booking -.->|"<<include>>"| UC_Pay
    UC_Cancel -.->|"<<include>>"| UC_Deposit

    UC_AISuggest -.->|"<<extend>>"| UC_Booking
    UC_AINotif -.->|"<<extend>>"| UC_Booking
    UC_AIReport -.->|"<<extend>>"| UC_Stats

    %% External Connections
    UC_AISuggest --- AI
    UC_AINotif --- AI
    UC_AIReport --- AI
    UC_Deposit --- Bank
    UC_Pay --- Bank
```

### Mã PlantUML:
```plantuml
@startuml Hinh_2_1_Use_Case_Tong_Quat
skinparam actorStyle awesome
skinparam packageStyle rectangle
skinparam roundcorner 12
skinparam shadowing true

left to right direction

actor "Người dùng (User)" as User
actor "Quản trị viên (Admin)" as Admin
actor "Nhân viên (Staff)" as Staff
actor "Khách hàng (Customer)" as Customer

actor "AI Engine (Google Gemini)" as AI <<External>>
actor "Cổng VietQR / Bank" as Bank <<External>>

Admin -up-|> User
Staff -up-|> User
Customer -up-|> User

rectangle "HỆ THỐNG QUẢN LÝ SÂN THỂ THAO CÓ TÍCH HỢP AI" {
    package "Xác thực & Tài khoản" {
        usecase "UC01: Đăng nhập & Xác thực JWT" as UC01
        usecase "UC02: Quản lý tài khoản & Phân quyền" as UC02
    }

    package "Quản lý Sân & Giá" {
        usecase "UC03: Quản lý thông tin sân" as UC03
        usecase "UC04: Cấu hình giá giờ thường & cao điểm" as UC04
        usecase "UC05: Quản lý lịch bảo trì sân" as UC05
    }

    package "Đặt sân & Nghiệp vụ" {
        usecase "UC06: Tra cứu lịch sân trống" as UC06
        usecase "UC07: Đặt sân (Online / Tại quầy)" as UC07
        usecase "UC08: Kiểm tra chống trùng lịch" as UC08
        usecase "UC09: Đổi lịch / Hủy đặt sân" as UC09
    }

    package "Tài chính & Ví điện tử" {
        usecase "UC10: Thanh toán đơn đặt sân" as UC10
        usecase "UC11: Nạp ví tự động qua VietQR" as UC11
        usecase "UC12: Xem báo cáo thống kê doanh thu" as UC12
    }

    package "Trí Tuệ Nhân Tạo (AI)" {
        usecase "UC13: AI Gợi ý khung giờ trống" as UC13
        usecase "UC14: AI Sinh tin nhắn xác nhận / nhắc lịch" as UC14
        usecase "UC15: AI Tóm tắt công suất & Đề xuất voucher" as UC15
    }

    package "Cộng đồng Thể thao" {
        usecase "UC16: Đánh giá sân & Bình luận" as UC16
        usecase "UC17: Đăng bài tìm đối giao lưu" as UC17
    }
}

User --> UC01
User --> UC06

Admin --> UC02
Admin --> UC03
Admin --> UC04
Admin --> UC05
Admin --> UC12

Staff --> UC03
Staff --> UC05
Staff --> UC07
Staff --> UC09
Staff --> UC10

Customer --> UC07
Customer --> UC09
Customer --> UC11
Customer --> UC16
Customer --> UC17

UC07 ..> UC08 : <<include>>
UC07 ..> UC10 : <<include>>

UC13 ..> UC07 : <<extend>>
UC14 ..> UC07 : <<extend>>
UC15 ..> UC12 : <<extend>>

UC13 -- AI
UC14 -- AI
UC15 -- AI
UC11 -- Bank
UC10 -- Bank
@enduml
```

---

## 2.2. HÌNH 2.2 – SƠ ĐỒ THỰC THỂ QUAN HỆ (ERD) & BIỂU ĐỒ LỚP (CLASS DIAGRAM)

### Mã Mermaid:
```mermaid
classDiagram
    direction TB
    
    class User {
        +int id PK
        +string username UK
        +string email UK
        +string hashed_password
        +string full_name
        +string phone
        +UserRole role
        +float wallet_balance
        +boolean is_active
        +datetime last_login_at
        +datetime created_at
        +register()
        +login()
        +update_balance()
    }

    class Pitch {
        +int id PK
        +string name
        +PitchType sport_type
        +string location
        +float price_per_hour
        +float peak_price_per_hour
        +PitchStatus status
        +string description
        +string image_url
        +datetime created_at
        +check_availability()
    }

    class Booking {
        +int id PK
        +int user_id FK
        +int pitch_id FK
        +string customer_name
        +string customer_phone
        +string booking_date
        +string start_time
        +string end_time
        +float total_price
        +float deposit_amount
        +PaymentMethod payment_method
        +PaymentStatus payment_status
        +BookingStatus status
        +string note
        +boolean invoice_sent
        +datetime created_at
        +calculate_total()
        +cancel_booking()
    }

    class Payment {
        +int id PK
        +int booking_id FK
        +float amount
        +PaymentType payment_type
        +PaymentMethod payment_method
        +PaymentStatus status
        +string transaction_ref
        +string bank_name
        +datetime created_at
        +process_payment()
    }

    class WalletTransaction {
        +int id PK
        +int user_id FK
        +float amount
        +WalletTransactionType transaction_type
        +string payment_method
        +PaymentStatus status
        +string description
        +string transaction_code
        +datetime created_at
        +verify_deposit()
    }

    class Maintenance {
        +int id PK
        +int pitch_id FK
        +string start_date
        +string end_date
        +string reason
        +float cost
        +MaintenanceStatus status
        +datetime created_at
    }

    class Review {
        +int id PK
        +int user_id FK
        +int pitch_id FK
        +string customer_name
        +int rating
        +string comment
        +datetime created_at
    }

    class MatchPost {
        +int id PK
        +int user_id FK
        +string author_name
        +PitchType sport_type
        +string team_level
        +string match_time
        +string contact_phone
        +string content
        +datetime created_at
    }

    class UserActivityLog {
        +int id PK
        +int user_id FK
        +string username
        +string action
        +string role
        +string ip_address
        +datetime timestamp
    }

    User "1" --> "0..*" Booking : places
    User "1" --> "0..*" WalletTransaction : owns
    User "1" --> "0..*" Review : writes
    User "1" --> "0..*" MatchPost : publishes
    User "1" --> "0..*" UserActivityLog : generates

    Pitch "1" --> "0..*" Booking : contains
    Pitch "1" --> "0..*" Maintenance : undergoes
    Pitch "1" --> "0..*" Review : receives

    Booking "1" --> "0..*" Payment : billed_in
```

### Mã PlantUML:
```plantuml
@startuml Hinh_2_2_ERD_Class_Diagram
skinparam classAttributeIconSize 0
skinparam classFontStyle bold
skinparam roundcorner 8

enum UserRole {
    ADMIN
    STAFF
    CUSTOMER
}

enum PitchType {
    FOOTBALL
    BADMINTON
    TENNIS
    GYM
    BASKETBALL
}

enum PitchStatus {
    AVAILABLE
    MAINTENANCE
    INACTIVE
}

enum BookingStatus {
    PENDING
    CONFIRMED
    COMPLETED
    CANCELLED
}

enum PaymentStatus {
    PENDING
    PAID
    REFUNDED
}

class User {
    + id: Integer {PK}
    + username: String(50) {UQ}
    + email: String(100) {UQ}
    + hashed_password: String(255)
    + full_name: String(100)
    + phone: String(20)
    + role: UserRole = CUSTOMER
    + wallet_balance: Float = 0.0
    + is_active: Boolean = true
    + created_at: DateTime
}

class Pitch {
    + id: Integer {PK}
    + name: String(100)
    + sport_type: PitchType
    + location: String(255)
    + price_per_hour: Float
    + peak_price_per_hour: Float
    + status: PitchStatus = AVAILABLE
    + description: Text
    + image_url: String(255)
}

class Booking {
    + id: Integer {PK}
    + user_id: Integer {FK}
    + pitch_id: Integer {FK}
    + customer_name: String(100)
    + customer_phone: String(20)
    + booking_date: String(10)
    + start_time: String(5)
    + end_time: String(5)
    + total_price: Float
    + deposit_amount: Float
    + payment_method: String
    + payment_status: PaymentStatus
    + status: BookingStatus
    + invoice_sent: Boolean = false
    + created_at: DateTime
}

class Payment {
    + id: Integer {PK}
    + booking_id: Integer {FK}
    + amount: Float
    + payment_type: String
    + payment_method: String
    + status: PaymentStatus
    + transaction_ref: String(100)
    + created_at: DateTime
}

class WalletTransaction {
    + id: Integer {PK}
    + user_id: Integer {FK}
    + amount: Float
    + transaction_type: String
    + payment_method: String
    + status: PaymentStatus
    + transaction_code: String(100)
    + created_at: DateTime
}

class Maintenance {
    + id: Integer {PK}
    + pitch_id: Integer {FK}
    + start_date: String(10)
    + end_date: String(10)
    + reason: String(255)
    + cost: Float
    + status: String
}

class Review {
    + id: Integer {PK}
    + user_id: Integer {FK}
    + pitch_id: Integer {FK}
    + customer_name: String(100)
    + rating: Integer (1-5)
    + comment: Text
    + created_at: DateTime
}

class MatchPost {
    + id: Integer {PK}
    + user_id: Integer {FK}
    + author_name: String(100)
    + sport_type: PitchType
    + team_level: String(50)
    + match_time: String(100)
    + contact_phone: String(20)
    + content: Text
}

User "1" *-- "0..*" Booking : creates >
User "1" *-- "0..*" WalletTransaction : owns >
User "1" *-- "0..*" Review : writes >
User "1" *-- "0..*" MatchPost : posts >

Pitch "1" *-- "0..*" Booking : is_booked_in >
Pitch "1" *-- "0..*" Maintenance : has >
Pitch "1" *-- "0..*" Review : receives >

Booking "1" *-- "0..*" Payment : contains >
@enduml
```

---

## 2.3. HÌNH 2.3 – SƠ ĐỒ KIẾN TRÚC HỆ THỐNG TỔNG THỂ (SYSTEM ARCHITECTURE)

### Mã Mermaid:
```mermaid
graph TB
    subgraph Client_Layer ["1. TẦNG GIAO DIỆN NGƯỜI DÙNG (PRESENTATION LAYER)"]
        SPA["Single Page Application (SPA)
HTML5 / Tailwind CSS / Vanilla JS"]
        UI_Admin["Admin & Staff Dashboard
(Quản lý sân, Lịch, Doanh thu)"]
        UI_Customer["Customer Booking Portal
(Đặt sân trực tuyến, Nạp ví)"]
        UI_AI["AI Smart Chat & Assistant
(Tư vấn, Gợi ý, Báo cáo)"]
        SPA --- UI_Admin
        SPA --- UI_Customer
        SPA --- UI_AI
    end

    subgraph Gateway_Layer ["2. TẦNG XÁC THỰC & BẢO MẬT (API GATEWAY & SECURITY)"]
        API_GW["FastAPI Core Engine (Port 8000)"]
        CORS["CORS & Middleware"]
        JWT_Auth["JWT Token Bearer Authentication"]
        RBAC["Role-Based Access Control (Admin / Staff / Customer)"]
        API_GW --> CORS --> JWT_Auth --> RBAC
    end

    subgraph Service_Layer ["3. TẦNG DỊCH VỤ & NGHIỆP VỤ (BUSINESS LOGIC LAYER)"]
        Router_Auth["Auth Router (/api/auth)"]
        Router_Pitch["Pitch Router (/api/pitches)"]
        Router_Booking["Booking Router (/api/bookings)
- Conflict Detection Engine"]
        Router_Wallet["Wallet Router (/api/wallet)
- VietQR Auto Payment"]
        Router_AI["AI Router (/api/ai)
- Slot Suggestion & Promo"]
        Router_Stats["Stats Router (/api/stats)
- Chart.js Aggregations"]
    end

    subgraph AI_Layer ["4. TẦNG TÍCH HỢP TRÍ TUỆ NHÂN TẠO (AI SERVICE LAYER)"]
        AI_Service["AI Service Module
(app/services/ai_service.py)"]
        Prompt_Mgr["Prompt Engineering Manager
(app/prompts/)"]
        Fallback_Engine["Heuristic Rule Engine
(Cơ chế dự phòng khi Offline / Lỗi Quota)"]
        AI_Service --> Prompt_Mgr
        AI_Service --> Fallback_Engine
    end

    subgraph Persistence_Layer ["5. TẦNG LƯU TRỮ DỮ LIỆU (DATA PERSISTENCE LAYER)"]
        ORM["SQLAlchemy ORM 2.0"]
        DB[(Cơ sở dữ liệu Quan hệ
SQLite / PostgreSQL)]
        ORM --> DB
    end

    subgraph External_Services ["6. HỆ THỐNG NGOẠI VI BÊN THỨ 3"]
        Ext_Gemini["Google Gemini 1.5 Flash API
(LLM Engine)"]
        Ext_VietQR["VietQR Banking API
(Cổng nạp tiền động)"]
        Ext_SMTP["SMTP Mail Server
(Gửi hóa đơn tự động)"]
    end

    Client_Layer ==>|HTTP / RESTful API JSON| Gateway_Layer
    Gateway_Layer ==> Service_Layer
    Router_Booking --> ORM
    Router_Pitch --> ORM
    Router_Wallet --> ORM
    Router_Auth --> ORM
    Router_Stats --> ORM
    Router_AI --> AI_Service
    AI_Service --> ORM

    AI_Service <==>|Google GenAI SDK| Ext_Gemini
    Router_Wallet <==>|Payload QR Code| Ext_VietQR
    Router_Booking <==>|Email Invoices| Ext_SMTP
```

---

## 2.4. HÌNH 2.4 – SƠ ĐỒ LUỒNG XỬ LÝ CHỨC NĂNG AI GỢI Ý KHUNG GIỜ (ACTIVITY DIAGRAM)

### Mã Mermaid:
```mermaid
flowchart TD
    Start([Bắt đầu: Khách hàng / Nhân viên mở AI Assistant]) --> InputData[Nhập loại sân, ngày cần đặt và khung giờ mong muốn]
    InputData --> FetchDB[Backend truy vấn CSDL: Lấy danh sách khung giờ còn trống trong ngày]
    
    FetchDB --> CheckSlots{Có khung giờ trống nào không?}
    CheckSlots -- Không --> OutOfSlots[AI thông báo: Tất cả sân đã kín trong ngày đã chọn]
    OutOfSlots --> EndNode([Kết thúc])
    
    CheckSlots -- Có --> BuildPrompt[Xây dựng System Prompt & nạp dữ liệu slot thực tế vào User Prompt]
    BuildPrompt --> CallGemini[Gửi Request đến Google Gemini 1.5 Flash API]
    
    CallGemini --> CheckAPI{Gọi Gemini API thành công?}
    
    CheckAPI -- Không (Timeout / Hết Quota) --> TriggerFallback[Kích hoạt Heuristic Fallback Engine nội bộ]
    TriggerFallback --> GenLocal[Sinh gợi ý dựa trên thuật toán so khớp khoảng cách giờ gần nhất]
    
    CheckAPI -- Có --> ParseResponse[Nhận phản hồi từ Gemini và Parse cấu trúc JSON]
    
    GenLocal --> MergeResult[Đóng gói 3-5 gợi ý tối ưu kèm lý do giải thích]
    ParseResponse --> MergeResult
    
    MergeResult --> RenderUI[Hiển thị danh sách Card gợi ý trên Dashboard]
    RenderUI --> UserSelect[Người dùng bấm 'Đặt nhanh khung giờ này']
    UserSelect --> AutoFill[Hệ thống tự động điền form và chuyển sang xác nhận đặt sân]
    AutoFill --> EndNode
```

---

## 2.5. CÁC SƠ ĐỒ TUẦN TỰ TRỌNG TÂM (SEQUENCE DIAGRAMS)

### SD01: Sơ đồ Tuần tự Đăng nhập & Xác thực JWT
```mermaid
sequenceDiagram
    autonumber
    actor Actor as Người dùng (Admin / Staff / Customer)
    participant UI as Giao diện Frontend (SPA)
    participant AuthRouter as AuthRouter (/api/auth/login)
    participant DB as CSDL (users table)

    Actor->>UI: Nhập Username và Password
    UI->>AuthRouter: POST /api/auth/login {username, password}
    AuthRouter->>DB: Query User where username = :username and is_active = True
    DB-->>AuthRouter: Trả về User record (kèm hashed_password)
    
    alt Không tìm thấy User hoặc sai Mật khẩu
        AuthRouter-->>UI: 401 Unauthorized ("Sai thông tin đăng nhập")
        UI-->>Actor: Hiển thị thông báo lỗi
    else Xác thực bcrypt thành công
        AuthRouter->>AuthRouter: Tạo JWT Token (chứa user_id, username, role, exp)
        AuthRouter->>DB: Cập nhật last_login_at
        AuthRouter-->>UI: 200 OK {access_token, role, full_name, wallet_balance}
        UI->>UI: Lưu Token & User info vào LocalStorage
        UI->>UI: Chuyển hướng Dashboard theo Role (Admin / Staff / Customer)
        UI-->>Actor: Hiển thị giao diện làm việc
    end
```

---

### SD02: Sơ đồ Tuần tự Đặt sân & Thuật toán Chống trùng lịch (Double-Booking Prevention)
```mermaid
sequenceDiagram
    autonumber
    actor Customer as Khách hàng / Nhân viên
    participant UI as Giao diện Đặt sân (SPA)
    participant BookingRouter as BookingRouter (/api/bookings)
    participant DB as CSDL (bookings table)
    participant WalletRouter as Wallet / Payment Service

    Customer->>UI: Chọn Sân, Ngày, Giờ bắt đầu (S), Giờ kết thúc (E)
    UI->>BookingRouter: POST /api/bookings {pitch_id, date, S, E, payment_method}
    
    BookingRouter->>DB: Query kiểm tra trùng lịch:
(booking_date == date) AND (pitch_id == id) AND
(status != 'CANCELLED') AND (S < end_time) AND (E > start_time)
    DB-->>BookingRouter: Trả về danh sách đơn trùng (nếu có)
    
    alt Phát hiện trùng lịch (Overlap > 0)
        BookingRouter-->>UI: 409 Conflict ("Khung giờ đã có người đặt hoặc đang bảo trì")
        UI-->>Customer: Báo lỗi và gợi ý khung giờ khác
    else Khung giờ hợp lệ (Không trùng)
        BookingRouter->>BookingRouter: Tính toán tổng tiền (nhân hệ số cao điểm nếu sau 17h00)
        
        alt Thanh toán bằng Ví điện tử
            BookingRouter->>WalletRouter: Kiểm tra & Khấu trừ số dư ví
            WalletRouter-->>BookingRouter: Khấu trừ thành công
        end
        
        BookingRouter->>DB: INSERT INTO bookings (status='CONFIRMED', payment_status='PAID')
        DB-->>BookingRouter: Trả về booking_id mới
        BookingRouter-->>UI: 201 Created {booking_id, status: 'CONFIRMED'}
        UI-->>Customer: Hiển thị thông báo đặt sân thành công & mã đơn
    end
```

---

### SD03: Sơ đồ Tuần tự AI Tư vấn & Gợi ý Sân thông minh
```mermaid
sequenceDiagram
    autonumber
    actor User as Khách hàng / Nhân viên
    participant UI as AI Chat UI
    participant AIRouter as AIRouter (/api/ai/suggest-slots)
    participant DB as CSDL (pitches, bookings)
    participant AIService as AIService (ai_service.py)
    participant Gemini as Google Gemini 1.5 Flash API

    User->>UI: Gửi câu hỏi: "Tư vấn sân bóng 7 người tối nay từ 18h-20h"
    UI->>AIRouter: POST /api/ai/suggest-slots {user_query, sport_type: 'FOOTBALL'}
    AIRouter->>DB: Lấy danh sách sân trống thực tế trong ngày từ CSDL
    DB-->>AIRouter: Trả về danh sách available_slots
    
    AIRouter->>AIService: generate_slot_suggestion(user_query, available_slots)
    AIService->>AIService: Nạp System Prompt + Dữ liệu CSDL vào context
    
    alt Gọi Gemini API bình thường
        AIService->>Gemini: POST generateContent(prompt)
        Gemini-->>AIService: Trả về phản hồi dạng JSON danh sách sân
    else Mất mạng / Lỗi hạn mức API
        AIService->>AIService: Kích hoạt Heuristic Fallback Engine
        AIService->>AIService: Lọc slot có khoảng cách gần 18h-20h nhất từ CSDL
    end
    
    AIService-->>AIRouter: Trả về Structure Response (List Suggestions + Reason)
    AIRouter-->>UI: 200 OK {suggestions: [...], message: "..."}
    UI-->>User: Hiển thị các Card sân trống kèm nút "Đặt ngay"
```

---

### SD04: Sơ đồ Tuần tự Nạp tiền Ví điện tử tự động qua VietQR
```mermaid
sequenceDiagram
    autonumber
    actor Customer as Khách hàng
    participant UI as Giao diện Ví tiền (SPA)
    participant WalletRouter as WalletRouter (/api/wallet/deposit-qr)
    participant DB as CSDL (wallet_transactions, users)
    participant Bank as Cổng VietQR / Ngân hàng

    Customer->>UI: Nhập số tiền muốn nạp (ví dụ: 200,000đ)
    UI->>WalletRouter: POST /api/wallet/deposit-qr {amount: 200000}
    WalletRouter->>WalletRouter: Tạo mã giao dịch duy nhất (VD: NAP200K_U1_98234)
    WalletRouter->>DB: INSERT INTO wallet_transactions (amount=200000, status='PENDING')
    WalletRouter->>WalletRouter: Sinh link ảnh VietQR động kèm nội dung chuyển khoản
    WalletRouter-->>UI: 200 OK {qr_url, transaction_code, amount}
    
    UI-->>Customer: Hiển thị Modal mã QR và hướng dẫn chuyển khoản
    Customer->>Bank: Quét mã QR và chuyển khoản qua App Ngân hàng
    
    Customer->>UI: Bấm "Tôi đã chuyển khoản thành công"
    UI->>WalletRouter: POST /api/wallet/confirm-deposit {transaction_code}
    WalletRouter->>DB: UPDATE wallet_transactions SET status = 'PAID'
    WalletRouter->>DB: UPDATE users SET wallet_balance = wallet_balance + 200000
    DB-->>WalletRouter: Cập nhật thành công
    WalletRouter-->>UI: 200 OK {new_balance: 200000, status: 'SUCCESS'}
    UI-->>Customer: Hiển thị thông báo nạp ví thành công & cập nhật số dư tức thì
```

---

# PHẦN 3. HƯỚNG DẪN MỞ & XUẤT ẢNH TRÊN STARUML

1. **Bước 1:** Khởi động phần mềm **StarUML** trên máy tính.
2. **Bước 2:** Chọn menu **File** -> **Open...** -> Trỏ đến tệp tin: `F:\Du_An_San_The_Thao_StarUML.mdj`.
3. **Bước 3:** Ở khung **Model Explorer** (bên phải màn hình), bạn sẽ thấy 2 thư mục mô hình chính:
   - `1. Use Case Model (Hinh 2.1)` -> Nháy đúp vào `Hinh 2.1 - So do Use Case Tong Quat He Thong` để xem và chỉnh sửa giao diện.
   - `2. Class Diagram & ERD (Hinh 2.2)` -> Nháy đúp vào `Hinh 2.2 - So do ERD & Class Model CSDL` để xem toàn bộ cấu trúc bảng và kiểu dữ liệu.
4. **Bước 4:** Để xuất ảnh chèn vào Word:
   - Chọn menu **File** -> **Export Diagram As** -> Chọn định dạng **PNG...** hoặc **JPEG...**.
   - Lưu ảnh với độ phân giải cao và dán vào đúng vị trí các hình trong file Word báo cáo!
