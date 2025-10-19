"""
测试完整流程
使用现有的test项目数据
"""
from main import VideoGenerator

# 使用test项目（已有字幕文件）
project_name = "test"

# 创建生成器
generator = VideoGenerator(project_name, "")

print("跳过步骤1（已有字幕文件）")
print("跳过步骤2（已有提示词文件）")

# 从步骤3开始：生成图像
if generator.step3_generate_images():
    # 步骤4：合成视频
    generator.step4_generate_video()
