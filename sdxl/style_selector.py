"""
风格选择器 - 根据故事内容自动选择合适的风格LoRA
"""
import random
from pathlib import Path
from typing import Dict, List, Optional
from sdxl.style_manager import StyleManager


class StyleSelector:
    """智能风格选择器"""
    
    def __init__(self):
        self.manager = StyleManager()
        self.presets = self.manager.list_presets(include_advanced=False)
    
    def select_style_for_project(
        self, 
        metadata: Dict,
        mode: str = "auto"
    ) -> str:
        """
        为项目选择风格
        
        Args:
            metadata: 项目元数据（包含story_metadata和global_settings）
            mode: 选择模式
                - "auto": 自动选择（Agent模式）
                - "random": 随机选择（传统模式）
                - "first": 使用第一个风格（默认）
        
        Returns:
            风格预设ID
        """
        if mode == "auto":
            return self._auto_select(metadata)
        elif mode == "random":
            return self._random_select()
        else:
            return self._first_select()
    
    def _auto_select(self, metadata: Dict) -> str:
        """
        Agent模式：根据故事内容智能选择风格
        
        匹配规则：
        1. 检查theme_tags中的关键词
        2. 匹配风格的style_tags
        3. 如果没有匹配，随机选择
        """
        story_meta = metadata.get('story_metadata', {})
        theme_tags = story_meta.get('theme_tags', [])
        genre = story_meta.get('genre', '')
        
        print(f"\n🎨 智能风格选择:")
        print(f"  故事类型: {genre}")
        print(f"  主题标签: {theme_tags}")
        
        # 匹配分数
        scores = {}
        
        for preset in self.presets:
            preset_id = preset['id']
            score = 0
            
            # 检查style_tags匹配
            style_tags = preset.get('style_tags', [])
            if style_tags:
                for tag in theme_tags:
                    if tag in style_tags:
                        score += 10
                        print(f"  ✓ [{preset['name']}] 匹配标签: {tag}")
            
            # 检查描述中的关键词
            description = preset.get('description', '')
            for tag in theme_tags:
                if tag in description:
                    score += 5
            
            # 检查genre匹配
            if genre:
                if genre in description or genre in preset.get('name', ''):
                    score += 3
            
            if score > 0:
                scores[preset_id] = score
        
        # 选择得分最高的
        if scores:
            best_preset = max(scores, key=scores.get)
            preset_name = next(p['name'] for p in self.presets if p['id'] == best_preset)
            print(f"\n  🎯 选择风格: {preset_name} (得分: {scores[best_preset]})")
            return best_preset
        
        # 没有匹配，随机选择
        print(f"\n  ⚠️ 没有匹配的风格，随机选择")
        return self._random_select()
    
    def _random_select(self) -> str:
        """随机选择一个风格"""
        if not self.presets:
            raise ValueError("没有可用的风格预设")
        
        preset = random.choice(self.presets)
        print(f"\n🎲 随机选择风格: {preset['name']}")
        return preset['id']
    
    def _first_select(self) -> str:
        """选择第一个风格（默认风格）"""
        if not self.presets:
            raise ValueError("没有可用的风格预设")
        
        preset = self.presets[0]
        print(f"\n📌 使用默认风格: {preset['name']}")
        return preset['id']
    
    def get_style_info(self, preset_id: str) -> Dict:
        """获取风格详细信息"""
        preset = self.manager.get_preset(preset_id)
        if not preset:
            raise ValueError(f"风格预设不存在: {preset_id}")
        
        return {
            'id': preset_id,
            'name': preset['name'],
            'description': preset['description'],
            'lora': preset.get('lora'),
            'lora_weight': preset.get('lora_weight', 0),
            'prompt_prefix': preset.get('prompt_prefix', ''),
            'negative_prompt': preset.get('negative_prompt', ''),
            'params': {
                'steps': preset.get('recommended_steps', 12),
                'cfg_scale': preset.get('recommended_cfg', 2.5)
            }
        }


def test_selector():
    """测试风格选择器"""
    selector = StyleSelector()
    
    # 测试1: 古风故事
    print("\n" + "="*70)
    print("测试1: 古风故事")
    print("="*70)
    metadata1 = {
        "story_metadata": {
            "title": "宫廷秘史",
            "genre": "古风",
            "theme_tags": ["古风", "女主", "宫廷", "汉服"]
        }
    }
    style1 = selector.select_style_for_project(metadata1, mode="auto")
    info1 = selector.get_style_info(style1)
    print(f"\n选择结果: {info1['name']}")
    
    # 测试2: 现代都市
    print("\n" + "="*70)
    print("测试2: 现代都市")
    print("="*70)
    metadata2 = {
        "story_metadata": {
            "title": "都市爱情",
            "genre": "都市",
            "theme_tags": ["现代", "都市", "清新", "爱情"]
        }
    }
    style2 = selector.select_style_for_project(metadata2, mode="auto")
    info2 = selector.get_style_info(style2)
    print(f"\n选择结果: {info2['name']}")
    
    # 测试3: 随机选择
    print("\n" + "="*70)
    print("测试3: 随机选择")
    print("="*70)
    style3 = selector.select_style_for_project({}, mode="random")
    info3 = selector.get_style_info(style3)
    print(f"\n选择结果: {info3['name']}")


if __name__ == '__main__':
    test_selector()
