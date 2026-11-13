"""Build and verify benchmark/questions.json with 100% guaranteed exact substring slices."""
import json
import re
from pathlib import Path
from starter.src.ingestion import load_pdf

def slice_page(page_text: str, start_words: str, end_words: str) -> str:
    pattern = (
        r"("
        + r"\s+".join(re.escape(w) for w in start_words.split())
        + r".*?"
        + r"\s+".join(re.escape(w) for w in end_words.split())
        + r")"
    )
    m = re.search(pattern, page_text, re.DOTALL)
    if not m:
        raise ValueError(f"Pattern not found between [{start_words}] and [{end_words}]")
    return m.group(1)

def main():
    root = Path(__file__).resolve().parent.parent.parent
    pdf_path = root / "2023-BC-toan-canh-cong-nghe-AI-cham-soc-suc-khoe.pdf"
    pages = load_pdf(pdf_path, include_cover_and_toc=True)
    p_map = {p.page: p.text for p in pages}

    # 20 questions specifications
    specs = [
        # DEV QUESTIONS (15)
        {
            "id": "q01",
            "split": "dev",
            "question_type": "direct",
            "question": "Trí tuệ nhân tạo (AI) phục vụ lĩnh vực chăm sóc sức khỏe được định nghĩa như thế nào trong phần mở đầu?",
            "expected_answer": "Là việc sử dụng các thuật toán và phần mềm phức tạp (như học máy cổ điển, học máy sâu, xử lý ngôn ngữ tự nhiên,...) để hỗ trợ con người trong việc phân tích các dữ liệu y tế phức tạp, thực hiện các công tác chẩn đoán y khoa, bào chế thuốc.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 3,
            "start": "Trí tuệ nhân tạo (AI) phục vụ lĩnh vực chăm sóc sức khỏe",
            "end": "bào chế thuốc",
            "filter": None
        },
        {
            "id": "q02",
            "split": "dev",
            "question_type": "direct",
            "question": "Trong giai đoạn 1985-2022, số lượng sáng chế AI y tế đăng ký bảo hộ gia tăng liên tục ở những quốc gia và tổ chức nào?",
            "expected_answer": "Gia tăng liên tục ở Trung Quốc, Ấn Độ và PCT.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 7,
            "start": "số lượng sáng chế đăng ký bảo hộ gia tăng",
            "end": "Ấn Độ và PCT.",
            "filter": None
        },
        {
            "id": "q03",
            "split": "dev",
            "question_type": "direct",
            "question": "Sáng chế có mã số IN20221104896 tại Ấn Độ kết hợp công nghệ nào với AI để tăng tính bảo mật cho hệ thống chăm sóc sức khỏe?",
            "expected_answer": "Kết hợp công nghệ blockchain (chuỗi khối an toàn hỗ trợ trí tuệ nhân tạo).",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 8,
            "start": "công nghệ blockchain để tăng tính bảo mật",
            "end": "IN20221104896",
            "filter": None
        },
        {
            "id": "q04",
            "split": "dev",
            "question_type": "direct",
            "question": "Sáng chế US10963795B2 của Tập đoàn IBM đăng ký tại Mỹ năm 2015 giải quyết bài toán gì?",
            "expected_answer": "Tạo các mô hình dự đoán dựa trên phân tích văn bản của dữ liệu nghiên cứu y học.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 11,
            "start": "sáng chế có mã số US10963795B2 đăng ký",
            "end": "dữ liệu nghiên cứu y học",
            "filter": None
        },
        {
            "id": "q05",
            "split": "dev",
            "question_type": "direct",
            "question": "Sáng chế KR10-2020-0066484A đăng ký tại Hàn Quốc của Trung tâm Y tế Asan hỗ trợ điều trị bệnh gì?",
            "expected_answer": "Hỗ trợ quyết định lâm sàng cho bệnh ung thư đại trực tràng.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 13,
            "start": "Sáng chế có mã số KR10-2020-0066484A",
            "end": "đ ại trực tràng",
            "filter": None
        },
        {
            "id": "q06",
            "split": "dev",
            "question_type": "direct",
            "question": "So sánh tương quan giữa 6 quốc gia/tổ chức, quốc gia nào có tỷ lệ bảo hộ cao nhất đối với Hệ thống hỗ trợ chẩn đoán bệnh?",
            "expected_answer": "Trung Quốc có tỷ lệ bảo hộ cao nhất đối với hệ thống hỗ trợ phân tích chẩn đoán.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 14,
            "start": "So sánh tương quan về tỷ lệ bảo hộ giữa 6 quốc gia/tổ chức",
            "end": "phân tích chẩn đoán và ra quyết định",
            "filter": None
        },
        {
            "id": "q07",
            "split": "dev",
            "question_type": "paraphrase",
            "question": "Tập đoàn công nghệ nào của Hà Lan dẫn đầu bảng xếp hạng top 25 tổ chức sở hữu sáng chế AI trong y tế trên toàn cầu?",
            "expected_answer": "Koninklijke Philips Electronics N.V. (Hà Lan).",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 22,
            "start": "Dẫn đầu sở hữu các sáng chế ứng dụng công nghệ AI",
            "end": "Koninklijke Philips Electronics N.V. (Hà Lan)",
            "filter": None
        },
        {
            "id": "q08",
            "split": "dev",
            "question_type": "direct",
            "question": "Tập đoàn Koninklijke Philips Electronics N.V. của Hà Lan đăng ký bảo hộ sáng chế AI y tế chủ yếu tại đâu?",
            "expected_answer": "Đăng ký bảo hộ chủ yếu tại PCT (181 sáng chế) và Mỹ (105 sáng chế).",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 24,
            "start": "tập đoàn Koninklijke Philips Electronics N.V.",
            "end": "Mỹ (105 sáng chế)",
            "filter": None
        },
        {
            "id": "q09",
            "split": "dev",
            "question_type": "metadata_filter",
            "question": "Trong nhóm các sáng chế về kỹ thuật xử lý dữ liệu y tế, có bao nhiêu phần trăm liên quan đến Kỹ thuật xử lý dữ liệu bệnh án điện tử?",
            "expected_answer": "25,4% liên quan đến Kỹ thuật xử lý dữ liệu bệnh án điện tử, phần lớn sử dụng xử lý ngôn ngữ tự nhiên (NLP) để phân tích các văn bản y khoa.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 10,
            "start": "25,4% liên quan đ ến Kỹ thuật xử lý dữ liệu bệnh án",
            "end": "phân tích các văn bản y khoa",
            "filter": {"section": "phan_1_the_gioi"}
        },
        {
            "id": "q10",
            "split": "dev",
            "question_type": "metadata_filter",
            "question": "Đơn vị nào tại Việt Nam là chủ đơn sáng chế hệ thống robot y tế vận chuyển phục vụ trong khu cách ly bệnh truyền nhiễm nguy cơ cao?",
            "expected_answer": "Viện Khoa học và Công nghệ Quân sự (Việt Nam), số đơn VN 2-2021-00058.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 29,
            "start": "Hệ thống robot y t ế vận chuyển phục vụ",
            "end": "Viện Khoa học và Công nghệ Quân sự (Việt Nam)",
            "filter": {"section": "phan_2_viet_nam"}
        },
        {
            "id": "q11",
            "split": "dev",
            "question_type": "direct",
            "question": "Những ai là tác giả của sáng chế về phương pháp và hệ thống chỉnh sửa báo cáo hình ảnh y khoa được bảo hộ tại Việt Nam?",
            "expected_answer": "Trương Quốc Hùng, Hoàng Vũ, Nguyễn Mạnh Hùng, Bùi Hữu Trung, Nguyễn Anh Tú.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 32,
            "start": "Tác giả sáng chế: Trương Quốc Hùng",
            "end": "Nguyễn Anh Tú.",
            "filter": None
        },
        {
            "id": "q12",
            "split": "dev",
            "question_type": "conditional_exception",
            "question": "Khó khăn lớn nhất trong quá trình nghiên cứu khai thác bệnh án điện tử tiếng Việt là gì?",
            "expected_answer": "Xử lý dữ liệu lâm sàng do bác sĩ/điều dưỡng ghi vào bệnh án, do đây là ngôn ngữ tự nhiên và chưa được chuẩn hóa.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 34,
            "start": "Khó khăn lớn nhất trong quá trình nghiên cứu là việc xử lý",
            "end": "chưa được chuẩn hóa.",
            "filter": None
        },
        {
            "id": "q13",
            "split": "dev",
            "question_type": "direct",
            "question": "Mô hình nghiên cứu học máy trong ung thư biểu mô tế bào gan tại Việt Nam cho phép dự đoán khả năng đáp ứng những phương pháp điều trị nào?",
            "expected_answer": "Dự đoán khả năng đáp ứng điều trị TACE và Sorafenib dựa trên kết quả RT-qPCR.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 38,
            "start": "cho phép ch ẩn đoán s ớm",
            "end": "người Vi ệt Nam",
            "filter": None
        },
        {
            "id": "q14",
            "split": "dev",
            "question_type": "conditional_exception",
            "question": "Các công cụ phân biệt viêm ruột thừa và viêm ruột thừa có biến chứng hiện có (như Alvarado, APSI, Atema) có nhược điểm hoặc đòi hỏi điều kiện gì?",
            "expected_answer": "Đòi hỏi phải có thông tin chi tiết từ CT scan.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 42,
            "start": "Các công c ụ để phân biệt VRT và VRT có bi ến chứng",
            "end": "CT scan",
            "filter": None
        },
        {
            "id": "q15",
            "split": "dev",
            "question_type": "direct",
            "question": "Website nào được nhóm nghiên cứu giới thiệu nhằm ứng dụng AI trong hỗ trợ phát hiện viêm ruột thừa biến chứng?",
            "expected_answer": "Địa chỉ website là https://viemruotthua.com/.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 43,
            "start": "website nh ằm ứng dụng AI trong hỗ trợ phát hiện viêm",
            "end": "https://viemruotthua.com/.",
            "filter": None
        },

        # TEST QUESTIONS (5)
        {
            "id": "q16",
            "split": "test",
            "question_type": "direct",
            "question": "Hệ thống robot phẫu thuật nào của Công ty Intuitive Surgical đã thực hiện hơn 1,8 triệu ca phẫu thuật trên toàn cầu?",
            "expected_answer": "Hệ thống phẫu thuật robot Da Vinci.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 40,
            "start": "robot phẫu thuật Da Vinci",
            "end": "năm 2022",
            "filter": None
        },
        {
            "id": "q17",
            "split": "test",
            "question_type": "metadata_filter",
            "question": "Tại Việt Nam, ứng dụng di động nào được Công ty Cổ phần 1SK phát triển để theo dõi sức khỏe thông minh cho người bệnh?",
            "expected_answer": "Ứng dụng 1SK Health Tracker.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 45,
            "start": "1SK Health Tracker",
            "end": "1SK RPM Platform",
            "filter": {"section": "phan_2_viet_nam"}
        },
        {
            "id": "q18",
            "split": "test",
            "question_type": "paraphrase",
            "question": "Công trình nghiên cứu công nghệ lõi khai thác bệnh án điện tử tiếng Việt do đơn vị nào chủ trì thực hiện?",
            "expected_answer": "Do nhóm nghiên cứu tại Đại học Quốc gia TP.HCM phối hợp với 17 bệnh viện lớn.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 33,
            "start": "công trình nghiên cứu “Phát triển những công nghệ lõi",
            "end": "Đại học Quốc gia TP.HCM",
            "filter": None
        },
        {
            "id": "q19",
            "split": "test",
            "question_type": "conditional_exception",
            "question": "Nghiên cứu ứng dụng dữ liệu lớn và học máy trong chẩn đoán ung thư biểu mô tế bào gan tại Việt Nam gặp phải những hạn chế nào?",
            "expected_answer": "Số mẫu chưa đủ nhiều, chưa kết hợp được các yếu tố lâm sàng vào mô hình, và chưa có dữ liệu đáp ứng thuốc của bệnh nhân Việt Nam.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 39,
            "start": "Tuy nhiên, nghiên cứu vẫn còn gặp một số hạn chế",
            "end": "bệnh nhân Việt Nam.",
            "filter": None
        },
        {
            "id": "q20",
            "split": "test",
            "question_type": "paraphrase",
            "question": "Theo phần kết luận của báo cáo, nhóm sáng chế nào về xử lý dữ liệu y tế chiếm đa số?",
            "expected_answer": "Nhóm sáng chế về Kỹ thuật xử lý dữ liệu hình ảnh y tế và Kỹ thuật xử lý dữ liệu bệnh án điện tử.",
            "gold_source_id": "cesti-2023-ai-healthcare",
            "gold_page": 47,
            "start": "nhóm các sáng chế về Kỹ thuật xử lý dữ liệu hình ảnh y tế",
            "end": "chiếm đa số.",
            "filter": None
        }
    ]

    questions = []
    print(f"Generating and verifying exact slices for {len(specs)} questions...")
    for s in specs:
        p_text = p_map[s["gold_page"]]
        slice_quote = slice_page(p_text, s["start"], s["end"])
        assert slice_quote in p_text, f"Internal error: slice not in page for {s['id']}"

        q_obj = {
            "id": s["id"],
            "split": s["split"],
            "question_type": s["question_type"],
            "question": s["question"],
            "expected_answer": s["expected_answer"],
            "gold_source_id": s["gold_source_id"],
            "gold_page": s["gold_page"],
            "evidence_quote": slice_quote,
            "filter": s["filter"]
        }
        questions.append(q_obj)
        print(f"  [{s['id']}] {s['split']} (Page {s['gold_page']}): 100% VERIFIED ({len(slice_quote)} chars)")

    benchmark_dir = root / "benchmark"
    benchmark_dir.mkdir(exist_ok=True)
    out_file = benchmark_dir / "questions.json"
    out_file.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSUCCESS: All {len(questions)} questions verified and saved to {out_file}")

if __name__ == "__main__":
    main()
