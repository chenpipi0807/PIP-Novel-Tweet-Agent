"""
小说转短剧工具
功能：
1. 按标点符号拆分长文本
2. 为每句生成TTS音频
3. 生成字幕文件（SRT + JSON）
4. 记录时间轴信息
"""
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple
import wave
import logging
from tts_tool import ShortDramaTTS

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class NovelToDrama:
    """小说转短剧工具"""
    
    def __init__(self, timbre_name: str = "抖音-读小说"):
        """
        初始化
        
        Args:
            timbre_name: 默认音色
        """
        self.tts = ShortDramaTTS()
        self.default_timbre = timbre_name
        logger.info(f"✓ 使用默认音色: {timbre_name}")
    
    def split_text(self, text: str, max_length: int = 50) -> List[str]:
        """
        按标点符号拆分文本
        
        Args:
            text: 原始文本
            max_length: 单句最大长度
            
        Returns:
            拆分后的句子列表
        """
        # 清理文本
        text = text.strip().replace('\n', ' ').replace('\r', '')
        
        # 按句号、问号、感叹号拆分
        sentences = re.split(r'([。！？!?])', text)
        
        # 重新组合句子和标点
        result = []
        temp = ""
        for i, part in enumerate(sentences):
            if i % 2 == 0:  # 句子内容
                temp = part
            else:  # 标点符号
                sentence = (temp + part).strip()
                if sentence:
                    # 如果句子太长，按逗号再拆分
                    if len(sentence) > max_length:
                        sub_parts = re.split(r'([，,、；;])', sentence)
                        sub_temp = ""
                        for j, sub_part in enumerate(sub_parts):
                            if j % 2 == 0:
                                sub_temp = sub_part
                            else:
                                sub_sentence = (sub_temp + sub_part).strip()
                                if sub_sentence:
                                    result.append(sub_sentence)
                    else:
                        result.append(sentence)
        
        # 过滤空句子和无效内容
        def is_valid_sentence(s):
            """判断是否为有效句子"""
            if not s or len(s) <= 1:
                return False
            # 移除引号和空格后检查
            cleaned = s.strip('"\'""''「」『』【】《》 \t')
            if not cleaned or len(cleaned) <= 1:
                return False
            # 只包含标点符号的不要
            if all(c in '，。！？,.:;!?、""''"\'「」『』【】《》—…·' for c in cleaned):
                return False
            return True
        
        result = [s for s in result if is_valid_sentence(s)]
        
        logger.info(f"✓ 文本拆分完成: {len(result)} 句")
        return result
    
    def get_audio_duration(self, audio_path: str) -> float:
        """
        获取音频时长（秒）
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            时长（秒）
        """
        try:
            with wave.open(audio_path, 'r') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                return duration
        except Exception as e:
            logger.warning(f"无法读取音频时长: {e}")
            # 估算：假设平均每个字0.3秒
            return 0.0
    
    def generate_audio_files(
        self,
        sentences: List[str],
        output_dir: Path,
        timbre_name: str = None,
        prefix: str = "scene"
    ) -> List[Dict]:
        """
        为每句话生成音频文件
        
        Args:
            sentences: 句子列表
            output_dir: 输出目录
            timbre_name: 音色名称
            prefix: 文件名前缀
            
        Returns:
            包含时间轴信息的列表
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        timbre = timbre_name or self.default_timbre
        
        timeline = []
        current_time = 0.0
        
        logger.info(f"\n开始生成音频文件...")
        logger.info(f"输出目录: {output_dir}")
        logger.info(f"=" * 60)
        
        for i, sentence in enumerate(sentences, 1):
            # 生成文件名
            filename = f"{prefix}_{i:04d}.wav"
            output_path = output_dir / filename
            
            # 显示进度
            logger.info(f"[{i}/{len(sentences)}] {sentence[:30]}...")
            
            # 生成音频
            success = self.tts.synthesize(
                text=sentence,
                timbre_name=timbre,
                output_path=str(output_path)
            )
            
            if not success:
                logger.warning(f"  ✗ 生成失败，跳过")
                continue
            
            # 获取音频时长
            duration = self.get_audio_duration(str(output_path))
            
            # 记录时间轴
            timeline.append({
                "index": i,
                "text": sentence,
                "filename": filename,
                "start_time": round(current_time, 2),
                "end_time": round(current_time + duration, 2),
                "duration": round(duration, 2)
            })
            
            logger.info(f"  ✓ {filename} ({duration:.2f}秒)")
            
            current_time += duration
        
        logger.info(f"=" * 60)
        logger.info(f"✓ 音频生成完成: {len(timeline)}/{len(sentences)} 成功")
        logger.info(f"✓ 总时长: {current_time:.2f} 秒 ({current_time/60:.1f} 分钟)")
        
        return timeline
    
    def generate_srt(self, timeline: List[Dict], output_path: Path):
        """
        生成SRT字幕文件
        
        Args:
            timeline: 时间轴信息
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in timeline:
                # 序号
                f.write(f"{item['index']}\n")
                
                # 时间轴
                start = self._format_srt_time(item['start_time'])
                end = self._format_srt_time(item['end_time'])
                f.write(f"{start} --> {end}\n")
                
                # 字幕内容
                f.write(f"{item['text']}\n")
                f.write("\n")
        
        logger.info(f"✓ SRT字幕已生成: {output_path}")
    
    def _format_srt_time(self, seconds: float) -> str:
        """格式化SRT时间格式 HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def generate_json(self, timeline: List[Dict], output_path: Path):
        """
        生成JSON字幕文件
        
        Args:
            timeline: 时间轴信息
            output_path: 输出文件路径
        """
        data = {
            "total_duration": timeline[-1]['end_time'] if timeline else 0,
            "total_sentences": len(timeline),
            "subtitles": timeline
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ JSON字幕已生成: {output_path}")
    
    def process_novel(
        self,
        text: str,
        project_name: str,
        timbre_name: str = None,
        max_sentence_length: int = 50
    ) -> Path:
        """
        处理完整小说文本
        
        Args:
            text: 小说文本
            project_name: 项目名称
            timbre_name: 音色名称
            max_sentence_length: 单句最大长度
            
        Returns:
            项目目录路径
        """
        logger.info("\n" + "=" * 60)
        logger.info(f"开始处理项目: {project_name}")
        logger.info("=" * 60)
        
        # 创建项目目录
        project_dir = Path("projects") / project_name
        audio_dir = project_dir / "audio"
        
        # 1. 拆分文本
        logger.info("\n步骤 1/4: 拆分文本")
        sentences = self.split_text(text, max_sentence_length)
        logger.info(f"  原文长度: {len(text)} 字")
        logger.info(f"  拆分句数: {len(sentences)} 句")
        
        # 2. 生成音频
        logger.info("\n步骤 2/4: 生成音频文件")
        timeline = self.generate_audio_files(
            sentences=sentences,
            output_dir=audio_dir,
            timbre_name=timbre_name,
            prefix=project_name
        )
        
        # 3. 生成SRT字幕
        logger.info("\n步骤 3/4: 生成SRT字幕")
        srt_path = project_dir / f"{project_name}.srt"
        self.generate_srt(timeline, srt_path)
        
        # 4. 生成JSON字幕
        logger.info("\n步骤 4/4: 生成JSON字幕")
        json_path = project_dir / f"{project_name}.json"
        self.generate_json(timeline, json_path)
        
        # 保存原文
        text_path = project_dir / f"{project_name}_original.txt"
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        logger.info(f"✓ 原文已保存: {text_path}")
        
        # 生成项目信息
        info = {
            "project_name": project_name,
            "timbre": timbre_name or self.default_timbre,
            "total_sentences": len(timeline),
            "total_duration": timeline[-1]['end_time'] if timeline else 0,
            "audio_files": len(timeline),
            "created_at": str(Path.cwd())
        }
        
        info_path = project_dir / "project_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ 项目信息已保存: {info_path}")
        
        # 总结
        logger.info("\n" + "=" * 60)
        logger.info("✓ 项目处理完成！")
        logger.info("=" * 60)
        logger.info(f"\n项目目录: {project_dir.absolute()}")
        logger.info(f"  ├── audio/              # 音频文件 ({len(timeline)} 个)")
        logger.info(f"  ├── {project_name}.srt  # SRT字幕")
        logger.info(f"  ├── {project_name}.json # JSON字幕")
        logger.info(f"  ├── {project_name}_original.txt # 原文")
        logger.info(f"  └── project_info.json   # 项目信息")
        logger.info(f"\n总时长: {timeline[-1]['end_time']:.1f} 秒 ({timeline[-1]['end_time']/60:.1f} 分钟)")
        logger.info("")
        
        return project_dir


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='小说转短剧工具')
    parser.add_argument('--input', '-i', required=True, help='输入文本文件路径')
    parser.add_argument('--project', '-p', required=True, help='项目名称')
    parser.add_argument('--timbre', '-t', default='抖音-读小说', help='音色名称')
    parser.add_argument('--max-length', '-m', type=int, default=50, help='单句最大长度')
    parser.add_argument('--list-timbres', action='store_true', help='列出可用音色')
    
    args = parser.parse_args()
    
    # 列出音色
    if args.list_timbres:
        converter = NovelToDrama()
        timbres = converter.tts.list_timbres()
        print("\n可用音色:")
        for i, timbre in enumerate(timbres, 1):
            print(f"  {i:2d}. {timbre}")
        return
    
    # 读取文本
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 处理
    converter = NovelToDrama(timbre_name=args.timbre)
    converter.process_novel(
        text=text,
        project_name=args.project,
        timbre_name=args.timbre,
        max_sentence_length=args.max_length
    )


if __name__ == '__main__':
    main()
