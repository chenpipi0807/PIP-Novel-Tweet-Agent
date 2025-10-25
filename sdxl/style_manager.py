"""
风格管理器 - 管理风格预设和LoRA配置
"""
import json
from pathlib import Path
from typing import Dict, List, Optional


class StyleManager:
    """风格预设管理器"""
    
    def __init__(self, config_path: str = "config/style_presets.json"):
        """
        初始化风格管理器
        
        Args:
            config_path: 风格配置文件路径
        """
        self.config_path = Path(config_path)
        self.presets = self._load_presets()
        # 支持两个LoRA目录
        self.lora_dirs = [
            Path("sdxl/models/loras"),
            Path("sdxl/models/style_lora")
        ]
    
    def _load_presets(self) -> Dict:
        """加载风格预设配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"风格配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_preset(self, preset_id: str) -> Optional[Dict]:
        """
        获取指定风格预设
        
        Args:
            preset_id: 预设ID
            
        Returns:
            风格预设配置，如果不存在返回None
        """
        # 先在基础预设中查找
        for preset in self.presets.get('style_presets', []):
            if preset['id'] == preset_id:
                return preset
        
        # 再在高级模板中查找
        for template in self.presets.get('advanced_presets', {}).get('templates', []):
            if template['id'] == preset_id:
                return template
        
        return None
    
    def list_presets(self, include_advanced: bool = True) -> List[Dict]:
        """
        列出所有可用的风格预设
        
        Args:
            include_advanced: 是否包含高级模板
            
        Returns:
            风格预设列表
        """
        presets = self.presets.get('style_presets', []).copy()
        
        if include_advanced:
            presets.extend(self.presets.get('advanced_presets', {}).get('templates', []))
        
        return presets
    
    def get_lora_path(self, lora_filename: str) -> Optional[Path]:
        """
        获取LoRA文件的完整路径
        
        Args:
            lora_filename: LoRA文件名（相对路径）
            
        Returns:
            LoRA文件的绝对路径，如果不存在返回None
        """
        if not lora_filename:
            return None
        
        lora_path = Path(lora_filename)
        
        # 如果是绝对路径，直接检查
        if lora_path.is_absolute():
            if lora_path.exists():
                return lora_path
            else:
                print(f"⚠️ LoRA文件不存在: {lora_path}")
                return None
        
        # 相对路径，在多个目录中查找
        for lora_dir in self.lora_dirs:
            full_path = lora_dir / lora_path
            if full_path.exists():
                return full_path
        
        # 都没找到
        print(f"⚠️ LoRA文件不存在: {lora_filename}")
        print(f"   已搜索目录: {[str(d) for d in self.lora_dirs]}")
        return None
    
    def build_prompt(self, preset_id: str, base_prompt: str) -> str:
        """
        构建完整的提示词（包含风格前缀）
        
        Args:
            preset_id: 风格预设ID
            base_prompt: 基础提示词
            
        Returns:
            完整的提示词
        """
        preset = self.get_preset(preset_id)
        
        if not preset:
            print(f"⚠️ 风格预设不存在: {preset_id}，使用默认配置")
            return base_prompt
        
        prefix = preset.get('prompt_prefix', '')
        
        # 组合：风格前缀 + 基础提示词
        if prefix:
            return f"{prefix}, {base_prompt}"
        else:
            return base_prompt
    
    def get_negative_prompt(self, preset_id: str) -> str:
        """
        获取负面提示词
        
        Args:
            preset_id: 风格预设ID
            
        Returns:
            负面提示词
        """
        preset = self.get_preset(preset_id)
        
        if not preset:
            # 默认负面词
            return "bad quality, worst quality, worst detail, sketch, censored, artist name, signature, watermark"
        
        return preset.get('negative_prompt', '')
    
    def get_generation_params(self, preset_id: str) -> Dict:
        """
        获取生成参数（步数、CFG等）
        
        Args:
            preset_id: 风格预设ID
            
        Returns:
            生成参数字典
        """
        preset = self.get_preset(preset_id)
        
        if not preset:
            # 默认参数
            return {
                'steps': 12,
                'cfg_scale': 2.5
            }
        
        return {
            'steps': preset.get('recommended_steps', 12),
            'cfg_scale': preset.get('recommended_cfg', 2.5)
        }
    
    def get_lora_config(self, preset_id: str) -> Optional[Dict]:
        """
        获取LoRA配置
        
        Args:
            preset_id: 风格预设ID
            
        Returns:
            LoRA配置字典，如果不使用LoRA返回None
        """
        preset = self.get_preset(preset_id)
        
        if not preset or not preset.get('lora'):
            return None
        
        lora_path = self.get_lora_path(preset['lora'])
        
        if not lora_path:
            return None
        
        return {
            'path': str(lora_path),
            'weight': preset.get('lora_weight', 0.8)
        }
    
    def print_preset_info(self, preset_id: str):
        """
        打印风格预设信息
        
        Args:
            preset_id: 风格预设ID
        """
        preset = self.get_preset(preset_id)
        
        if not preset:
            print(f"❌ 风格预设不存在: {preset_id}")
            return
        
        print(f"\n{'='*60}")
        print(f"🎨 风格预设: {preset['name']}")
        print(f"{'='*60}")
        print(f"ID: {preset['id']}")
        print(f"描述: {preset['description']}")
        print(f"\n提示词前缀:")
        print(f"  {preset.get('prompt_prefix', 'N/A')}")
        print(f"\n负面提示词:")
        print(f"  {preset.get('negative_prompt', 'N/A')}")
        
        if preset.get('lora'):
            print(f"\nLoRA配置:")
            print(f"  文件: {preset['lora']}")
            print(f"  权重: {preset.get('lora_weight', 0.8)}")
            lora_path = self.get_lora_path(preset['lora'])
            if lora_path:
                print(f"  状态: ✓ 已安装")
            else:
                print(f"  状态: ✗ 未找到")
        else:
            print(f"\nLoRA: 不使用")
        
        print(f"\n推荐参数:")
        print(f"  采样步数: {preset.get('recommended_steps', 12)}")
        print(f"  CFG Scale: {preset.get('recommended_cfg', 2.5)}")
        print(f"{'='*60}\n")


def main():
    """测试和演示"""
    import argparse
    
    parser = argparse.ArgumentParser(description='风格预设管理器')
    parser.add_argument('--list', action='store_true', help='列出所有风格预设')
    parser.add_argument('--info', type=str, help='显示指定风格预设的详细信息')
    parser.add_argument('--test', type=str, help='测试构建提示词')
    
    args = parser.parse_args()
    
    manager = StyleManager()
    
    if args.list:
        print("\n可用的风格预设:\n")
        presets = manager.list_presets()
        
        print("基础风格:")
        for preset in manager.presets.get('style_presets', []):
            lora_status = "✓ LoRA" if preset.get('lora') else ""
            print(f"  [{preset['id']}] {preset['name']} {lora_status}")
            print(f"      {preset['description']}")
        
        print("\n高级模板:")
        for template in manager.presets.get('advanced_presets', {}).get('templates', []):
            lora_status = "✓ LoRA" if template.get('lora') else ""
            print(f"  [{template['id']}] {template['name']} {lora_status}")
            print(f"      {template['description']}")
    
    elif args.info:
        manager.print_preset_info(args.info)
    
    elif args.test:
        base_prompt = "a girl standing in a garden, beautiful flowers, sunny day"
        full_prompt = manager.build_prompt(args.test, base_prompt)
        negative = manager.get_negative_prompt(args.test)
        params = manager.get_generation_params(args.test)
        lora_config = manager.get_lora_config(args.test)
        
        print(f"\n测试风格预设: {args.test}\n")
        print(f"基础提示词:")
        print(f"  {base_prompt}\n")
        print(f"完整提示词:")
        print(f"  {full_prompt}\n")
        print(f"负面提示词:")
        print(f"  {negative}\n")
        print(f"生成参数:")
        print(f"  步数: {params['steps']}")
        print(f"  CFG: {params['cfg_scale']}\n")
        
        if lora_config:
            print(f"LoRA配置:")
            print(f"  路径: {lora_config['path']}")
            print(f"  权重: {lora_config['weight']}\n")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
