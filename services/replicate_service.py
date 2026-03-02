import replicate
from utils.security import decrypt_token

def generate_product_image(prompt: str, user_encrypted_key: str):
    """Sử dụng Replicate API (Mô hình Flux/SDXL) để tạo ảnh sản phẩm"""
    try:
        real_api_key = decrypt_token(user_encrypted_key)
        client = replicate.Client(api_token=real_api_key)
        
        # Gọi mô hình black-forest-labs/flux-schnell (hoặc model tùy chọn)
        output = client.run(
            "black-forest-labs/flux-schnell",
            input={"prompt": prompt, "num_outputs": 1, "aspect_ratio": "16:9", "output_format": "webp"}
        )
        
        # Output là một mảng URI file
        if isinstance(output, list) and len(output) > 0:
            return {"url": str(output[0])}
        return {"url": str(output)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def generate_product_video(prompt: str, user_encrypted_key: str):
    """Sử dụng Replicate API (Luma/Minimax) tạo video"""
    try:
        real_api_key = decrypt_token(user_encrypted_key)
        client = replicate.Client(api_token=real_api_key)
        
        # Có thể dùng minimax/video-01 hoặc luma/ray
        output = client.run(
            "minimax/video-01",
            input={"prompt": prompt, "prompt_optimizer": True}
        )
        
        # URI Output của video Mp4
        if isinstance(output, list) and len(output) > 0:
             return {"url": str(output[0])}
        return {"url": str(output)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
