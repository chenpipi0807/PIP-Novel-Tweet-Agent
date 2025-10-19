"""
处理test.txt的示例脚本
"""
from novel_to_drama import NovelToDrama
from pathlib import Path

# 读取test.txt
input_file = Path("../test.txt")
with open(input_file, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"读取文本: {len(text)} 字")
print(f"预览: {text[:100]}...\n")

# 创建转换器
converter = NovelToDrama(timbre_name="播音中年男")

# 处理文本
project_dir = converter.process_novel(
    text=text,
    project_name="test",  # 项目名称
    timbre_name="播音中年男",  # 使用旁白音色
    max_sentence_length=50  # 单句最大50字
)

print(f"\n完成！项目目录: {project_dir.absolute()}")
