"""
IndexTTS 1.5 短剧生产TTS工具
用于短剧视频的语音合成，支持零样本音色克隆
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict
import torch

# 添加index-tts到Python路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
INDEX_TTS_DIR = PROJECT_ROOT / "index-tts"
sys.path.insert(0, str(INDEX_TTS_DIR))

# 应用wetext补丁（Python 3.12兼容性）
import types
wetext_module = types.ModuleType('wetext')
class SimpleNormalizer:
    def __init__(self, **kwargs): pass
    def normalize(self, text): return text
wetext_module.Normalizer = SimpleNormalizer
sys.modules['wetext'] = wetext_module

from indextts.infer import IndexTTS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ShortDramaTTS:
    """短剧TTS工具类"""
    
    def __init__(
        self,
        model_dir: str = None,
        config_path: str = None,
        timbre_dir: str = None,
        use_gpu: bool = True
    ):
        """
        初始化TTS工具
        
        Args:
            model_dir: 模型文件夹路径，默认为 ../models
            config_path: 配置文件路径，默认为 ../models/config.yaml
            timbre_dir: 音色参考音频文件夹，默认为 ../Timbre
            use_gpu: 是否使用GPU加速
        """
        # 设置默认路径
        if model_dir is None:
            model_dir = str(PROJECT_ROOT / "models")
        if config_path is None:
            config_path = str(PROJECT_ROOT / "models" / "config.yaml")
        if timbre_dir is None:
            timbre_dir = str(PROJECT_ROOT / "Timbre")
            
        self.model_dir = Path(model_dir)
        self.config_path = Path(config_path)
        self.timbre_dir = Path(timbre_dir)
        
        # 检查路径
        if not self.model_dir.exists():
            raise FileNotFoundError(f"模型文件夹不存在: {self.model_dir}")
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        if not self.timbre_dir.exists():
            raise FileNotFoundError(f"音色文件夹不存在: {self.timbre_dir}")
        
        # 检查GPU
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        logger.info(f"使用设备: {self.device}")
        if self.device == "cuda":
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        
        # 初始化模型
        logger.info("正在加载IndexTTS 1.5模型...")
        self.tts = IndexTTS(
            model_dir=str(self.model_dir),
            cfg_path=str(self.config_path)
        )
        logger.info("模型加载完成！")
        
        # 获取可用的音色列表
        self.available_timbres = self._scan_timbres()
        logger.info(f"找到 {len(self.available_timbres)} 个可用音色")
    
    def _scan_timbres(self) -> Dict[str, str]:
        """扫描音色文件夹，返回音色名称到文件路径的映射"""
        timbres = {}
        audio_extensions = {'.wav', '.mp3', '.flac', '.WAV', '.MP3', '.FLAC'}
        
        for file_path in self.timbre_dir.iterdir():
            if file_path.suffix in audio_extensions:
                # 使用文件名（不含扩展名）作为音色名称
                timbre_name = file_path.stem
                timbres[timbre_name] = str(file_path)
        
        return timbres
    
    def list_timbres(self) -> List[str]:
        """列出所有可用的音色名称"""
        return sorted(self.available_timbres.keys())
    
    def get_timbre_path(self, timbre_name: str) -> Optional[str]:
        """根据音色名称获取音频文件路径"""
        return self.available_timbres.get(timbre_name)
    
    def synthesize(
        self,
        text: str,
        timbre_name: str,
        output_path: str,
        timbre_audio_path: Optional[str] = None
    ) -> bool:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            timbre_name: 音色名称（从Timbre文件夹中选择）
            output_path: 输出音频文件路径
            timbre_audio_path: 自定义音色参考音频路径（可选，如果提供则忽略timbre_name）
        
        Returns:
            bool: 是否成功
        """
        try:
            # 获取音色参考音频
            if timbre_audio_path:
                voice_path = timbre_audio_path
                logger.info(f"使用自定义音色: {voice_path}")
            else:
                voice_path = self.get_timbre_path(timbre_name)
                if not voice_path:
                    logger.error(f"找不到音色: {timbre_name}")
                    logger.info(f"可用音色: {', '.join(self.list_timbres()[:10])}...")
                    return False
                logger.info(f"使用音色: {timbre_name}")
            
            # 检查音色文件
            if not Path(voice_path).exists():
                logger.error(f"音色文件不存在: {voice_path}")
                return False
            
            # 合成语音
            logger.info(f"正在合成: {text[:50]}...")
            self.tts.infer(
                audio_prompt=voice_path,
                text=text,
                output_path=output_path
            )
            
            logger.info(f"合成完成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"合成失败: {str(e)}", exc_info=True)
            return False
    
    def batch_synthesize(
        self,
        scripts: List[Dict[str, str]],
        output_dir: str
    ) -> List[str]:
        """
        批量合成语音
        
        Args:
            scripts: 脚本列表，每个元素是字典，包含:
                - text: 文本内容
                - timbre: 音色名称
                - filename: 输出文件名（可选）
            output_dir: 输出文件夹路径
        
        Returns:
            List[str]: 成功生成的文件路径列表
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        success_files = []
        
        for i, script in enumerate(scripts):
            text = script.get('text', '')
            timbre = script.get('timbre', '')
            filename = script.get('filename', f'output_{i+1:03d}.wav')
            
            if not text or not timbre:
                logger.warning(f"跳过第 {i+1} 条：缺少文本或音色")
                continue
            
            output_path = str(output_dir / filename)
            
            logger.info(f"[{i+1}/{len(scripts)}] 处理中...")
            if self.synthesize(text, timbre, output_path):
                success_files.append(output_path)
            else:
                logger.warning(f"第 {i+1} 条合成失败")
        
        logger.info(f"批量合成完成: {len(success_files)}/{len(scripts)} 成功")
        return success_files


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IndexTTS 1.5 短剧TTS工具')
    parser.add_argument('--text', type=str, help='要合成的文本')
    parser.add_argument('--timbre', type=str, help='音色名称')
    parser.add_argument('--output', type=str, default='output.wav', help='输出文件路径')
    parser.add_argument('--list-timbres', action='store_true', help='列出所有可用音色')
    parser.add_argument('--batch', type=str, help='批量合成，提供JSON文件路径')
    parser.add_argument('--model-dir', type=str, help='模型文件夹路径')
    parser.add_argument('--timbre-dir', type=str, help='音色文件夹路径')
    parser.add_argument('--no-gpu', action='store_true', help='不使用GPU')
    
    args = parser.parse_args()
    
    # 初始化TTS
    tts = ShortDramaTTS(
        model_dir=args.model_dir,
        timbre_dir=args.timbre_dir,
        use_gpu=not args.no_gpu
    )
    
    # 列出音色
    if args.list_timbres:
        print("\n可用音色列表:")
        print("-" * 50)
        for i, timbre in enumerate(tts.list_timbres(), 1):
            print(f"{i:3d}. {timbre}")
        print("-" * 50)
        print(f"共 {len(tts.list_timbres())} 个音色")
        return
    
    # 批量合成
    if args.batch:
        with open(args.batch, 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        
        output_dir = Path(args.batch).parent / 'outputs'
        tts.batch_synthesize(scripts, str(output_dir))
        return
    
    # 单个合成
    if args.text and args.timbre:
        tts.synthesize(args.text, args.timbre, args.output)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
