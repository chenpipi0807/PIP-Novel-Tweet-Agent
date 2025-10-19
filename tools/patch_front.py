"""
临时补丁：修复front.py中的wetext导入问题
在Python 3.12上pynini无法编译，导致wetext不可用
这个补丁会创建一个简单的normalizer替代品
"""
import sys
from pathlib import Path

# 添加index-tts到路径
PROJECT_ROOT = Path(__file__).parent.parent
INDEX_TTS_DIR = PROJECT_ROOT / "index-tts"
sys.path.insert(0, str(INDEX_TTS_DIR))

# 创建一个简单的Normalizer替代品
class SimpleNormalizer:
    """简单的文本规范化器，不依赖pynini"""
    def __init__(self, **kwargs):
        self.lang = kwargs.get('lang', 'zh')
        print(f"  使用简化版Normalizer ({self.lang})")
    
    def normalize(self, text):
        """基本的文本规范化"""
        # 简单处理，不做复杂的TN转换
        return text

# 在导入front之前，先创建一个假的wetext模块
import types
wetext_module = types.ModuleType('wetext')
wetext_module.Normalizer = SimpleNormalizer
sys.modules['wetext'] = wetext_module

print("✓ wetext补丁已应用")
print("  注意：使用简化版文本规范化，可能影响数字和特殊符号的读音")
