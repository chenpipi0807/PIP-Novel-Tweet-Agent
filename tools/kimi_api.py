"""
Kimi API工具
支持超长文本处理
"""
import requests
import json
from pathlib import Path

class KimiAPI:
    def __init__(self, api_key=None):
        """
        初始化Kimi API
        
        Args:
            api_key: API密钥，如果不提供则从config.json读取
        """
        if api_key:
            self.api_key = api_key
        else:
            # 从config.json读取
            config_path = Path(__file__).parent.parent / "config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.api_key = config.get('kimi_api_key')
        
        if not self.api_key:
            raise ValueError("未找到API密钥")
        
        self.base_url = "https://api.moonshot.cn/v1"
        self.model = "moonshot-v1-auto"  # 使用 auto 自动选择最佳模型（包括k2）
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def test_connection(self):
        """测试API连接"""
        try:
            print("正在测试Kimi API连接...")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": "你好"}
                    ],
                    "temperature": 0.3
                },
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            print("✓ API连接成功！")
            print(f"✓ 模型响应: {result['choices'][0]['message']['content']}")
            return True
            
        except Exception as e:
            print(f"❌ API连接失败: {e}")
            return False
    
    def chat(self, messages, model=None, temperature=0.3, stream=False, max_tokens=None):
        """
        调用Kimi聊天API
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称（None则使用默认的auto模型）
                - moonshot-v1-auto: 自动选择最佳模型（推荐，包括k2）
                - moonshot-v1-8k: 8k上下文
                - moonshot-v1-32k: 32k上下文
                - moonshot-v1-128k: 128k上下文（超长文本）
            temperature: 温度参数 0-1
            stream: 是否流式输出
            max_tokens: 最大输出token数，None表示不限制
        
        Returns:
            str: AI回复内容
        """
        try:
            # 如果没指定模型，使用默认的auto模型
            if model is None:
                model = self.model
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream
            }
            
            # 只有指定了max_tokens才添加
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=300  # 增加超时时间到300秒（5分钟）
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"API调用失败: {e}")
            return None
    
    def translate_prompt(self, chinese_text):
        """
        翻译中文提示词为英文AI绘画提示词
        
        Args:
            chinese_text: 中文提示词
        
        Returns:
            str: 英文提示词
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的AI绘画提示词翻译助手。将中文提示词翻译成英文，保持绘画风格描述的准确性。只返回翻译结果，不要解释。"
            },
            {
                "role": "user",
                "content": f"将以下中文提示词翻译成英文AI绘画提示词：{chinese_text}"
            }
        ]
        
        return self.chat(messages, model="moonshot-v1-8k")
    
    def process_long_text(self, text, instruction):
        """
        处理超长文本
        
        Args:
            text: 超长文本内容
            instruction: 处理指令
        
        Returns:
            str: 处理结果
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的文本处理助手。"
            },
            {
                "role": "user",
                "content": f"{instruction}\n\n文本内容：\n{text}"
            }
        ]
        
        # 使用128k模型处理超长文本
        return self.chat(messages, model="moonshot-v1-128k")


def main():
    """测试Kimi API"""
    print("=" * 70)
    print("Kimi API 测试")
    print("=" * 70)
    
    try:
        # 初始化
        print("\n[1/3] 初始化API...")
        api = KimiAPI()
        print("✓ API初始化成功")
        
        # 测试连接
        print("\n[2/3] 测试连接...")
        if not api.test_connection():
            return
        
        # 测试翻译
        print("\n[3/3] 测试翻译功能...")
        test_prompts = [
            "一个穿蓝色长袍的老道士，神秘的微笑，中国风，高质量",
            "现代都市街道，黄昏时分，温暖的光线，电影感"
        ]
        
        for prompt in test_prompts:
            print(f"\n中文: {prompt}")
            translated = api.translate_prompt(prompt)
            print(f"英文: {translated}")
        
        print("\n" + "=" * 70)
        print("✓ 测试完成！")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()
