"""
增强版视频合成模块
支持Ken Burns运镜效果和字幕
"""
import json
import subprocess
import random
from pathlib import Path


# Ken Burns运镜效果配置（扩展版）
CAMERA_EFFECTS = [
    # 基础缩放
    {"name": "zoom_in", "scale_start": "1.0", "scale_end": "1.2", "x_start": "0", "x_end": "0", "y_start": "0", "y_end": "0"},
    {"name": "zoom_out", "scale_start": "1.2", "scale_end": "1.0", "x_start": "0", "x_end": "0", "y_start": "0", "y_end": "0"},
    {"name": "zoom_in_slow", "scale_start": "1.0", "scale_end": "1.15", "x_start": "0", "x_end": "0", "y_start": "0", "y_end": "0"},
    {"name": "zoom_out_slow", "scale_start": "1.15", "scale_end": "1.0", "x_start": "0", "x_end": "0", "y_start": "0", "y_end": "0"},
    
    # 平移
    {"name": "pan_right", "scale_start": "1.1", "scale_end": "1.1", "x_start": "-50", "x_end": "50", "y_start": "0", "y_end": "0"},
    {"name": "pan_left", "scale_start": "1.1", "scale_end": "1.1", "x_start": "50", "x_end": "-50", "y_start": "0", "y_end": "0"},
    {"name": "pan_up", "scale_start": "1.1", "scale_end": "1.1", "x_start": "0", "x_end": "0", "y_start": "50", "y_end": "-50"},
    {"name": "pan_down", "scale_start": "1.1", "scale_end": "1.1", "x_start": "0", "x_end": "0", "y_start": "-50", "y_end": "50"},
    
    # 对角线移动
    {"name": "pan_right_up", "scale_start": "1.1", "scale_end": "1.1", "x_start": "-40", "x_end": "40", "y_start": "40", "y_end": "-40"},
    {"name": "pan_right_down", "scale_start": "1.1", "scale_end": "1.1", "x_start": "-40", "x_end": "40", "y_start": "-40", "y_end": "40"},
    {"name": "pan_left_up", "scale_start": "1.1", "scale_end": "1.1", "x_start": "40", "x_end": "-40", "y_start": "40", "y_end": "-40"},
    {"name": "pan_left_down", "scale_start": "1.1", "scale_end": "1.1", "x_start": "40", "x_end": "-40", "y_start": "-40", "y_end": "40"},
    
    # 缩放+移动组合
    {"name": "zoom_in_up", "scale_start": "1.0", "scale_end": "1.15", "x_start": "0", "x_end": "0", "y_start": "30", "y_end": "-30"},
    {"name": "zoom_in_down", "scale_start": "1.0", "scale_end": "1.15", "x_start": "0", "x_end": "0", "y_start": "-30", "y_end": "30"},
    {"name": "zoom_in_left", "scale_start": "1.0", "scale_end": "1.15", "x_start": "30", "x_end": "-30", "y_start": "0", "y_end": "0"},
    {"name": "zoom_in_right", "scale_start": "1.0", "scale_end": "1.15", "x_start": "-30", "x_end": "30", "y_start": "0", "y_end": "0"},
    {"name": "zoom_out_up", "scale_start": "1.15", "scale_end": "1.0", "x_start": "0", "x_end": "0", "y_start": "30", "y_end": "-30"},
    {"name": "zoom_out_down", "scale_start": "1.15", "scale_end": "1.0", "x_start": "0", "x_end": "0", "y_start": "-30", "y_end": "30"},
    {"name": "zoom_out_left", "scale_start": "1.15", "scale_end": "1.0", "x_start": "30", "x_end": "-30", "y_start": "0", "y_end": "0"},
    {"name": "zoom_out_right", "scale_start": "1.15", "scale_end": "1.0", "x_start": "-30", "x_end": "30", "y_start": "0", "y_end": "0"},
    
    # 静止（第一张图使用）
    {"name": "static", "scale_start": "1.0", "scale_end": "1.0", "x_start": "0", "x_end": "0", "y_start": "0", "y_end": "0"},
]


def random_camera_effect():
    """随机选择运镜效果"""
    return random.choice(CAMERA_EFFECTS)


def split_subtitle_lines(text, max_chars_per_line=22):
    """
    智能分割字幕为多行（平均分配）
    
    Args:
        text: 字幕文本
        max_chars_per_line: 每行最大字符数
    
    Returns:
        list: 分割后的行列表
    """
    # 如果文本长度小于等于最大字符数，直接返回
    if len(text) <= max_chars_per_line:
        return [text]
    
    # 计算需要的行数
    total_len = len(text)
    num_lines = (total_len + max_chars_per_line - 1) // max_chars_per_line
    avg_len = total_len // num_lines
    
    # 按逗号分割成句子
    punctuations = ['，', '。', '！', '？', '、', '；', '：', ',', '.', '!', '?', ';', ':']
    segments = []
    current_seg = ""
    
    for char in text:
        current_seg += char
        if char in punctuations:
            segments.append(current_seg)
            current_seg = ""
    
    if current_seg:
        segments.append(current_seg)
    
    # 如果没有标点符号，按字符平均分割
    if len(segments) <= 1:
        lines = []
        for i in range(0, total_len, avg_len):
            lines.append(text[i:i+avg_len])
        return lines
    
    # 将句子组合成行，尽量平均分配
    lines = []
    current_line = ""
    
    for seg in segments:
        # 如果加上这个句子不超过目标长度，就加上
        if len(current_line) + len(seg) <= avg_len + 5:
            current_line += seg
        else:
            # 否则开始新行
            if current_line:
                lines.append(current_line)
            current_line = seg
    
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
    
    # 智能分割字幕为多行（平均分配，每行最多22字）
    subtitle_lines = split_subtitle_lines(subtitle_text, max_chars_per_line=22)
    
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
    合成带运镜和字幕的视频（支持父子分镜结构）
    
    父分镜：对应图片，播放时长 = 所有子分镜时长之和
    子分镜：对应TTS音频和字幕
    
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
    
    total_duration = subtitles_data['total_duration']
    
    # 判断是新格式还是旧格式
    if 'parent_scenes' in subtitles_data:
        # 新格式：父子分镜结构
        parent_scenes = subtitles_data['parent_scenes']
        print(f"父分镜（图片）: {len(parent_scenes)} 个")
        print(f"子分镜（字幕）: {subtitles_data.get('total_child_scenes', 0)} 个")
    else:
        # 旧格式：兼容处理
        subtitles = subtitles_data.get('subtitles', [])
        print(f"总句数: {len(subtitles)}")
        # 转换为父子格式
        parent_scenes = []
        for sub in subtitles:
            parent_scenes.append({
                'parent_index': sub['index'],
                'text': sub['text'],
                'duration': sub['duration'],
                'children': [{
                    'child_index': sub['index'],
                    'text': sub['text'],
                    'filename': sub['filename'],
                    'duration': sub['duration']
                }]
            })
    
    print(f"总时长: {total_duration:.2f}秒")
    
    imgs_path = Path(imgs_dir)
    audio_path = Path(audio_dir)
    output_path = Path(output_dir)
    
    # 创建临时目录
    temp_dir = output_path / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    # 生成每个父分镜的视频片段
    segment_files = []
    
    print("\n生成视频片段（父子分镜结构）...")
    for i, parent_scene in enumerate(parent_scenes, 1):
        parent_index = parent_scene['parent_index']
        parent_text = parent_scene['text']
        children = parent_scene['children']
        parent_duration = parent_scene['duration']
        
        print(f"\n[{i}/{len(parent_scenes)}] 父分镜 {parent_index}")
        print(f"  文本: {parent_text[:60]}...")
        print(f"  子分镜数: {len(children)}")
        print(f"  总时长: {parent_duration:.2f}秒")
        
        # 图片路径
        img_file = imgs_path / f"scene_{parent_index:04d}.png"
        
        if not img_file.exists():
            print(f"  ⚠ 图片缺失，跳过")
            continue
        
        # 第一张图使用静止效果，其他随机选择
        if i == 1:
            effect = {"name": "static", "scale_start": "1.0", "scale_end": "1.0", "x_start": "0", "x_end": "0", "y_start": "0", "y_end": "0"}
        else:
            effect = random_camera_effect()
        
        print(f"  运镜: {effect['name']}")
        
        # 为每个子分镜生成带字幕的视频片段
        child_segments = []
        
        for j, child in enumerate(children, 1):
            child_index = child['child_index']
            child_text = child['text']
            child_duration = child['duration']
            audio_file = audio_path / child['filename']
            
            if not audio_file.exists():
                print(f"    ⚠ 子分镜 {j} 音频缺失，跳过")
                continue
            
            # 输出子片段
            child_segment_file = temp_dir / f"segment_{parent_index:04d}_{j:02d}.mp4"
            
            print(f"    [{j}/{len(children)}] 子分镜: {child_text[:40]}... ({child_duration:.2f}秒)")
            
            try:
                create_video_with_effects(
                    img_path=img_file,  # 使用父分镜的图片
                    audio_path=audio_file,
                    output_path=child_segment_file,
                    duration=child_duration,
                    subtitle_text=child_text,
                    effect=effect  # 所有子分镜使用相同的运镜效果
                )
                
                child_segments.append(child_segment_file)
                print(f"        ✓ 完成")
                
            except Exception as e:
                print(f"        ❌ 失败: {e}")
                continue
        
        # 如果有子片段，合并它们
        if child_segments:
            if len(child_segments) == 1:
                # 只有一个子片段，直接使用
                segment_files.append(child_segments[0])
            else:
                # 多个子片段，需要合并
                merged_segment = temp_dir / f"segment_{parent_index:04d}_merged.mp4"
                concat_file = temp_dir / f"concat_{parent_index:04d}.txt"
                
                with open(concat_file, 'w', encoding='utf-8') as f:
                    for seg in child_segments:
                        f.write(f"file '{seg.absolute()}'\n")
                
                subprocess.run([
                    'ffmpeg', '-y',
                    '-f', 'concat', '-safe', '0',
                    '-i', str(concat_file),
                    '-c', 'copy',
                    str(merged_segment)
                ], check=True, capture_output=True)
                
                segment_files.append(merged_segment)
                
                # 清理子片段
                for seg in child_segments:
                    seg.unlink()
                concat_file.unlink()
            
            print(f"  ✓ 父分镜 {parent_index} 完成")
        else:
            print(f"  ❌ 父分镜 {parent_index} 没有有效的子片段")
    
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
