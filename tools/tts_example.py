"""
IndexTTS 1.5 使用示例
演示如何在短剧生产中使用TTS工具
"""
from tts_tool import ShortDramaTTS
from pathlib import Path

def example_1_simple_synthesis():
    """示例1: 简单的单句合成"""
    print("\n" + "="*60)
    print("示例1: 简单的单句合成")
    print("="*60)
    
    # 初始化TTS工具
    tts = ShortDramaTTS()
    
    # 合成一句话
    text = "大家好，我是短剧配音演员，很高兴为大家服务！"
    timbre = "温柔学姐"  # 使用Timbre文件夹中的音色
    output = "outputs/example1.wav"
    
    # 确保输出文件夹存在
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    
    success = tts.synthesize(text, timbre, output)
    
    if success:
        print(f"✓ 合成成功！输出文件: {output}")
    else:
        print("✗ 合成失败")


def example_2_list_timbres():
    """示例2: 查看所有可用音色"""
    print("\n" + "="*60)
    print("示例2: 查看所有可用音色")
    print("="*60)
    
    tts = ShortDramaTTS()
    
    timbres = tts.list_timbres()
    print(f"\n找到 {len(timbres)} 个可用音色:\n")
    
    for i, timbre in enumerate(timbres[:20], 1):  # 只显示前20个
        print(f"  {i:2d}. {timbre}")
    
    if len(timbres) > 20:
        print(f"  ... 还有 {len(timbres) - 20} 个音色")


def example_3_multiple_characters():
    """示例3: 多角色对话场景"""
    print("\n" + "="*60)
    print("示例3: 多角色对话场景")
    print("="*60)
    
    tts = ShortDramaTTS()
    
    # 定义短剧对话脚本
    dialogue = [
        {
            "character": "男主",
            "timbre": "温润青年",
            "text": "你好，我是李明，很高兴认识你。"
        },
        {
            "character": "女主",
            "timbre": "温柔学姐",
            "text": "你好，我是小雅，也很高兴认识你。"
        },
        {
            "character": "男主",
            "timbre": "温润青年",
            "text": "听说你对人工智能很感兴趣？"
        },
        {
            "character": "女主",
            "timbre": "温柔学姐",
            "text": "是的，我觉得AI技术特别神奇，尤其是语音合成这块。"
        }
    ]
    
    # 逐句合成
    output_dir = Path("outputs/dialogue")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, line in enumerate(dialogue, 1):
        output_file = output_dir / f"line_{i:02d}_{line['character']}.wav"
        
        print(f"\n[{i}/{len(dialogue)}] {line['character']}: {line['text'][:30]}...")
        
        success = tts.synthesize(
            text=line['text'],
            timbre=line['timbre'],
            output_path=str(output_file)
        )
        
        if success:
            print(f"  ✓ 已保存到: {output_file}")
        else:
            print(f"  ✗ 合成失败")


def example_4_batch_synthesis():
    """示例4: 批量合成（适合大量台词）"""
    print("\n" + "="*60)
    print("示例4: 批量合成")
    print("="*60)
    
    tts = ShortDramaTTS()
    
    # 准备批量脚本
    scripts = [
        {
            "text": "第一集：命运的相遇",
            "timbre": "播音中年男",
            "filename": "ep01_title.wav"
        },
        {
            "text": "在一个阳光明媚的早晨，故事开始了。",
            "timbre": "播音中年男",
            "filename": "ep01_narration_01.wav"
        },
        {
            "text": "李明走在熟悉的街道上，心中充满期待。",
            "timbre": "播音中年男",
            "filename": "ep01_narration_02.wav"
        },
        {
            "text": "今天会发生什么呢？",
            "timbre": "温润青年",
            "filename": "ep01_male_01.wav"
        },
        {
            "text": "请问，这里是科技大厦吗？",
            "timbre": "温柔学姐",
            "filename": "ep01_female_01.wav"
        }
    ]
    
    # 批量合成
    output_dir = "outputs/batch"
    success_files = tts.batch_synthesize(scripts, output_dir)
    
    print(f"\n批量合成完成！")
    print(f"成功: {len(success_files)}/{len(scripts)} 个文件")


def example_5_custom_timbre():
    """示例5: 使用自定义音色文件"""
    print("\n" + "="*60)
    print("示例5: 使用自定义音色文件")
    print("="*60)
    
    tts = ShortDramaTTS()
    
    # 使用自定义的音色参考音频（不在Timbre文件夹中）
    custom_audio = "path/to/your/custom_voice.wav"  # 替换为实际路径
    text = "这是使用自定义音色合成的语音。"
    output = "outputs/example5_custom.wav"
    
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    
    # 注意：如果文件不存在，这个示例会失败
    # 这里只是演示用法
    print(f"提示: 请将 {custom_audio} 替换为实际的音频文件路径")
    print("或者直接使用Timbre文件夹中的音色")


def example_6_production_workflow():
    """示例6: 完整的短剧生产工作流"""
    print("\n" + "="*60)
    print("示例6: 完整的短剧生产工作流")
    print("="*60)
    
    tts = ShortDramaTTS()
    
    # 短剧场景配置
    scene_config = {
        "episode": 1,
        "scene": 1,
        "characters": {
            "narrator": "播音中年男",
            "hero": "温润青年",
            "heroine": "温柔学姐",
            "villain": "沉稳高管"
        },
        "lines": [
            {"speaker": "narrator", "text": "第一集第一场：办公室"},
            {"speaker": "hero", "text": "早上好，各位同事！"},
            {"speaker": "heroine", "text": "早上好，李明！今天精神不错啊。"},
            {"speaker": "hero", "text": "是啊，今天有个重要的项目要启动。"},
            {"speaker": "villain", "text": "李明，来我办公室一趟。"},
            {"speaker": "narrator", "text": "李明心中一紧，不知道老板找他有什么事。"}
        ]
    }
    
    # 生成输出文件夹
    output_dir = Path(f"outputs/ep{scene_config['episode']:02d}_scene{scene_config['scene']:02d}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n开始制作: 第{scene_config['episode']}集 第{scene_config['scene']}场")
    print(f"输出目录: {output_dir}\n")
    
    # 逐句合成
    for i, line in enumerate(scene_config['lines'], 1):
        speaker = line['speaker']
        timbre = scene_config['characters'][speaker]
        text = line['text']
        
        output_file = output_dir / f"{i:03d}_{speaker}.wav"
        
        print(f"[{i}/{len(scene_config['lines'])}] {speaker}: {text}")
        
        success = tts.synthesize(text, timbre, str(output_file))
        
        if success:
            print(f"  ✓ {output_file.name}")
        else:
            print(f"  ✗ 失败")
    
    print(f"\n场景制作完成！所有文件保存在: {output_dir}")


def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("IndexTTS 1.5 短剧TTS工具 - 使用示例")
    print("="*60)
    
    examples = [
        ("1", "简单的单句合成", example_1_simple_synthesis),
        ("2", "查看所有可用音色", example_2_list_timbres),
        ("3", "多角色对话场景", example_3_multiple_characters),
        ("4", "批量合成", example_4_batch_synthesis),
        ("5", "使用自定义音色", example_5_custom_timbre),
        ("6", "完整的短剧生产工作流", example_6_production_workflow),
    ]
    
    print("\n请选择要运行的示例:")
    for num, desc, _ in examples:
        print(f"  {num}. {desc}")
    print("  0. 运行所有示例")
    print("  q. 退出")
    
    choice = input("\n请输入选项 (0-6, q): ").strip()
    
    if choice == 'q':
        return
    elif choice == '0':
        for _, _, func in examples:
            try:
                func()
            except Exception as e:
                print(f"\n错误: {e}")
            input("\n按回车继续...")
    else:
        for num, _, func in examples:
            if choice == num:
                try:
                    func()
                except Exception as e:
                    print(f"\n错误: {e}")
                break
        else:
            print("无效的选项")


if __name__ == '__main__':
    main()
