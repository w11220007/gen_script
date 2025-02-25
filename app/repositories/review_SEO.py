import re
import json
import os
from app.core.settings import settings

os.environ["GOOGLE_API_KEY"] = "AIzaSyCr5whd4_46jBsXqippmtf6Jh5eqXjN4uY"
def analyze_seo_content(content, keyword):
    score = 0
    analysis = {}
    suggestions = []
    words = content.split()
    word_count = len(words)
    keyword_count = content.lower().count(keyword.lower())
    keyword_density = (keyword_count / word_count) * 100 if word_count else 0

    # Tiêu đề (H1)
    h1_match = re.search(r'<h1>(.*?)</h1>', content, re.IGNORECASE)
    has_h1 = bool(h1_match)
    score += 10 if has_h1 else 0
    suggestions.append(
        "You have added H1" if has_h1 else "You need to add an H1 heading")

    # Meta description
    meta_match = re.search(r'<meta name="description" content="(.*?)"', content,
                           re.IGNORECASE)
    has_meta = bool(meta_match)
    score += 10 if has_meta else 0
    suggestions.append(
        "You have added a meta description" if has_meta else "You need to add a meta description")

    # Hình ảnh có ALT
    alt_count = len(re.findall(r'<img [^>]*alt="[^"]+"', content, re.IGNORECASE))
    score += min(10, alt_count * 2)  # Tối đa 10 điểm
    suggestions.append(
        f"You have {alt_count} images with ALT attributes" if alt_count else "You need to add ALT attributes to images")

    # Liên kết nội bộ
    internal_links = len(re.findall(r'<a href="/[^>]+">', content))
    score += min(10, internal_links * 2)  # Tối đa 10 điểm
    suggestions.append(
        f"You have {internal_links} internal links" if internal_links else "You need to add internal links")

    # Mật độ từ khóa (tối ưu khoảng 1-3%)
    if 1 <= keyword_density <= 3:
        score += 15
    elif keyword_density > 3:
        score += 5  # Quá nhiều từ khóa cũng không tốt
    suggestions.append(
        f"Keyword density is {round(keyword_density, 2)}%" if 1 <= keyword_density <= 3 else "Keyword density should be between 1-3%")

    # Độ dài nội dung
    if word_count >= 300:
        score += 20
    elif word_count >= 150:
        score += 10
    suggestions.append(
        f"Content length is {word_count} words" if word_count >= 300 else "Content should have at least 300 words")

    # Tính toán điểm tổng
    max_score = 95  # Điểm tối đa có thể đạt được
    final_score = (score / max_score) * 100

    # Kết quả phân tích
    analysis['Word Count'] = word_count
    analysis['Keyword Count'] = keyword_count
    analysis['Keyword Density (%)'] = round(keyword_density, 2)
    analysis['Has H1'] = has_h1
    analysis['Has Meta Description'] = has_meta
    analysis['ALT Attributes Count'] = alt_count
    analysis['Internal Links Count'] = internal_links
    analysis['Final Score'] = round(final_score, 2)
    analysis['Suggestions'] = suggestions

    return analysis
    print(analysis)

def save_output_review(output, output_format, file_name):
    """
    Saves the SEO analysis results in the desired format.
    """
    # Chuyển output thành chuỗi JSON
    output_str = json.dumps(output, indent=4, ensure_ascii=False)

    # Kiểm tra loại dữ liệu của output trước khi ghi file (debug)
    print("Output type:", type(output_str))  # Nên là <class 'dict'>
    print("Output content (JSON string):\n", output_str)

    # Ghi file với output_str để tránh lỗi
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(output_str)  # Ghi dưới dạng chuỗi luôn, không cần json.dump()
def main():
    content = "<h1>AI and SEO</h1> <meta name='description' content='An overview of AI in SEO.'> AI is evolving."
    keyword = "AI"
    output_format = "markdown"  # Có thể là 'markdown', 'json', hoặc 'txt'

    settings = type("Settings", (object,), {"media_dir_static": "/var/www/media/"})()

    # Chạy phân tích SEO
    analysis_result = analyze_seo_content(content, keyword)

    # Tạo tên file và đường dẫn
    output_file = f"review.{output_format}"
    output_path = os.path.join(settings.media_dir_static, output_file)

    # Lưu dữ liệu
    save_output_review(analysis_result, output_format, output_path)
    print(f"File saved at: {output_path}")

