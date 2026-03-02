from openai import OpenAI
from utils.security import decrypt_token
import json

SYSTEM_PROMPT = """
Bạn là chuyên gia sáng tạo nội dung E-commerce hàng đầu Việt Nam.
Dựa trên dữ liệu sản phẩm/video được cung cấp, hãy tạo ra 2 loại Prompt:

1. **sora_prompt** (Prompt cho Video AI - Sora/Runway/Luma):
   - Mô tả chuyển động camera (pan, zoom, dolly)
   - Ánh sáng (studio lighting, golden hour, neon...)
   - Góc quay (close-up sản phẩm, lifestyle shot...)
   - Bối cảnh (studio trắng, phòng khách sang trọng, ngoài trời...)
   - Thời lượng và nhịp điệu

2. **midjourney_prompt** (Prompt cho Ảnh AI - Midjourney/Flux):
   - Mô tả bối cảnh studio cao cấp
   - Phong cách nghệ thuật (minimalist, luxury, editorial...)
   - Ánh sáng và màu sắc
   - Tỷ lệ và bố cục

Trả về **JSON thuần** gồm đúng 2 keys: `sora_prompt` và `midjourney_prompt`.
Mỗi prompt phải viết bằng tiếng Anh, chi tiết ít nhất 3 dòng.
"""

def generate_ai_prompts(source_data: dict, target_type: str, user_encrypted_key: str, gemini_encrypted_key: str = None):
    """
    Ưu tiên dùng Gemini (miễn phí), fallback sang OpenAI.
    """
    # Thử Gemini trước (miễn phí, không bị quota)
    if gemini_encrypted_key:
        result = _try_gemini(source_data, target_type, gemini_encrypted_key)
        if result and "error" not in result.lower():
            return result

    # Fallback sang OpenAI
    if user_encrypted_key:
        result = _try_openai(source_data, target_type, user_encrypted_key)
        return result

    return json.dumps({"error": "Chưa có API Key nào được cấu hình. Vui lòng vào Settings nhập Gemini hoặc OpenAI Key."})


def _try_gemini(source_data: dict, target_type: str, gemini_encrypted_key: str) -> str:
    """Gọi Google Gemini API"""
    try:
        import google.generativeai as genai
        
        real_api_key = decrypt_token(gemini_encrypted_key)
        genai.configure(api_key=real_api_key)
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        user_content = f"Dữ liệu sản phẩm ({target_type}): {json.dumps(source_data, ensure_ascii=False)}"
        
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\n{user_content}\n\nTrả về JSON thuần, không có markdown code block.",
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7,
            )
        )
        
        return response.text
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": f"Gemini lỗi: {str(e)}"})


def _try_openai(source_data: dict, target_type: str, user_encrypted_key: str) -> str:
    """Gọi OpenAI API (fallback)"""
    try:
        real_api_key = decrypt_token(user_encrypted_key)
        client = OpenAI(api_key=real_api_key)
        
        user_content = f"Dữ liệu sản phẩm ({target_type}): {json.dumps(source_data, ensure_ascii=False)}"
        
        # Thử gpt-4o-mini trước (rẻ hơn 15x so với gpt-4o)
        for model_name in ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            except Exception:
                continue
        
        return json.dumps({"error": "Tất cả model OpenAI đều lỗi. Kiểm tra lại API Key và Billing tại platform.openai.com"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": f"OpenAI lỗi: {str(e)}"})
