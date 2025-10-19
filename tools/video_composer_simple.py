"""
简化的视频合成模块
使用ffmpeg直接合成，不依赖moviepy
"""
import json
import subprocess
from pathlib import Path


def compose_video(project_dir, subtitle_file, imgs_dir, audio_dir, output_dir):
    """
    使用ffmpeg合成视频
    
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
    
    imgs_path = Path(imgs_dir)
    audio_path = Path(audio_dir)
    output_path = Path(output_dir)
    
    # 创建ffmpeg concat文件
    concat_file = output_path / "concat.txt"
    
    print("\n创建视频片段列表...")
    with open(concat_file, 'w', encoding='utf-8') as f:
        for i, subtitle in enumerate(subtitles, 1):
            index = subtitle['index']
            duration = subtitle['duration']
            
            # 图片路径
            img_file = imgs_path / f"scene_{index:04d}.png"
            if not img_file.exists():
                print(f"⚠ 图片不存在: {img_file}，跳过")
                continue
            
            # 写入concat文件
            f.write(f"file '{img_file.absolute()}'\n")
            f.write(f"duration {duration}\n")
        
        # 最后一帧需要重复
        if subtitles:
            last_img = imgs_path / f"scene_{subtitles[-1]['index']:04d}.png"
            f.write(f"file '{last_img.absolute()}'\n")
    
    print(f"✓ 片段列表已创建: {concat_file}")
    
    # 合并所有音频
    print("\n合并音频...")
    audio_list_file = output_path / "audio_list.txt"
    with open(audio_list_file, 'w', encoding='utf-8') as f:
        for subtitle in subtitles:
            audio_file = audio_path / subtitle['filename']
            if audio_file.exists():
                f.write(f"file '{audio_file.absolute()}'\n")
    
    merged_audio = output_path / "merged_audio.wav"
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', str(audio_list_file),
        '-c', 'copy',
        str(merged_audio)
    ], check=True)
    
    print(f"✓ 音频已合并: {merged_audio}")
    
    # 合成最终视频
    print("\n合成最终视频...")
    final_output = output_path / f"{Path(project_dir).name}_final.mp4"
    
    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0', '-i', str(concat_file),  # 图片
        '-i', str(merged_audio),  # 音频
        '-c:v', 'libx264',  # 视频编码
        '-pix_fmt', 'yuv420p',  # 像素格式
        '-c:a', 'aac',  # 音频编码
        '-shortest',  # 以最短流为准
        str(final_output)
    ], check=True)
    
    # 清理临时文件
    concat_file.unlink()
    audio_list_file.unlink()
    merged_audio.unlink()
    
    print(f"\n✓ 视频合成完成: {final_output}")
    
    return str(final_output)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python video_composer_simple.py <项目名称>")
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
