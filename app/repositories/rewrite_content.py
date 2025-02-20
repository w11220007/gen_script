import json
import os
import re
import google.generativeai as genai  # Using Gemini API

os.environ["GOOGLE_API_KEY"] = "AIzaSyCr5whd4_46jBsXqippmtf6Jh5eqXjN4uY"

'''style = [
    'Auto-select by AI', 'Pain point + harms + solution, using fear-based hooks', 'Pain points + harms + solutions, using curiosity-based hooks',
    'Pain ponts + harms + solutions, using pain point hooks',
    'Pain ponit + harms + solution, using pain point hooks', 'Pain points + harms + solutions, using hooks related to relationships',
    'Attention-grabbing opening + setting expectation + solutions, using reveal-type hooks',
]'''
def analyze_layout(text):
    """Analyze the paragraph layout by detecting sentence length and spacing."""
    sentences = re.split(r'([.!?])', text)  # Split by punctuation
    layout = [(len(s.strip()), s) for s in sentences if s.strip()]
    return layout


def generate_new_text(prompt, tone):
    """Generate a new paragraph with the requested tone using the Gemini API."""
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(
        f"Rewrite the paragraph with a {tone} tone: {prompt}")
    return response.text


def format_text(original_text, new_content):
    """Format the new paragraph according to the original layout."""
    old_layout = analyze_layout(original_text)
    new_sentences = re.split(r'([.!?])', new_content)
    new_sentences = [s.strip() for s in new_sentences if s.strip()]

    formatted_text = ""
    idx = 0
    for length, structure in old_layout:
        if idx < len(new_sentences):
            formatted_text += new_sentences[idx] + (
                structure if structure in ".!?" else " ")
            idx += 1
    return formatted_text


def save_result_SEO_content(output, output_format, file_name):
    """
    Saves the generated evaluation in the desired format.
    """
    if isinstance(output, str):  # Validate output is a string
        if output_format == "markdown":
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(output)
        elif output_format == "html":
            html_content = f"<html><body><pre>{output}</pre></body></html>"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(html_content)
        elif output_format == "json":
            evaluation_json = {"evaluation": output.split("\n")}
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(evaluation_json, f, indent=4, ensure_ascii=False)
        else:
            raise ValueError("Unsupported output format.")
    else:
        raise TypeError("Output must be a string.")

def process_SEO_evaluation():
    """
    Execute the SEO evaluation process and save the results.
    """
    output_format = "markdown"  # Can be 'markdown', 'json', or 'html'
    settings = type("Settings", (object,), {"media_dir_static": "/var/www/media/"})()

    output_file = f"SEO_content.{output_format}"
    output_path = os.path.join(settings.media_dir_static, output_file)

    analysis_result = "SEO analysis result goes here"  # Placeholder result
    save_result_SEO_content(analysis_result, output_format, output_path)
    print(f"File saved at: {output_path}")


