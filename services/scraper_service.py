import requests

def get_shopee_product_data(product_url: str):
    """
    Get generic shopee product data (Using RapidAPI dummy logic or real logic)
    """
    # Assuming using RapidAPI for real data
    # api_url = "https://shopee-data-api.p.rapidapi.com/product_info"
    # headers = {"X-RapidAPI-Key": "YOUR_KEY"}
    # response = requests.get(api_url, params={"url": product_url}, headers=headers)
    # return response.json()
    
    # Dummy logic to illustrate process
    return {
        "title": "Sản phẩm mẫu từ Shopee",
        "price": "100.000đ",
        "sold": 1200,
        "description": "Đây là mô tả mẫu lấy được từ link Shopee.",
        "url": product_url
    }

def get_tiktok_video_data(video_url: str):
    """
    Get logic for TikTok video
    """
    return {
        "title": "Video Tiktok Mẫu",
        "caption": "#xuhuong #sanpham",
        "transcript": "Đây là nội dung kịch bản bóc tách từ video...",
        "url": video_url
    }
