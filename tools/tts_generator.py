"""
TTS音频和字幕生成模块
"""
import sys
import os
import json
import re
from pathlib import Path

# 添加index-tts到路径
PROJECT_ROOT = Path(__file__).parent.parent
INDEX_TTS_DIR = PROJECT_ROOT / "index-tts"
sys.path.insert(0, str(INDEX_TTS_DIR))

# 应用wetext补丁
import patch_front

import torchaudio
torchaudio.set_audio_backend("soundfile")

from indextts.infer import IndexTTS


def split_sentences(text):
    """将文本分割成句子"""
    # 先移除逗号（保留句子完整性）
    text = text.replace('，', ' ').replace(',', ' ')
    
    # 按标点符号分割
    sentences = re.split(r'([。！？\.!?])', text)
    
    # 重新组合句子和标点
    result = []
    for i in range(0, len(sentences)-1, 2):
        sentence = sentences[i].strip()
        punct = sentences[i+1] if i+1 < len(sentences) else ''
        if sentence:
            result.append(sentence + punct)
    
    # 处理最后一个可能没有标点的句子
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        result.append(sentences[-1].strip())
    
    return result


def generate_audio_and_subtitles(text, project_name, timbre_name=None):
    """
    生成音频和字幕文件
    
    Args:
        text: 小说文本
        project_name: 项目名称
        timbre_name: 音色名称（可选）
    
    Returns:
        bool: 是否成功
    """
    # 创建项目目录
    project_dir = PROJECT_ROOT / "projects" / project_name
    audio_dir = project_dir / "Audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # 分割句子
    sentences = split_sentences(text)
    print(f"分割成 {len(sentences)} 个句子")
    
    # 加载TTS模型
    print("加载TTS模型...")
    models_dir = PROJECT_ROOT / "models"
    tts = IndexTTS(
        model_dir=str(models_dir),
        cfg_path=str(models_dir / "config.yaml")
    )
    print("✓ TTS模型加载成功")
    
    # 选择音色
    timbre_dir = PROJECT_ROOT / "Timbre"
    if timbre_name:
        timbre_path = timbre_dir / timbre_name
    else:
        # 使用第一个WAV文件
        wav_files = list(timbre_dir.glob("*.wav")) + list(timbre_dir.glob("*.WAV"))
        if not wav_files:
            print("❌ 没有找到音色文件")
            return False
        timbre_path = wav_files[0]
    
    print(f"使用音色: {timbre_path.name}")
    
    # 生成音频和字幕
    subtitles = []
    current_time = 0.0
    
    for i, sentence in enumerate(sentences, 1):
        print(f"\n[{i}/{len(sentences)}] {sentence}")
        
        # 生成音频
        output_file = audio_dir / f"{project_name}_{i:04d}.wav"
        
        try:
            tts.infer(
                audio_prompt=str(timbre_path),  # 参考音频
                text=sentence,
                output_path=str(output_file)
            )
            
            # 获取音频时长
            import soundfile as sf
            audio_data, sample_rate = sf.read(str(output_file))
            duration = len(audio_data) / sample_rate
            
            # 添加到字幕
            subtitle = {
                "index": i,
                "text": sentence,
                "filename": output_file.name,
                "start_time": current_time,
                "end_time": current_time + duration,
                "duration": duration
            }
            subtitles.append(subtitle)
            
            current_time += duration
            
            print(f"✓ 生成完成，时长: {duration:.2f}秒")
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            continue
    
    # 保存字幕文件
    subtitle_file = audio_dir / "Subtitles.json"
    subtitle_data = {
        "total_duration": current_time,
        "total_sentences": len(subtitles),
        "subtitles": subtitles
    }
    
    with open(subtitle_file, 'w', encoding='utf-8') as f:
        json.dump(subtitle_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 字幕文件已保存: {subtitle_file}")
    print(f"  总句数: {len(subtitles)}")
    print(f"  总时长: {current_time:.2f}秒")
    
    # 卸载模型释放显存
    print("\n释放显存...")
    del tts
    import torch
    import gc
    torch.cuda.empty_cache()
    gc.collect()
    
    return True


if __name__ == "__main__":
    # 测试
    test_text = "深夜，李明独自走在回家的路上。突然，一个穿着破旧风衣的老人拦住了他。"
    generate_audio_and_subtitles(test_text, "test_tts")
