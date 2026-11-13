# Báo cáo cá nhân — Day 6: Data Ingestion Engineering

- **Họ và tên**: Nguyễn Quang Vũ
- **MSSV**: 2A202603407
- **Lớp**: L3A
- **Chủ đề**: Toàn cảnh công nghệ AI phục vụ lĩnh vực chăm sóc sức khỏe
- **Corpus**: `2023-BC-toan-canh-cong-nghe-AI-cham-soc-suc-khoe.pdf` (Sở Khoa học và Công nghệ TP.HCM - CESTI)

---

## 1. Dữ liệu và pipeline

### Chủ đề, nguồn/quyền, số trang và quy tắc tính trang
- **Chủ đề**: Báo cáo phân tích toàn cảnh công nghệ trí tuệ nhân tạo (AI) trong chăm sóc sức khỏe, xu hướng nghiên cứu và bảo hộ sáng chế trên thế giới, cùng các giải pháp công nghệ sẵn sàng chuyển giao tại Việt Nam.
- **Nguồn và bản quyền**: Báo cáo chuyên đề do Trung tâm Thông tin và Thống kê Khoa học và Công nghệ (CESTI) thuộc Sở Khoa học và Công nghệ TP.HCM xuất bản (tháng 10/2022). Tài liệu phát hành công khai phục vụ nghiên cứu, đào tạo và phổ biến tri thức khoa học phi thương mại.
- **Số trang và quy tắc tính**:
  - File PDF gốc có **58 trang vật lý**.
  - Quy tắc loại trừ: Loại trừ Trang 1 (Trang bìa) và Trang 2 (Mục lục) vì không chứa nội dung tri thức chuyên đề hữu ích, tránh gây nhiễu từ vựng trong vector store.
  - Số trang nội dung được nạp: **56 trang** (từ trang 3 đến trang 58), bao gồm: Phần mở đầu (trang 3-4), Phần 1 Thế giới (trang 5-25), Phần 2 Việt Nam (trang 26-45), Phần 3 Kết luận & Khuyến nghị (trang 46-50), và Phần Phụ lục (trang 51-58).
  - Tổng số ký tự sau chuẩn hóa: **98.305 ký tự**. Đạt và vượt xa yêu cầu tối thiểu 30 trang nội dung hữu ích theo quy định đề bài.
  - Chi tiết manifest được lưu tại [data/manifest.json](../../data/manifest.json).

### Chuẩn hóa, lỗi và giới hạn
- **Quy trình chuẩn hóa văn bản**:
  - Chuẩn hóa Unicode `NFKC` bằng thư viện `unicodedata`: đảm bảo tất cả các ký tự tiếng Việt có dấu (dù lưu dưới dạng tổ hợp hay dựng sẵn trong PDF) đều được quy về một dạng chuẩn duy nhất.
  - Loại bỏ các ký tự điều khiển ẩn lạ (`control characters`), chuẩn hóa khoảng trắng thừa và ký tự tab thành khoảng trắng đơn.
  - Chuẩn hóa ngắt dòng: bảo toàn cấu trúc phân đoạn tự nhiên (`\n\n`) để phục vụ chiến lược chunking theo đoạn văn.
- **Lỗi và giới hạn gặp phải**:
  - File PDF xuất hiện hiện tượng tách ký tự/khoảng trắng cục bộ trong một số từ tiếng Việt do font encoding/kerning khi trích xuất (ví dụ: `y t ế`, `ch ẩn đoán`, `bi ến chứng`). Pipeline đã xử lý chuẩn hóa để đảm bảo việc trích xuất và so khớp bằng chứng không bị sai lệch.
  - Trang 51 là trang tiêu đề phân cách phần phụ lục có dung lượng văn bản ngắn (47 ký tự), được ghi nhận cụ thể trong `manifest.json`.

### Embedding model, Vector store, Lệnh chạy và Chi phí
- **Embedding model**:
  - Tên mô hình: `gemini-embedding-001` (Google Gemini API).
  - Số chiều biểu diễn: **768 chiều** (sử dụng kỹ thuật Matryoshka dimensionality reduction qua tham số `outputDimensionality=768`).
  - Phân loại tác vụ (`taskType`): Áp dụng `RETRIEVAL_DOCUMENT` khi nhúng văn bản tài liệu/chunk và `RETRIEVAL_QUERY` khi nhúng câu hỏi tìm kiếm.
  - Tuyệt đối không sử dụng vector mock/ngẫu nhiên.
- **Vector store**:
  - Hệ thống: `Qdrant` phiên bản 1.20.0 (`qdrant-client`), chế độ **Local Persistent Storage** lưu trữ bền vững trên đĩa cứng tại thư mục `./results/qdrant_data`.
  - Không phụ thuộc vào Docker, tương thích hoàn toàn trên môi trường Windows.
  - Độ đo khoảng cách: **Cosine similarity** (`Distance.COSINE`).
  - Đảm bảo tính lũy đẳng (`idempotent`): Định danh điểm dữ liệu (`PointStruct.id`) được sinh bằng hàm băm xác định `uuid.uuid5` từ `chunk_id`, ngăn chặn hoàn toàn việc nhân đôi bản ghi khi chạy lại pipeline.

### Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn
- **Metadata bắt buộc**: `document_id` (`cesti-2023-ai-healthcare`), `source` (`2023-BC-toan-canh-cong-nghe-AI-cham-soc-suc-khoe.pdf`), `page` (số trang vật lý tương ứng từ 3 đến 58).
- **Trường lọc bổ sung (`section`)**:
  - Gồm 5 giá trị phạm vi có cấu trúc rõ ràng:
    + `mo_dau`: Trang 3 - 4 (Tổng quan khái niệm và bối cảnh).
    + `phan_1_the_gioi`: Trang 5 - 25 (Xu hướng công nghệ, bằng sáng chế và tổ chức hàng đầu thế giới).
    + `phan_2_viet_nam`: Trang 26 - 45 (Sáng chế bảo hộ và giải pháp y tế chuyển giao tại Việt Nam).
    + `phan_3_ket_luan`: Trang 46 - 50 (Nhận định, kết luận và khuyến nghị chính sách).
    + `phu_luc`: Trang 51 - 58 (Danh mục và thống kê chi tiết).
  - **Nguồn giá trị**: Trích xuất tự động và tin cậy tuyệt đối từ cấu trúc mục lục thực tế của tài liệu.
  - **Lý do chọn**: Giúp AI agent thu hẹp không gian tìm kiếm khi người dùng hỏi các câu hỏi có phạm vi cụ thể (ví dụ: chỉ hỏi về giải pháp tại Việt Nam hoặc chỉ hỏi về tình hình sáng chế thế giới), loại bỏ nhiễu từ các phần khác.

---

## 2. Cấu hình và benchmark

### Mô tả 3 chiến lược A / B / C
- **Strategy A (Fixed-size Window)**:
  - Chia chunk theo kích thước cố định: `size = 500` ký tự, độ gối `overlap = 50` ký tự.
  - Tổng số chunk sinh ra: **244 chunks**. Độ dài trung bình: 441.1 ký tự.
  - Truy xuất: Tìm kiếm tương đồng Cosine thuần túy, không áp dụng lọc metadata.
- **Strategy B (Paragraph-aware Chunking)**:
  - Chia chunk dựa theo ranh giới đoạn văn tự nhiên (`\n\n`), kết hợp gom các đoạn ngắn liền kề và phân rã các đoạn quá khổ với giới hạn trên `max_size = 800` ký tự.
  - Tổng số chunk sinh ra: **210 chunks**. Độ dài trung bình: 467.1 ký tự.
  - Truy xuất: Tìm kiếm tương đồng Cosine thuần túy, không áp dụng lọc metadata.
  - *Khác biệt kiểm soát A–B*: Giữ nguyên embedding model, vector store và bộ câu hỏi; chỉ thay đổi phương pháp chia chunk (cố định vs theo đoạn văn).
- **Strategy C (Paragraph-aware + Metadata Filter)**:
  - Sử dụng chung tập chunk và vector lưu trữ với Strategy B (**210 chunks**).
  - Truy xuất: Tự động kích hoạt bộ lọc siêu dữ liệu (`filters={"section": ...}`) khi câu hỏi có yêu cầu phạm vi xác định trước; giữ tìm kiếm không lọc đối với câu hỏi thông thường.
  - *Khác biệt kiểm soát B–C*: Giữ nguyên hoàn toàn dữ liệu chunk và biểu diễn vector; chỉ thay đổi duy nhất việc bật/tắt bộ lọc metadata.

### Bộ câu hỏi Benchmark (≥20 câu, phân chia Dev/Test)
- Bộ câu hỏi gồm **20 câu** hoàn chỉnh tại [benchmark/questions.json](../../benchmark/questions.json):
  - **15 câu Dev (`q01` đến `q15`)**: Dùng để phân tích hành vi và tinh chỉnh lựa chọn chiến lược.
  - **5 câu Test (`q16` đến `q20`)**: Tập kiểm thử độc lập, được cố định tuyệt đối trước khi chạy thực nghiệm.
- **Phân bổ đa dạng các dạng câu hỏi**:
  - 11 câu hỏi trực tiếp (`direct`): Tra cứu sự kiện, tên công nghệ, mã số sáng chế quốc tế (US10963795B2, KR10-2020-0066484A, IN20221104896).
  - 3 câu diễn đạt lại (`paraphrase`): Kiểm tra khả năng truy xuất ngữ nghĩa khi câu từ không trùng lặp máy móc.
  - 3 câu điều kiện / ngoại lệ / hạn chế (`conditional_exception`): Đòi hỏi nắm bắt đúng điều kiện tiên quyết (CT scan, ngôn ngữ tự nhiên chưa chuẩn hóa trong bệnh án điện tử, cỡ mẫu ung thư gan).
  - 3 câu kiểm tra bộ lọc metadata (`metadata_filter`): Gồm 2 câu dev (`q09`, `q10`) và 1 câu test (`q17`).
- **Kiểm chứng bằng chứng (`evidence_quote`)**:
  - 100% (20/20 câu) đều có đoạn trích bằng chứng là chuỗi con nguyên bản khớp tuyệt đối trong trang nguồn đã chuẩn hóa (`gold_page`).

### Tiêu chí chọn chiến lược chốt trước khi xem Test
1. **Tiêu chí 1 (Ưu tiên cao nhất)**: Độ chính xác truy xuất bằng chứng trên tập Dev (`Evidence Hit@3` 85% và `Hit@1` 70\%).
2. **Tiêu chí 2**: Tính mạch lạc của chunk (`Chunk Coherence` 1.5/2.0), giảm thiểu tối đa hiện tượng ngắt câu giữa ý.
3. **Tiêu chí 3**: Chất lượng thông tin nền (`Grounding Quality` 1.6/2.0), đảm bảo chunk cung cấp đủ ngữ cảnh để LLM trả lời mà không bị ảo giác.
4. **Tiêu chí 4**: Hiệu quả tài nguyên (số lượng chunk tối ưu, thời gian ingest nhanh, chi phí thấp).

---

## 3. Kết quả thực nghiệm

### Bảng 1: Hiệu năng truy xuất và Tài nguyên
| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian Ingest | Chi phí API |
|---|---|---|---|---|---|---|
| **Strategy A** (Fixed 500/50) | dev | 12/15 (80.0%) | 14/15 (93.3%) | 244 | 204.14s | $0.0 |
| **Strategy A** (Fixed 500/50) | test | 2/5 (40.0%) | 2/5 (40.0%) | 244 | - | $0.0 |
| **Strategy B** (Paragraph 800) | dev | 13/15 (86.7%) | 14/15 (93.3%) | 210 | 176.69s | $0.0 |
| **Strategy B** (Paragraph 800) | test | 1/5 (20.0%) | 4/5 (80.0%) | 210 | - | $0.0 |
| **Strategy C** (B + Filter) | dev | 13/15 (86.7%) | 14/15 (93.3%) | 210 | 176.69s (dùng chung index) | $0.0 |
| **Strategy C** (B + Filter) | test | 2/5 (40.0%) | 4/5 (80.0%) | 210 | - | $0.0 |

### Bảng 2: Đánh giá chất lượng và Độ tin cậy (Audit thủ công)
| Strategy | Coherence trung bình /2 (10 mẫu) | Metadata đủ và đúng (15 mẫu test) | Filter tuân thủ (1 câu test filter) | Grounding 0/1/2 (số câu) và trung bình /2 |
|---|---|---|---|---|
| **Strategy A** | 1.00 / 2.0 | 15/15 (100.0%) | N/A | [0: 2, 1: 1, 2: 2] -> 1.00 / 2.0 |
| **Strategy B** | 2.00 / 2.0 | 15/15 (100.0%) | N/A | [0: 1, 1: 0, 2: 4] -> 1.60 / 2.0 |
| **Strategy C** | 2.00 / 2.0 | 15/15 (100.0%) | 1/1 (100.0%) | [0: 1, 1: 0, 2: 4] -> 1.60 / 2.0 |

- **Đường dẫn artifacts**:
  - Dữ liệu trace chi tiết: [results/traces.json](../../results/traces.json)
  - Tóm tắt số liệu tự động: [results/summary.json](../../results/summary.json)
  - Nhật ký thí nghiệm đối sánh: [artifacts/experiment_log.csv](../../artifacts/experiment_log.csv)
  - Dữ liệu audit tổng hợp: [results/audit_metrics.json](../../results/audit_metrics.json)
- **Phương pháp chọn mẫu audit**:
  - *Coherence*: Cố định 10 vị trí nội dung trải dài theo các trang nội dung chính (Trang 3, 5, 7, 8, 10, 11, 13, 14, 22, 24).
  - *Metadata & Grounding*: Kiểm tra toàn bộ 5 câu test Top-3 hits = 15 bản ghi cho mỗi chiến lược.

---

## 4. Phân tích và kết luận

### So sánh có kiểm soát A–B và B–C
1. **So sánh A–B (Fixed-size vs Paragraph-aware)**:
   - **Độ chính xác truy xuất**: Trên tập Test độc lập, `Evidence Hit@3` của Strategy B đạt **80.0% (4/5)**, vượt trội hoàn toàn so với **40.0% (2/5)** của Strategy A.
   - **Tính mạch lạc (Chunk Coherence)**: Strategy B đạt điểm tuyệt đối **2.00/2.0**, trong khi Strategy A chỉ đạt **1.00/2.0**. Nguyên nhân do Strategy A cắt cứng ở ký tự thứ 500, dẫn đến 10/10 vị trí kiểm tra đều bị đứt gãy câu giữa chừng (thiếu vị ngữ hoặc mất chủ thể ngữ pháp), làm embedding model không thể nắm bắt trọn vẹn ngữ cảnh ngữ nghĩa.
   - **Hiệu quả tài nguyên**: Strategy B giảm số lượng chunk từ 244 xuống 210 chunk (giảm 14%), giúp rút ngắn thời gian nhúng vector từ 204.14s xuống 176.69s.
2. **So sánh B–C (Ảnh hưởng của Metadata Filtering)**:
   - Trên câu hỏi có điều kiện lọc phạm vi (`q17` thuộc tập Test, hỏi về ứng dụng di động tại Việt Nam):
     - Ở Strategy B (không lọc), hệ thống bị nhiễu bởi các đoạn văn về ứng dụng di động theo dõi sức khỏe ở thị trường quốc tế (Mỹ, Ấn Độ ở Phần 1), khiến Hit@1 bị trượt.
     - Ở Strategy C (có lọc `section="phan_2_viet_nam"`), hệ thống loại bỏ 100% các ứng viên ngoài phạm vi, đưa đúng chunk về `1SK Health Tracker` lên vị trí Rank 1.
     - Nhờ đó, Hit@1 trên tập Test của Strategy C tăng gấp đôi từ 20.0% (1/5) lên 40.0% (2/5), trong khi giữ vững Hit@3 ở mức 80.0%.

### Phân tích 2 ví dụ sai lệch cụ thể
1. **Ví dụ lỗi 1 — Strategy A (Câu `q15` tập Dev)**:
   - *Câu hỏi*: "Website nào được nhóm nghiên cứu giới thiệu nhằm ứng dụng AI trong hỗ trợ phát hiện viêm ruột thừa biến chứng?"
   - *Gold Page*: Trang 43 | *Bằng chứng*: `https://viemruotthua.com/`
   - *Kết quả*: Top-1 trả về đúng trang 43 (`score = 0.8710`), nhưng bị đánh dấu là False vì chunk bị ngắt ở ký tự 500: phần đầu chunk nói về mô hình XGBoost, trong khi đường dẫn link website nằm ở đoạn văn cuối trang bị đẩy sang chunk tiếp theo với score thấp hơn (nằm ngoài Top-3).
   - *Bài học*: Fixed-size chunking làm phân tán các thực thể quan trọng (URL, số liệu) ra nhiều chunk khác nhau, khiến việc thu thập bằng chứng đầy đủ bị thất bại.
2. **Ví dụ lỗi 2 — Strategy B (Câu `q03` tập Dev)**:
   - *Câu hỏi*: "Sáng chế có mã số IN20221104896 tại Ấn Độ kết hợp công nghệ nào với AI để tăng tính bảo mật cho hệ thống chăm sóc sức khỏe?"
   - *Gold Page*: Trang 8 | *Bằng chứng*: `công nghệ blockchain... mã số IN20221104896`
   - *Kết quả*: Top-1 trả về trang 8 (`score = 0.8024`), nhưng đoạn văn trên trang 8 bắt đầu câu chuyện blockchain ở cuối trang 8 và kéo dài sang trang 9 (`26/8/2022, đề cập đến việc sử dụng...`). Do chia theo ranh giới trang, bằng chứng bị cắt đôi giữa trang 8 và trang 9.
   - *Bài học*: Cần có cơ chế gối ngữ cảnh liên trang (cross-page context stitching) khi một đoạn văn nằm vắt ngang giữa hai trang tài liệu.

### Chiến lược được chọn, đánh đổi và điều kiện áp dụng
- **Chiến lược được chọn**: **Strategy C (Paragraph-aware Chunking kết hợp Metadata Filtering)** là chiến lược tối ưu toàn diện nhất.
- **Lý do lựa chọn**:
  - Đạt Hit@3 cao nhất trên cả Dev (93.3%) và Test (80.0%).
  - Đạt điểm Coherence cao nhất (2.00/2.0) và Grounding cao nhất (1.60/2.0).
  - Tiết kiệm 14% dung lượng vector lưu trữ so với Fixed-size chunking.
  - Khả năng kiểm soát phạm vi chính xác khi người dùng cung cấp ngữ cảnh lọc.
- **Đánh đổi (Trade-offs)**:
  - Phụ thuộc vào chất lượng trích xuất cấu trúc đoạn văn của thư viện PDF. Nếu tài liệu bị scan hoặc lỗi layout không có dấu ngắt đoạn, pipeline cần bước phân tích layout (layout analysis) phức tạp hơn.
  - Yêu cầu ứng dụng AI phải có khả năng trích xuất hoặc nhận diện đúng metadata filter từ ý định người dùng trước khi truy vấn vector store.

### Hạn chế và Hướng cải tiến
- **Hạn chế**:
  - Tập test gồm 5 câu là kích thước mẫu nhỏ theo quy định lab, độ biến động của từng câu có thể gây dao động chỉ số tỷ lệ % lớn (mỗi câu chiếm 20%).
  - Môi trường Gemini Free Tier bị giới hạn tốc độ 100 requests/phút đòi hỏi phải cài đặt cơ chế sleep backoff, làm tăng tổng thời gian ingest ban đầu.
- **Hướng cải tiến nếu mở rộng**:
  1. *Hybrid Retrieval*: Kết hợp Dense Vector Search (Gemini Embedding) với Sparse Keyword Search (BM25) để tối ưu hóa việc tìm kiếm các từ khóa chính xác như mã số sáng chế (`IN20221104896`, `US10963795B2`).
  2. *Cross-page Stitching*: Tự động nối các đoạn văn bị đứt gãy ở ranh giới chân trang và đầu trang kế tiếp để tránh chia cắt bằng chứng.
