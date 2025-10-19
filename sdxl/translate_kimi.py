"""
使用Kimi API翻译中文提示词
"""
import requests
import json

def translate_with_kimi(text, api_key=None):
    """
    使用Kimi API翻译中文到英文
    
    使用方法:
    1. 获取Kimi API Key: https://platform.moonshot.cn/
    2. 设置环境变量: set KIMI_API_KEY=your_key
    3. 或者直接传入api_key参数
    """
    if not api_key:
        import os
        api_key = os.environ.get('KIMI_API_KEY')
    
    if not api_key:
        print("⚠ 未设置KIMI_API_KEY，使用简单翻译")
        return simple_translate(text)
    
    try:
        url = "https://api.moonshot.cn/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "moonshot-v1-8k",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的AI绘画提示词翻译助手。将中文提示词翻译成英文，保持绘画风格描述的准确性。只返回翻译结果，不要解释。"
                },
                {
                    "role": "user",
                    "content": f"将以下中文提示词翻译成英文AI绘画提示词：{text}"
                }
            ],
            "temperature": 0.3
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        translation = result['choices'][0]['message']['content'].strip()
        
        print(f"  [Kimi翻译] {text} -> {translation}")
        return translation
        
    except Exception as e:
        print(f"  [Kimi翻译失败] {e}，使用简单翻译")
        return simple_translate(text)

def simple_translate(text):
    """简单的关键词映射翻译"""
    mappings = {
        "老道士": "old taoist priest",
        "道士": "taoist priest",
        "蓝色长袍": "blue robe",
        "长袍": "robe",
        "神秘": "mysterious",
        "微笑": "smile",
        "中国风": "chinese style",
        "现代都市": "modern city",
        "都市": "city",
        "街道": "street",
        "黄昏": "sunset",
        "温暖": "warm",
        "光线": "lighting",
        "电影感": "cinematic",
        "高质量": "high quality",
        "细节": "detailed",
        "写实": "realistic",
        "动漫": "anime",
        "室内": "indoor",
        "书房": "study room",
        "年轻人": "young person",
        "思考": "thinking",
        "窗外": "outside window",
        "阳光": "sunlight",
    }
    
    result = text
    for cn, en in mappings.items():
        result = result.replace(cn, en)
    
    return result

# 测试
if __name__ == "__main__":
    test_prompts = [
        "一个穿蓝色长袍的老道士，神秘的微笑，中国风，高质量",
        "现代都市街道，黄昏时分，温暖的光线，电影感",
        "室内书房，一个年轻人在思考，窗外阳光"
    ]
    
    print("测试翻译功能:\n")
    for prompt in test_prompts:
        print(f"中文: {prompt}")
        translated = translate_with_kimi(prompt)
        print(f"英文: {translated}\n")
