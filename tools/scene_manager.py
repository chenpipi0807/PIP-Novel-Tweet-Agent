"""
场景卡管理器
提供场景选择和复用功能
"""
import json
from pathlib import Path
from typing import List, Dict, Optional


class SceneManager:
    """场景卡管理器"""
    
    def __init__(self):
        self.config_file = Path("config/scene_cards.json")
        self.scenes = self._load_scenes()
    
    def _load_scenes(self) -> List[Dict]:
        """加载场景卡"""
        if not self.config_file.exists():
            return []
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('scenes', [])
    
    def get_scene_by_id(self, scene_id: str) -> Optional[Dict]:
        """根据ID获取场景"""
        for scene in self.scenes:
            if scene['id'] == scene_id:
                return scene
        return None
    
    def search_scenes(self, keywords: List[str]) -> List[Dict]:
        """
        根据关键词搜索场景
        
        Args:
            keywords: 关键词列表（如：["室内", "现代"]）
            
        Returns:
            匹配的场景列表
        """
        results = []
        
        for scene in self.scenes:
            # 检查标签匹配
            tags = scene.get('tags', [])
            match_count = sum(1 for keyword in keywords if keyword in tags)
            
            if match_count > 0:
                results.append({
                    'scene': scene,
                    'match_score': match_count
                })
        
        # 按匹配度排序
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return [r['scene'] for r in results]
    
    def suggest_scene(self, subtitle_text: str, previous_scene: Optional[str] = None) -> str:
        """
        根据字幕内容建议场景
        
        Args:
            subtitle_text: 字幕文本
            previous_scene: 上一个场景ID（用于复用）
            
        Returns:
            建议的场景描述
        """
        text_lower = subtitle_text.lower()
        
        # 关键词映射
        keyword_map = {
            # 纯色背景（旁白/心理活动）
            '旁白': 'white_background',
            '心理': 'white_background',
            '想到': 'white_background',
            '回忆': 'dark_background',
            
            # 室内场景
            '厨房': 'kitchen',
            '卧室': 'bedroom',
            '客厅': 'living_room',
            '办公室': 'office',
            '教室': 'classroom',
            '餐厅': 'restaurant',
            '咖啡': 'cafe',
            '书房': 'study_room',
            '医馆': 'clinic_interior',
            '宫殿': 'palace',
            
            # 室外场景
            '街道': 'street',
            '街上': 'street',
            '马路': 'street',
            '公园': 'park',
            '庭院': 'courtyard',
            '森林': 'forest',
            '山': 'mountain',
            '海': 'beach',
            '洞': 'cave',
            '电话亭': 'phone_booth',
            
            # 特殊场景
            '战斗': 'sky_battlefield',
            '打斗': 'sky_battlefield',
            '空中': 'sky_battlefield',
        }
        
        # 检查关键词
        for keyword, scene_id in keyword_map.items():
            if keyword in subtitle_text:
                scene = self.get_scene_by_id(scene_id)
                if scene:
                    return scene['description']
        
        # 如果没有匹配，复用上一个场景
        if previous_scene:
            scene = self.get_scene_by_id(previous_scene)
            if scene:
                return scene['description']
        
        # 默认：白色背景
        return "white background"
    
    def list_all_scenes(self) -> List[Dict]:
        """列出所有场景"""
        return self.scenes
    
    def get_scene_description(self, scene_id: str) -> str:
        """获取场景描述"""
        scene = self.get_scene_by_id(scene_id)
        if scene:
            return scene['description']
        return "white background"


if __name__ == '__main__':
    # 测试
    manager = SceneManager()
    
    print("所有场景:")
    for scene in manager.list_all_scenes():
        print(f"  {scene['id']}: {scene['name']} - {scene['description']}")
    
    print("\n搜索'现代室内'场景:")
    results = manager.search_scenes(['现代', '室内'])
    for scene in results[:5]:
        print(f"  {scene['id']}: {scene['name']}")
    
    print("\n建议场景:")
    print(f"  '林默在厨房做饭' → {manager.suggest_scene('林默在厨房做饭')}")
    print(f"  '他想到了过去' → {manager.suggest_scene('他想到了过去')}")
    print(f"  '两人在街上相遇' → {manager.suggest_scene('两人在街上相遇')}")
