"""
增强版视频合成模块
支持Ken Burns运镜效果和字幕
"""
import json
import subprocess
import random
from pathlib import Path


# Ken Burns运镜效果配置
CAMERA_EFFECTS = [
    {
        "name": "zoom_in",
        "scale_start": "1.0",
        "scale_end": "1.2",
        "x_start": "0",
        "x_end": "0",
        "y_start": "0",
        "y_end": "0"
    },
    {
        "name": "zoom_out",
        "scale_start": "1.2",
        "scale_end": "1.0",
        "x_start": "0",
        "x_end": "0",
        "y_start": "0",
        "y_end": "0"
    },
    {
        "name": "pan_right",
        "scale_start": "1.1",
        "scale_end": "1.1",
        "x_start": "-50",
        "x_end": "50",
        "y_start": "0",
        "y_end": "0"
    },
    {
        "name": "pan_left",
        "scale_start": "1.1",
        "scale_end": "1.1",
        "x_start": "50",
        "x_end": "-50",
        "y_start": "0",
        "y_end": "0"
    },
    {
        "name": "pan_up",
        "scale_start": "1.1",
        "scale_end": "1.1",
        "x_start": "0",
        "x_end": "0",
        "y_start": "50",
        "y_end": "-50"
    },
    {
        "name": "pan_down",
        "scale_start": "1.1",
        "scale_end": "1.1",
        "x_start": "0",
        "x_end": "0",
        "y_start": "-50",
        "y_end": "50"
    },
    {
        "name": "zoom_in_up",
        "scale_start": "1.0",
        "scale_end": "1.15",
        "x_start": "0",
        "x_end": "0",
        "y_start": "30",
        "y_end": "-30"
    },
    {
        "name": "zoom_out_down",
        "scale_start": "1.15",
        "scale_end": "1.0",
        "x_start": "0",
        "x_end": "0",
        "y_start": "-30",
        "y_end": "30"
    }
]


def random_camera_effect():
    """随机选择运镜效果"""
    return random.choice(CAMERA_EFFECTS)


def split_subtitle_lines(text, max_chars_per_line=20):
    """
    智能分割字幕为多行
    
    Args:
        text: 字幕文本
        max_chars_per_line: 每行最大字符数
    
    Returns:
        list: 分割后的行列表
    """
    # 如果文本长度小于等于最大字符数，直接返回
    if len(text) <= max_chars_per_line:
        return [text]
    
    lines = []
    current_line = ""
    
    # 按标点符号分割
    for char in text:
        current_line += char
        
        # 如果当前行达到最大长度，或遇到标点符号，考虑换行
        if len(current_line) >= max_chars_per_line:
            # 在标点符号处换行
            if char in ['，', '。', '！', '？', '、', '；', '：', ',', '.', '!', '?', ';', ':']:
                lines.append(current_line)
                current_line = ""
            # 如果超过最大长度，强制换行
            elif len(current_line) > max_chars_per_line + 5:
                lines.append(current_line)
                current_line = ""
    
    # 添加剩余文本
    if current_line:
        lines.append(current_line)
    
    return lines


def create_video_with_effects(img_path, audio_path, output_path, duration, subtitle_text, effect):
    """
    为单个片段创建带运镜和字幕的视频
    
    Args:
        img_path: 图片路径
        audio_path: 音频路径
        output_path: 输出路径
        duration: 时长
        subtitle_text: 字幕文本
        effect: 运镜效果
    """
    # 构建zoompan滤镜（Ken Burns效果）
    fps = 24
    frames = int(duration * fps)
    
    zoompan_filter = (
        f"zoompan="
        f"z='min(zoom+0.0015,{effect['scale_end']})':"
        f"x='iw/2-(iw/zoom/2)+({effect['x_start']}+({effect['x_end']}-({effect['x_start']}))*on/{frames})':"
        f"y='ih/2-(ih/zoom/2)+({effect['y_start']}+({effect['y_end']}-({effect['y_start']}))*on/{frames})':"
        f"d={frames}:"
        f"s=1024x1024:"
        f"fps={fps}"
    )
    
    # 智能分割字幕为多行
    subtitle_lines = split_subtitle_lines(subtitle_text, max_chars_per_line=20)
    
    # 根据行数调整字体大小和位置
    num_lines = len(subtitle_lines)
    
    # 动态字体大小：1行用48，2行用44，3行及以上用40
    if num_lines == 1:
        fontsize = 48
    elif num_lines == 2:
        fontsize = 44
    else:
        fontsize = 40
    
    # 计算总高度（字体大小 * 行数 + 行间距）
    line_spacing = int(fontsize * 0.3)  # 行间距为字体大小的30%
    total_height = fontsize * num_lines + line_spacing * (num_lines - 1)
    
    # 底部边距
    bottom_margin = 80
    
    # 构建多行字幕滤镜
    subtitle_filters = []
    for i, line in enumerate(subtitle_lines):
        # 转义特殊字符（ffmpeg drawtext需要转义的字符）
        escaped_line = line
        # 转义反斜杠
        escaped_line = escaped_line.replace("\\", "\\\\")
        # 转义单引号
        escaped_line = escaped_line.replace("'", "'\\''")
        # 转义冒号
        escaped_line = escaped_line.replace(":", "\\:")
        # 转义百分号
        escaped_line = escaped_line.replace("%", "\\%")
        # 转义方括号
        escaped_line = escaped_line.replace("[", "\\[")
        escaped_line = escaped_line.replace("]", "\\]")
        # 转义引号（中英文）
        escaped_line = escaped_line.replace('"', '\\"')
        escaped_line = escaped_line.replace('"', '\\"')
        escaped_line = escaped_line.replace('"', '\\"')
        escaped_line = escaped_line.replace("'", "\\'")
        escaped_line = escaped_line.replace("'", "\\'")
        # 转义省略号
        escaped_line = escaped_line.replace("……", "...")
        escaped_line = escaped_line.replace("…", "...")
        
        # 计算每行的Y坐标（从下往上）
        y_offset = bottom_margin + (num_lines - 1 - i) * (fontsize + line_spacing)
        
        subtitle_filter = (
            f"drawtext="
            f"text='{escaped_line}':"
            f"fontfile='C\\:/Windows/Fonts/msyhbd.ttc':"  # 微软雅黑粗体
            f"fontsize={fontsize}:"
            f"fontcolor=white:"
            f"borderw=4:"  # 加粗描边
            f"bordercolor=black:"
            f"x=(w-text_w)/2:"  # 水平居中
            f"y=h-{y_offset}"  # 从底部向上偏移
        )
        subtitle_filters.append(subtitle_filter)
    
    # 组合所有滤镜
    video_filter = zoompan_filter
    for subtitle_filter in subtitle_filters:
        video_filter += f",{subtitle_filter}"
    
    # 使用ffmpeg生成视频片段
    cmd = [
        'ffmpeg', '-y',
        '-loop', '1', '-i', str(img_path),  # 循环图片
        '-i', str(audio_path),  # 音频
        '-vf', video_filter,  # 视频滤镜
        '-c:v', 'libx264',  # 视频编码
        '-tune', 'stillimage',  # 优化静态图片
        '-c:a', 'aac',  # 音频编码
        '-b:a', '192k',  # 音频比特率
        '-pix_fmt', 'yuv420p',  # 像素格式
        '-shortest',  # 以最短流为准
        '-t', str(duration),  # 时长
        str(output_path)
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)


def compose_video(project_dir, subtitle_file, imgs_dir, audio_dir, output_dir):
    """
    合成带运镜和字幕的视频
    
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
    
    # 创建临时目录
    temp_dir = output_path / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    # 生成每个片段
    segment_files = []
    
    print("\n生成视频片段（带运镜和字幕）...")
    for i, subtitle in enumerate(subtitles, 1):
        index = subtitle['index']
        duration = subtitle['duration']
        text = subtitle['text']
        
        # 图片和音频路径
        img_file = imgs_path / f"scene_{index:04d}.png"
        audio_file = audio_path / subtitle['filename']
        
        if not img_file.exists() or not audio_file.exists():
            print(f"⚠ [{i}/{len(subtitles)}] 文件缺失，跳过")
            continue
        
        # 随机选择运镜效果
        effect = random_camera_effect()
        
        # 输出片段
        segment_file = temp_dir / f"segment_{index:04d}.mp4"
        
        print(f"[{i}/{len(subtitles)}] 生成片段 {index} - 运镜: {effect['name']}")
        print(f"  字幕: {text}")
        
        try:
            create_video_with_effects(
                img_path=img_file,
                audio_path=audio_file,
                output_path=segment_file,
                duration=duration,
                subtitle_text=text,
                effect=effect
            )
            
            segment_files.append(segment_file)
            print(f"  ✓ 完成")
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            continue
    
    if not segment_files:
        print("❌ 没有生成任何视频片段")
        return None
    
    # 合并所有片段
    print(f"\n合并 {len(segment_files)} 个视频片段...")
    concat_file = temp_dir / "concat.txt"
    
    with open(concat_file, 'w', encoding='utf-8') as f:
        for segment in segment_files:
            f.write(f"file '{segment.absolute()}'\n")
    
    final_output = output_path / f"{Path(project_dir).name}_final.mp4"
    
    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', str(concat_file),
        '-c', 'copy',
        str(final_output)
    ], check=True)
    
    # 清理临时文件
    print("\n清理临时文件...")
    for segment in segment_files:
        segment.unlink()
    concat_file.unlink()
    temp_dir.rmdir()
    
    print(f"\n✓ 视频合成完成: {final_output}")
    print(f"  总时长: {total_duration:.2f}秒")
    print(f"  分辨率: 1024x1024")
    print(f"  包含运镜效果和字幕")
    
    return str(final_output)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python video_composer_enhanced.py <项目名称>")
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
