"""
小说字幕转AI绘画提示词生成模块
使用Kimi API将小说字幕转换为SDXL格式的提示词
采用两阶段批次生成策略
"""
import json
from pathlib import Path
from kimi_api import KimiAPI
import asyncio
from concurrent.futures import ThreadPoolExecutor


class PromptGenerator:
    def __init__(self, project_name, agent_mode=False):
        self.project_name = project_name
        self.project_dir = Path("projects") / project_name
        self.audio_dir = self.project_dir / "Audio"
        self.subtitle_file = self.audio_dir / "Subtitles.json"
        self.prompts_file = self.project_dir / "Prompts.json"
        self.agent_mode = agent_mode  # Agent模式标记
        
        # 加载两个PE
        self.pe_metadata = Path("PE") / "novel_to_prompts_metadata.txt"
        self.pe_batch = Path("PE") / "novel_to_prompts_batch.txt"
        
        with open(self.pe_metadata, 'r', encoding='utf-8') as f:
            self.system_prompt_metadata = f.read()
        
        with open(self.pe_batch, 'r', encoding='utf-8') as f:
            self.system_prompt_batch = f.read()
    
    def generate_metadata(self, subtitles_data):
        """
        阶段1: 生成全局元数据（角色、风格等）
        """
        print("\n[阶段1] 生成全局元数据...")
        
        # 提取所有父分镜文本（如果是新格式）
        if 'parent_scenes' in subtitles_data:
            all_text = "\n".join([scene['text'] for scene in subtitles_data['parent_scenes']])
        else:
            # 兼容旧格式
            all_text = "\n".join([sub['text'] for sub in subtitles_data.get('subtitles', [])])
        
        api = KimiAPI()
        
        # 将PE作为参考，而不是严格的system prompt
        user_content = f"""参考以下指导（可灵活调整）：

{self.system_prompt_metadata}

---

小说内容：

{all_text}"""
        
        messages = [
            {"role": "user", "content": user_content}
        ]
        
        response = api.chat(messages, model="moonshot-v1-128k", temperature=0.5)
        
        if not response:
            raise Exception("元数据生成失败")
        
        # 解析JSON
        json_str = response
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        
        metadata = json.loads(json_str.strip())
        print(f"✓ 元数据生成完成")
        print(f"  主题标签: {metadata['story_metadata'].get('theme_tags', [])}")
        print(f"  角色数: {len(metadata['global_settings']['characters'])}")
        
        return metadata
    
    def generate_batch_prompts(self, metadata, subtitles_batch, start_index, max_retries=5):
        """
        阶段2: 批次生成提示词（带重试机制）
        """
        api = KimiAPI()
        expected_count = len(subtitles_batch)
        
        # 构建消息（不包含风格信息，风格由LoRA控制）
        global_info = f"""
角色设定：
"""
        for char in metadata['global_settings']['characters']:
            global_info += f"- {char['name']}: {char['appearance']}, {char['clothing']}\n"
        
        # 添加故事信息（如果有）
        if 'story_metadata' in metadata:
            story = metadata['story_metadata']
            global_info += f"\n故事类型: {story.get('genre', '未知')}\n"
        
        subtitles_text = "\n".join([f"{i+1}. {sub['text']}" for i, sub in enumerate(subtitles_batch)])
        
        for retry in range(max_retries):
            try:
                # 将PE作为参考，而不是严格的system prompt
                user_content = f"""参考以下指导（可灵活调整）：

{self.system_prompt_batch}

---

{global_info}

请为以下{expected_count}个字幕生成提示词（必须生成{expected_count}个）：

{subtitles_text}"""
                
                messages = [
                    {"role": "user", "content": user_content}
                ]
                
                # 使用32k模型，更稳定，并限制输出长度
                response = api.chat(
                    messages, 
                    model="moonshot-v1-32k", 
                    temperature=0.5,  # 提高灵活性
                    max_tokens=4000  # 限制输出，防止截断
                )
                
                if not response:
                    if retry < max_retries - 1:
                        print(f"  ⚠ 第{retry+1}次尝试失败，重试中...")
                        continue
                    return None
                
                # 解析JSON
                json_str = response
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                
                batch_result = json.loads(json_str.strip())
                prompts = batch_result.get('scene_prompts', [])
                
                # 验证数量
                if len(prompts) < expected_count:
                    if retry < max_retries - 1:
                        print(f"  ⚠ 返回{len(prompts)}个，期望{expected_count}个，第{retry+1}次重试...")
                        continue
                    else:
                        print(f"  ⚠ 最终只返回{len(prompts)}/{expected_count}个提示词")
                
                return prompts
                
            except Exception as e:
                if retry < max_retries - 1:
                    print(f"  ⚠ 解析失败: {e}，第{retry+1}次重试...")
                    continue
                else:
                    print(f"  ❌ 解析失败: {e}")
                    return None
        
        return None
    
    def generate_prompts(self, subtitle_file):
        """
        两阶段生成提示词（并发版本）
        只为父分镜生成提示词（用于生成图片）
        """
        # 读取字幕
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            subtitles_data = json.load(f)
        
        # 判断是新格式还是旧格式
        if 'parent_scenes' in subtitles_data:
            # 新格式：只为父分镜生成提示词
            parent_scenes = subtitles_data['parent_scenes']
            total = len(parent_scenes)
            print(f"\n总父分镜数（图片）: {total}")
            print(f"总子分镜数（字幕）: {subtitles_data.get('total_child_scenes', 0)}")
            
            # 转换为统一格式供后续处理
            subtitles = []
            for scene in parent_scenes:
                subtitles.append({
                    'index': scene['parent_index'],
                    'text': scene['text']
                })
        else:
            # 旧格式：兼容处理
            subtitles = subtitles_data.get('subtitles', [])
            total = len(subtitles)
            print(f"\n总字幕数: {total}")
        
        print("采用两阶段并发生成策略")
        
        # 阶段1: 生成元数据
        metadata = self.generate_metadata(subtitles_data)
        
        # 阶段2: 并发批次生成（每批5个，提高稳定性）
        batch_size = 5
        batches = []
        
        # 准备所有批次
        for i in range(0, total, batch_size):
            batch = subtitles[i:i+batch_size]
            batches.append((metadata, batch, i+1, i // batch_size + 1))
        
        total_batches = len(batches)
        print(f"\n[阶段2] 并发生成提示词（{total_batches}个批次，每批{batch_size}个）...")
        
        # 使用线程池并发执行
        all_prompts = [None] * total_batches
        
        def process_batch(args):
            metadata, batch, start_index, batch_num = args
            try:
                print(f"\n批次 {batch_num}/{total_batches}: 第{start_index}-{start_index+len(batch)-1}个分镜 [开始]")
                prompts = self.generate_batch_prompts(metadata, batch, start_index)
                if prompts:
                    print(f"✓ 批次{batch_num}完成，已生成{len(prompts)}个提示词")
                    return (batch_num - 1, prompts)
                else:
                    print(f"❌ 批次{batch_num}失败")
                    return (batch_num - 1, [])
            except Exception as e:
                print(f"❌ 批次{batch_num}出错: {e}")
                return (batch_num - 1, [])
        
        # 并发执行（最多5个并发）
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(process_batch, batches)
            
            for batch_idx, prompts in results:
                all_prompts[batch_idx] = prompts
        
        # 合并结果（按顺序）并重新生成正确的index
        final_prompts = []
        current_index = 1
        
        # 构建角色通配符映射
        character_map = {}
        for char in metadata['global_settings']['characters']:
            name = char['name']
            full_desc = f"{char['appearance']}, {char['clothing']}"
            character_map[f"{{{name}}}"] = full_desc
        
        for prompts in all_prompts:
            if prompts:
                for prompt in prompts:
                    # 替换角色通配符
                    prompt_text = prompt['prompt']
                    for placeholder, full_desc in character_map.items():
                        prompt_text = prompt_text.replace(placeholder, full_desc)
                    
                    # 重新设置index，确保连续
                    prompt['index'] = current_index
                    prompt['prompt'] = prompt_text
                    final_prompts.append(prompt)
                    current_index += 1
        
        # 检查是否有缺失的分镜
        if len(final_prompts) < total:
            print(f"\n⚠ 警告：只生成了{len(final_prompts)}/{total}个提示词，缺失{total - len(final_prompts)}个")
            print("正在补全缺失的分镜...")
            
            # 找出缺失的index
            existing_indices = set(range(1, len(final_prompts) + 1))
            missing_indices = set(range(1, total + 1)) - existing_indices
            
            # 为缺失的分镜生成简单提示词
            for idx in sorted(missing_indices):
                subtitle = subtitles[idx - 1]
                simple_prompt = {
                    "index": idx,
                    "prompt": f"{metadata['global_settings']['characters'][0]['appearance']}, {metadata['global_settings']['characters'][0]['clothing']}, {metadata['global_settings']['art_style']}, masterpiece, best quality, highly detailed, anime"
                }
                final_prompts.insert(idx - 1, simple_prompt)
                print(f"  补全分镜 {idx}")
            
            # 重新排序
            final_prompts.sort(key=lambda x: x['index'])
        
        result = {
            "story_metadata": metadata['story_metadata'],
            "global_settings": metadata['global_settings'],
            "scene_prompts": final_prompts
        }
        
        print(f"\n✓ 全部完成！共生成{len(final_prompts)}/{total}个提示词")
        
        return result
    
    def save_prompts(self, prompts, output_file):
        """保存提示词到文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 提示词已保存: {output_file}")
    
    def print_summary(self, prompts):
        """打印提示词摘要"""
        print("\n" + "=" * 70)
        print("提示词生成摘要")
        print("=" * 70)
        
        metadata = prompts.get('story_metadata', {})
        print(f"\n故事信息:")
        print(f"  标题: {metadata.get('title', 'N/A')}")
        print(f"  类型: {metadata.get('genre', 'N/A')}")
        print(f"  风格: {metadata.get('style', 'N/A')}")
        
        global_settings = prompts.get('global_settings', {})
        characters = global_settings.get('characters', [])
        print(f"\n角色数量: {len(characters)}")
        for char in characters:
            print(f"  - {char.get('name', 'N/A')}: {char.get('appearance', 'N/A')}")
        
        scenes = prompts.get('scene_prompts', [])
        print(f"\n分镜数量: {len(scenes)}")
        
        # 显示前3个示例
        print(f"\n前3个分镜示例:")
        for scene in scenes[:3]:
            subtitle = scene.get('subtitle_text', '')
            prompt = scene.get('prompt', 'N/A')
            print(f"\n  [{scene.get('index')}] {subtitle}")
            print(f"  提示词: {prompt[:80]}..." if len(prompt) > 80 else f"  提示词: {prompt}")
        
        print("\n" + "=" * 70)


def main():
    """主函数"""
    import sys
    
    print("=" * 70)
    print("小说字幕 -> AI绘画提示词生成器")
    print("=" * 70)
    
    # 检查参数
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print("  python generate_prompts.py <字幕文件路径> [输出文件路径]")
        print("\n示例:")
        print("  python generate_prompts.py projects/test/test.json")
        print("  python generate_prompts.py projects/test/test.json projects/test/prompts.json")
        return
    
    subtitle_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 自动生成输出文件名
    if not output_file:
        subtitle_path = Path(subtitle_file)
        output_file = subtitle_path.parent / f"{subtitle_path.stem}_prompts.json"
    
    try:
        # 生成提示词
        generator = PromptGenerator()
        prompts = generator.generate_prompts(subtitle_file)
        
        # 保存结果
        generator.save_prompts(prompts, output_file)
        
        # 打印摘要
        generator.print_summary(prompts)
        
        print(f"\n✓ 完成！输出文件: {output_file}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
