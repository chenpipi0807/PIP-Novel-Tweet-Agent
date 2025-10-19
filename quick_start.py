"""
快速启动脚本
演示如何使用系统
"""
from main import VideoGenerator

def example_1_full_process():
    """示例1：完整流程"""
    print("=" * 70)
    print("示例1：完整流程（从小说到视频）")
    print("=" * 70)
    
    novel_text = """
    下班路上，一个穿蓝色长袍的老道儿叫住我。
    他竟准确说出我毕业院校和工作情况。
    还留下句"先上后下"就走了。
    """
    
    generator = VideoGenerator("demo_project", novel_text)
    generator.run()


def example_2_from_existing():
    """示例2：使用现有字幕文件"""
    print("=" * 70)
    print("示例2：从现有字幕文件生成")
    print("=" * 70)
    
    generator = VideoGenerator("test", "")
    
    # 跳过TTS，直接生成提示词
    print("跳过步骤1（使用现有字幕）")
    
    if generator.step2_generate_prompts():
        if generator.step3_generate_images():
            generator.step4_generate_video()


def example_3_only_images():
    """示例3：只生成图像"""
    print("=" * 70)
    print("示例3：只生成分镜图像")
    print("=" * 70)
    
    generator = VideoGenerator("test", "")
    
    print("跳过步骤1和2（使用现有数据）")
    generator.step3_generate_images()


if __name__ == "__main__":
    import sys
    
    print("\n选择示例:")
    print("1. 完整流程（从小说到视频）")
    print("2. 从现有字幕文件生成")
    print("3. 只生成分镜图像")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        example_1_full_process()
    elif choice == "2":
        example_2_from_existing()
    elif choice == "3":
        example_3_only_images()
    else:
        print("无效选择")
