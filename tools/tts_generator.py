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


def clean_input_text(text):
    """
    清理用户输入文本（保留基本结构）
    
    移除：
    - 换行符 \\n
    - 特殊符号（除了逗号、句号、问号、感叹号）
    - 多余空格
    
    保留：
    - 逗号、句号、问号、感叹号（用于分割）
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清理后的文本
    """
    # 1. 移除所有换行符（包括转义的和实际的）
    cleaned = text.replace('\\n', '').replace('\n', '')
    
    # 2. 移除Markdown格式符号
    cleaned = cleaned.replace('>', '').replace('#', '').replace('-', '')
    cleaned = cleaned.replace('*', '').replace('_', '').replace('`', '')
    
    # 3. 只保留中文、英文、数字、逗号、句号、问号、感叹号
    # 移除其他所有中文标点符号
    cleaned = re.sub(r'[：；、""''「」『』【】《》—…·（）\(\)]+', '', cleaned)
    
    # 4. 移除多余空格
    cleaned = re.sub(r'\s+', '', cleaned)
    
    return cleaned


def split_parent_scenes(text):
    """
    按句号分割父分镜（用于生成图片）
    
    Returns:
        list: 父分镜列表
    """
    # 按句号分割
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
    
    # 过滤无效句子
    def is_valid_sentence(s):
        """判断是否为有效句子"""
        if not s or len(s) <= 1:
            return False
        cleaned = s.strip('"\'""''「」『』【】《》 \t')
        if not cleaned or len(cleaned) <= 1:
            return False
        if all(c in '，。！？,.:;!?、""''"\'「」『』【】《》—…·' for c in cleaned):
            return False
        return True
    
    result = [s for s in result if is_valid_sentence(s)]
    return result


def split_child_scenes(parent_text):
    """
    按逗号分割子分镜（用于生成TTS和字幕）
    
    Args:
        parent_text: 父分镜文本
        
    Returns:
        list: 子分镜列表
    """
    # 按逗号分割
    parts = re.split(r'([，,])', parent_text)
    
    # 重新组合
    result = []
    for i in range(0, len(parts)-1, 2):
        part = parts[i].strip()
        punct = parts[i+1] if i+1 < len(parts) else ''
        if part:
            result.append(part + punct)
    
    # 处理最后一个没有逗号的部分
    if len(parts) % 2 == 1 and parts[-1].strip():
        result.append(parts[-1].strip())
    
    # 如果没有逗号，返回整个文本
    if len(result) == 0:
        result = [parent_text]
    
    return result


def clean_text_for_tts(text):
    """
    清理文本用于TTS（移除所有特殊符号和Markdown格式）
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清理后的文本
    """
    # 先移除Markdown格式符号
    cleaned = text.replace('\\n', '').replace('\n', '')  # 移除换行符（转义和实际）
    cleaned = cleaned.replace('>', '').replace('#', '').replace('-', '')  # 移除Markdown符号
    cleaned = cleaned.replace('*', '').replace('_', '').replace('`', '')  # 移除其他Markdown符号
    
    # 移除所有标点符号和特殊字符
    cleaned = re.sub(r'[，。！？、；：,.:;!?""''"\'「」『』【】《》—…·\s]+', '', cleaned)
    
    return cleaned


def generate_audio_and_subtitles(text, project_name, timbre_name=None):
    """
    生成音频和字幕文件（父子分镜结构）
    
    父分镜：按句号分割，用于生成图片
    子分镜：按逗号分割，用于生成TTS和字幕
    
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
    
    # 第一步：清理用户输入文本
    print("清理输入文本...")
    text = clean_input_text(text)
    print(f"✓ 文本清理完成，长度: {len(text)} 字符")
    
    # 分割父分镜（按句号）
    parent_scenes = split_parent_scenes(text)
    print(f"分割成 {len(parent_scenes)} 个父分镜（图片）")
    
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
    
    # 生成音频和字幕（父子分镜结构）
    parent_subtitles = []
    child_index = 0  # 子分镜全局索引
    current_time = 0.0
    
    for parent_idx, parent_text in enumerate(parent_scenes, 1):
        print(f"\n{'='*60}")
        print(f"父分镜 {parent_idx}/{len(parent_scenes)}: {parent_text[:50]}...")
        print(f"{'='*60}")
        
        # 分割子分镜（按逗号）
        child_scenes = split_child_scenes(parent_text)
        print(f"  包含 {len(child_scenes)} 个子分镜")
        
        child_subtitles = []
        parent_start_time = current_time
        
        for child_text in child_scenes:
            child_index += 1
            print(f"\n  [{child_index}] 子分镜: {child_text}")
            
            # 清理文本用于TTS（移除所有标点符号）
            tts_text = clean_text_for_tts(child_text)
            print(f"      TTS文本: {tts_text}")
            
            # 生成音频
            output_file = audio_dir / f"{project_name}_{child_index:04d}.wav"
            
            try:
                tts.infer(
                    audio_prompt=str(timbre_path),
                    text=tts_text,  # 使用清理后的文本
                    output_path=str(output_file)
                )
                
                # 获取音频时长
                import soundfile as sf
                audio_data, sample_rate = sf.read(str(output_file))
                duration = len(audio_data) / sample_rate
                
                # 子分镜字幕
                child_subtitle = {
                    "child_index": child_index,
                    "text": child_text,  # 保留原始文本（带标点）用于显示
                    "tts_text": tts_text,  # 清理后的文本
                    "filename": output_file.name,
                    "start_time": current_time,
                    "end_time": current_time + duration,
                    "duration": duration
                }
                child_subtitles.append(child_subtitle)
                
                current_time += duration
                
                print(f"      ✓ 生成完成，时长: {duration:.2f}秒")
                
            except Exception as e:
                print(f"      ❌ 生成失败: {e}")
                continue
        
        # 父分镜信息
        parent_duration = current_time - parent_start_time
        parent_subtitle = {
            "parent_index": parent_idx,
            "text": parent_text,
            "start_time": parent_start_time,
            "end_time": current_time,
            "duration": parent_duration,
            "children": child_subtitles
        }
        parent_subtitles.append(parent_subtitle)
        
        print(f"\n  父分镜 {parent_idx} 完成，总时长: {parent_duration:.2f}秒")
    
    # 保存字幕文件（父子分镜结构）
    subtitle_file = audio_dir / "Subtitles.json"
    
    # 统计子分镜总数
    total_children = sum(len(p['children']) for p in parent_subtitles)
    
    subtitle_data = {
        "total_duration": current_time,
        "total_parent_scenes": len(parent_subtitles),
        "total_child_scenes": total_children,
        "parent_scenes": parent_subtitles
    }
    
    with open(subtitle_file, 'w', encoding='utf-8') as f:
        json.dump(subtitle_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 字幕文件已保存: {subtitle_file}")
    print(f"  父分镜（图片）: {len(parent_subtitles)} 个")
    print(f"  子分镜（字幕）: {total_children} 个")
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
