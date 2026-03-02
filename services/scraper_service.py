import requests
import re
import json

def get_tiktok_video_data(video_url: str):
    """
    Lấy dữ liệu thật từ link TikTok bằng oembed API và scraping cơ bản.
    Hỗ trợ cả link video lẫn link profile.
    """
    result = {
        "title": "",
        "author": "",
        "caption": "",
        "likes": "",
        "thumbnail": "",
        "url": video_url
    }
    
    try:
        # Thử dùng TikTok oEmbed API (hoạt động với link video)
        oembed_url = f"https://www.tiktok.com/oembed?url={video_url}"
        resp = requests.get(oembed_url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            result["title"] = data.get("title", "Không lấy được tiêu đề")
            result["author"] = data.get("author_name", "")
            result["author_url"] = data.get("author_url", "")
            result["thumbnail"] = data.get("thumbnail_url", "")
            result["thumbnail_width"] = data.get("thumbnail_width", "")
            result["thumbnail_height"] = data.get("thumbnail_height", "")
            return result
    except Exception:
        pass

    try:
        # Fallback: Scrape trang web lấy meta tags
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(video_url, headers=headers, timeout=15, allow_redirects=True)
        html = resp.text

        # Lấy og:title
        og_title = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', html)
        if og_title:
            result["title"] = og_title.group(1)

        # Lấy og:description
        og_desc = re.search(r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"', html)
        if og_desc:
            result["caption"] = og_desc.group(1)

        # Lấy og:image (thumbnail)
        og_img = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]*)"', html)
        if og_img:
            result["thumbnail"] = og_img.group(1)

        # Lấy tên tác giả từ title tag
        title_tag = re.search(r'<title>([^<]*)</title>', html)
        if title_tag:
            result["page_title"] = title_tag.group(1)

        # Nếu không lấy được gì, báo rõ
        if not result["title"] and not result["caption"]:
            result["title"] = "Không thể bóc tách dữ liệu (TikTok chặn bot)"
            result["caption"] = "Anh cần dùng Cookie/Token TikTok hoặc API bên thứ 3 (RapidAPI) để lấy dữ liệu chi tiết hơn."
            
    except Exception as e:
        result["title"] = f"Lỗi khi lấy dữ liệu: {str(e)}"

    return result


def get_shopee_product_data(product_url: str):
    """
    Lấy dữ liệu thật từ link Shopee.
    Shopee chặn bot rất mạnh, nên cần fallback về scraping meta tags.
    """
    result = {
        "title": "",
        "price": "",
        "description": "",
        "image": "",
        "url": product_url
    }
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(product_url, headers=headers, timeout=15, allow_redirects=True)
        html = resp.text

        # Lấy og:title
        og_title = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', html)
        if og_title:
            result["title"] = og_title.group(1)

        # Lấy og:description
        og_desc = re.search(r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"', html)
        if og_desc:
            result["description"] = og_desc.group(1)

        # Lấy og:image
        og_img = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]*)"', html)
        if og_img:
            result["image"] = og_img.group(1)

        # Thử tìm giá trong JSON-LD hoặc meta
        price_match = re.search(r'"price":\s*"?(\d[\d,.]*)"?', html)
        if price_match:
            result["price"] = price_match.group(1)

        if not result["title"]:
            result["title"] = "Không thể bóc tách dữ liệu Shopee (bị chặn bot)"
            result["description"] = "Shopee chặn scraping rất mạnh. Anh cần dùng Shopee Open Platform API hoặc RapidAPI để lấy dữ liệu chính xác."

    except Exception as e:
        result["title"] = f"Lỗi khi lấy dữ liệu: {str(e)}"

    return result
