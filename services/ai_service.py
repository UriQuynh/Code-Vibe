from openai import OpenAI
from utils.security import decrypt_token

def generate_ai_prompts(source_data: dict, target_type: str, user_encrypted_key: str):
    try:
        real_api_key = decrypt_token(user_encrypted_key)
        client = OpenAI(api_key=real_api_key)
        
        system_prompt = """
        Bạn là chuyên gia sáng tạo nội dung E-commerce. 
        Dựa trên dữ liệu sản phẩm, hãy tạo ra 2 loại Prompt:
        1. Prompt cho Sora (Video): Mô tả chuyển động, ánh sáng, góc máy quay sản phẩm.
        2. Prompt cho Midjourney (Ảnh): Mô tả bối cảnh studio, phong cách nghệ thuật.
        Trả về định dạng JSON thuần gồm 2 keys: `sora_prompt` và `midjourney_prompt`.
        """
        
        user_content = f"Dữ liệu sản phẩm ({target_type}): {source_data}"
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={ "type": "json_object" }
        )
        return response.choices[0].message.content
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"{{'error': '{str(e)}'}}"
