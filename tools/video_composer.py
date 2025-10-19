"""
视频合成模块
将图片、音频、字幕合成为视频，支持随机转场效果
"""
import json
import random
from pathlib import Path
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip, 
    concatenate_videoclips, CompositeAudioClip
)
from moviepy.video.fx import fadein, fadeout, crossfadein, crossfadeout


# 转场效果列表
TRANSITIONS = [
    'fade',      # 淡入淡出
    'crossfade', # 交叉淡化
    'none',      # 无转场
]


def random_transition():
    """随机选择转场效果"""
    return random.choice(TRANSITIONS)


def apply_transition(clip, transition_type, duration=0.5):
    """
    应用转场效果
    
    Args:
        clip: 视频片段
        transition_type: 转场类型
        duration: 转场时长
    
    Returns:
        应用转场后的片段
    """
    if transition_type == 'fade':
        return clip.fadein(duration).fadeout(duration)
    elif transition_type == 'crossfade':
        return clip.crossfadein(duration).crossfadeout(duration)
    else:  # none
        return clip


def compose_video(project_dir, subtitle_file, imgs_dir, audio_dir, output_dir):
    """
    合成视频
    
    Args:
        project_dir: 项目目录
        subtitle_file: 字幕文件路径
        imgs_dir: 图片目录
        audio_dir: 音频目录
        output_dir: 输出目录
    
    Returns:
        生成的视频文件路径
    """
    print("读取字幕文件...")
    with open(subtitle_file, 'r', encoding='utf-8') as f:
        subtitles_data = json.load(f)
    
    subtitles = subtitles_data['subtitles']
    total_duration = subtitles_data['total_duration']
    
    print(f"总句数: {len(subtitles)}")
    print(f"总时长: {total_duration:.2f}秒")
    
    # 创建视频片段列表
    clips = []
    audio_clips = []
    
    imgs_path = Path(imgs_dir)
    audio_path = Path(audio_dir)
    
    print("\n创建视频片段...")
    for i, subtitle in enumerate(subtitles, 1):
        index = subtitle['index']
        start_time = subtitle['start_time']
        end_time = subtitle['end_time']
        duration = subtitle['duration']
        audio_file = subtitle['filename']
        
        # 图片路径
        img_file = imgs_path / f"scene_{index:04d}.png"
        if not img_file.exists():
            print(f"⚠ 图片不存在: {img_file}，跳过")
            continue
        
        # 音频路径
        audio_file_path = audio_path / audio_file
        if not audio_file_path.exists():
            print(f"⚠ 音频不存在: {audio_file_path}，跳过")
            continue
        
        # 创建图片片段
        img_clip = ImageClip(str(img_file)).set_duration(duration)
        
        # 随机选择转场效果
        transition = random_transition()
        img_clip = apply_transition(img_clip, transition, duration=0.3)
        
        # 设置开始时间
        img_clip = img_clip.set_start(start_time)
        
        # 加载音频
        audio_clip = AudioFileClip(str(audio_file_path)).set_start(start_time)
        
        clips.append(img_clip)
        audio_clips.append(audio_clip)
        
        if i % 10 == 0:
            print(f"  已处理 {i}/{len(subtitles)} 个片段")
    
    print(f"✓ 共创建 {len(clips)} 个视频片段")
    
    # 合成视频
    print("\n合成视频...")
    video = CompositeVideoClip(clips, size=(1024, 1024))
    
    # 合成音频
    print("合成音频...")
    audio = CompositeAudioClip(audio_clips)
    video = video.set_audio(audio)
    
    # 设置总时长
    video = video.set_duration(total_duration)
    
    # 输出文件
    output_path = Path(output_dir) / f"{Path(project_dir).name}_final.mp4"
    
    print(f"\n导出视频: {output_path}")
    print("这可能需要几分钟...")
    
    # 导出视频
    video.write_videofile(
        str(output_path),
        fps=24,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        threads=4
    )
    
    print(f"✓ 视频导出完成: {output_path}")
    
    return str(output_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python video_composer.py <项目名称>")
        sys.exit(1)
    
    project_name = sys.argv[1]
    project_dir = f"projects/{project_name}"
    
    compose_video(
        project_dir=project_dir,
        subtitle_file=f"{project_dir}/Audio/Subtitles.json",
        imgs_dir=f"{project_dir}/Imgs",
        audio_dir=f"{project_dir}/Audio",
        output_dir=f"{project_dir}/Videos"
    )
