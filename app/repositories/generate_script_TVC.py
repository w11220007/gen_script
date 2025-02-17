import fitz  # PyMuPDF
import json
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.settings import settings
from langchain.prompts import PromptTemplate
import re

# Cấu hình Google Generative AI (Gemini)
os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key

# Danh sách các script types, frameworks, tones
SCRIPT_TYPES = {
    "Product Highlights": ["sản phẩm", "tính năng", "đặc điểm", "ưu điểm", "công nghệ"],
    "Brand Story": ["câu chuyện", "hành trình", "sáng lập", "nguồn cảm hứng", "sứ mệnh"],
    "Problem-Solving": ["vấn đề", "khó khăn", "giải pháp", "thay đổi", "cải thiện"],
    "Call-to-Action": ["mua ngay", "đăng ký", "trải nghiệm", "thử ngay", "đặt hàng"]
}

FRAMEWORKS = {
    "PAS (Problem-Agitate-Solution)": ["vấn đề", "ảnh hưởng", "giải pháp"],
    "BAB (Before-After-Bridge)": ["trước đây", "sau đó", "thay đổi", "kết quả"],
    "AIDA (Attention-Interest-Desire-Action)": ["thu hút", "quan tâm", "mong muốn", "hành động"],
    "FAB (Feature-Advantage-Benefit)": ["tính năng", "ưu điểm", "lợi ích"],
    "The Hero’s Journey": ["hành trình", "thử thách", "biến đổi", "chiến thắng"]
}

TONES = {
    "Engaging": ["hấp dẫn", "thú vị", "sáng tạo", "trendy"],
    "Commercial": ["chuyên nghiệp", "quảng cáo", "doanh nghiệp", "chính thống"],
    "Gen Z": ["hài hước", "viral", "tiktok", "memes", "trend"],
    "Simple": ["ngắn gọn", "dễ hiểu", "đơn giản"],
    "Motivational": ["truyền cảm hứng", "động lực", "bứt phá", "cố gắng"],
    "Professional": ["lịch sự", "trang trọng", "doanh nghiệp"],
    "Inspirational": ["chạm vào cảm xúc", "ý nghĩa", "động lực sống"]
}

CUSTOMER_SEGMENTS = {
    "Gen Z": ["trẻ", "tiktok", "meme", "vui nhộn", "hài hước", "sáng tạo"],
    "Phụ nữ đã có chồng": ["gia đình", "con cái", "chăm sóc", "mẹ bỉm", "nuôi con"],
    "Doanh nhân": ["kinh doanh", "thành công", "đầu tư", "quản lý", "công việc"],
    "Dân văn phòng": ["công việc", "deadline", "stress", "họp", "máy tính"],
    "Người yêu thích thể thao": ["tập luyện", "fitness", "khỏe mạnh", "thể chất"],
}


# Hàm đọc nội dung từ file PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()

def extract_json(response_text):
    try:
        # Tìm đoạn JSON hợp lệ trong response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            raise ValueError("Không tìm thấy JSON hợp lệ trong phản hồi.")
    except json.JSONDecodeError:
        raise ValueError("Phản hồi không phải là JSON hợp lệ.")


# Hàm tìm loại script, framework, tone, và tệp khách hàng phù hợp
def analyze_text(text):
    prompt = PromptTemplate(
        input_variables=["text"],
        template="""
            Bạn là chuyên gia sáng tạo quảng cáo. Hãy phân tích đoạn văn bản sau và xác định:
            **Yêu cầu**:
            - *Chỉ trả về JSON hợp lệ**, không thêm bất kỳ nội dung nào khác.
            - Hãy đảm bảo định dạng chuẩn bằng cách bọc kết quả trong `json.dumps()`
            - Các giá trị bao gồm:
                - Loại kịch bản (Product Highlights, Brand Story, Problem-Solving, Call-to-Action)
                - Framework phù hợp (PAS, BAB, AIDA, FAB, Hero’s Journey)
                - Tone phù hợp (Engaging, Commercial, Gen Z, Simple, Motivational, Professional, Inspirational)
                - Tệp khách hàng phù hợp nhất (Gen Z, Phụ nữ đã có chồng, Doanh nhân, Dân văn phòng, Người yêu thích thể thao)

            Văn bản:
            {text}
            **JSON output**
                        {{
                "script_type": "...",
                "framework": "...",
                "tone": "...",
                "customer_segment": "..."
            }}
            """
    )
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.5,
            max_tokens=1024,
            timeout=30,
            max_retries=3,
        )
        prompt_text = prompt.format(text=text)
        # Chuyển thành chuỗi
        #print(f"abc: {prompt_text}")
        response = llm.invoke(prompt_text)
        response_text = response.content.strip()
        response_text = re.sub(r"```json|```", "", response_text, flags=re.DOTALL).strip()
        #print("Process response:")
        #print(response_text)
        try:
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError:
            raise RuntimeError(
                "Gemini AI trả về dữ liệu không hợp lệ. Kiểm tra lại đầu vào.")

    except Exception as e:
        raise RuntimeError(f"Error analyze text: {str(e)}")


# Hàm tạo kịch bản TVC với lời thoại + mô tả cảnh quay
def process_tvc_script(company_name, text):
    # Đọc nội dung PDF
    try:
        analysis_result  = analyze_text(text)
        script_type = analysis_result.get("script_type")
        framework = analysis_result.get("framework")
        tone = analysis_result.get("tone")
        customer_segment = analysis_result.get("customer_segment")

        prompt = PromptTemplate(
            input_variables=["text", "script_type", "framework", "tone",
                             "customer_segment"],
            template="""
            Bạn là chuyên gia sáng tạo quảng cáo. Viết một kịch bản TVC dựa trên nội dung sau:
            {text}

            Thông tin kịch bản:
            - 🏷 **Loại kịch bản**: {script_type}
            - 📜 **Framework**: {framework}
            - 🎭 **Tone**: {tone}
            - 🎯 **Tệp khách hàng**: {customer_segment}

            Kịch bản cần bao gồm:
            - 🎙 ** Chỉ có lời thoại (Voice-over)** để lồng tiếng**
            Hãy đảm bảo kịch bản thu hút, hấp dẫn, phù hợp với đối tượng khách hàng.
            """
        )
        # Bước 3: Gọi Gemini AI để sinh nội dung TVC
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3,
            max_tokens=1024,
            timeout=30,
            max_retries=3,
        )
        prompt_text = prompt.format(
            company_name=company_name,
            text=text,
            script_type=script_type,
            framework=framework,
            tone=tone,
            customer_segment=customer_segment
        )

        response = llm.invoke(prompt_text)

        # Xử lý đầu ra từ Gemini
        script_output = response.content.strip()

        return script_output  # Trả về kết quả dưới dạng markdown

    except Exception as e:
        raise RuntimeError(f"Error generating script: {str(e)}")


# Hàm lưu kịch bản TVC dưới dạng markdown, html hoặc json
def save_out_TVC(output, output_format, file_name):
    if isinstance(output, str):
        if output_format == "markdown":
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(output)
        elif output_format == "html":
            html_content = f"<html><body><pre>{output}</pre></body></html>"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(html_content)
        elif output_format == "json":
            tvc_json = format_script_to_json(output)
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(tvc_json, f, indent=4, ensure_ascii=False)
        else:
            raise ValueError("Unsupported output format.")
    else:
        raise TypeError("Output must be a string.")


# Hàm chuyển đổi kịch bản TVC thành JSON
def format_script_to_json(output):
    lines = output.split("\n")
    scenes = []
    current_scene = None

    for line in lines:
        line = line.strip()
        if line.startswith("📌"):
            if current_scene:
                scenes.append(current_scene)
            current_scene = {"scene": line, "details": []}
        elif current_scene and line:
            current_scene["details"].append(line)

    if current_scene:
        scenes.append(current_scene)

    return {"tvc_script": scenes}


