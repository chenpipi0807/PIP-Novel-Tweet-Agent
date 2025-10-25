"""
Agent 工具箱
将原有功能封装为 Agent 可调用的工具
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional


class AgentTools:
    """Agent 工具集合"""
    
    def __init__(self, video_generator):
        """
        初始化工具
        
        Args:
            video_generator: VideoGenerator 实例
        """
        self.generator = video_generator
        self.llm_client = None  # 将在后面设置
    
    def inspect_and_continue(self, **kwargs) -> Dict[str, Any]:
        """
        工具：检查项目状态并自动继续（一步到位）
        
        Returns:
            项目状态 + 下一步操作 + 自动执行结果
        """
        print("🔍 正在检查项目状态并自动继续...")
        
        try:
            from project_inspector import ProjectInspector
            
            inspector = ProjectInspector(self.generator.project_name)
            report = inspector.inspect()
            report_text = inspector.generate_report_text()
            
            print(report_text)
            
            # 根据检查结果自动执行下一步
            next_action = report['next_action']
            
            result = {
                "status": "success",
                "report": report,
                "steps_completed": report['steps_completed'],
                "next_action": next_action,
                "current_step": report['current_step'],
                "issues": report['issues'],
                "message": f"项目检查完成，已完成{len(report['steps_completed'])}/4步"
            }
            
            # 如果有下一步操作，提示应该执行什么
            if next_action and next_action != "任务已完成":
                action_map = {
                    "generate_audio": "generate_audio",
                    "generate_prompts": "generate_prompts",
                    "generate_images": "generate_images",
                    "continue_generate_images": "generate_images",
                    "generate_video": "compose_video"
                }
                suggested_tool = action_map.get(next_action, next_action)
                result["suggested_next_tool"] = suggested_tool
                result["message"] += f"，建议执行: {suggested_tool}"
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"检查失败: {str(e)}"
            }
    
    def inspect_project(self, **kwargs) -> Dict[str, Any]:
        """
        工具：检查项目状态（会更新Agent的内存状态）
        
        Returns:
            项目状态报告
        """
        print("🔍 正在检查项目状态...")
        
        try:
            from project_inspector import ProjectInspector
            
            inspector = ProjectInspector(self.generator.project_name)
            report = inspector.inspect()
            report_text = inspector.generate_report_text()
            
            print(report_text)
            
            # 关键：将检查结果同步到返回值中，让Agent能够更新内存
            return {
                "status": "success",
                "report": report,
                "report_text": report_text,
                "steps_completed": report['steps_completed'],  # 已完成的步骤
                "next_action": report['next_action'],  # 下一步操作
                "current_step": report['current_step'],  # 当前状态
                "issues": report['issues'],  # 问题列表
                "message": f"项目检查完成，已完成{len(report['steps_completed'])}/4步，下一步: {report['next_action']}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"项目检查失败: {str(e)}"
            }
        
    def regenerate_scene(self, scene_number: int, new_prompt: str = None, **kwargs) -> Dict[str, Any]:
        """
        工具：重新生成指定场景的图像（完整实现）
        
        Args:
            scene_number: 场景编号（从1开始）
            new_prompt: 新的提示词（可选，如果不提供则使用现有提示词）
            
        Returns:
            执行结果
        """
        print(f"🎨 正在重新生成场景 {scene_number}...")
        
        try:
            # 调用独立的单图重生工具
            from agent_tools_single_image import regenerate_single_image_tool
            
            result = regenerate_single_image_tool(
                project_name=self.generator.project_name,
                scene_index=scene_number,
                new_prompt=new_prompt
            )
            
            if result['success']:
                return {
                    "status": "success",
                    "scene_number": scene_number,
                    "message": result['message'],
                    "image_path": result.get('image_path'),
                    "prompt": result.get('prompt')
                }
            else:
                return {
                    "status": "error",
                    "message": result.get('error', '未知错误')
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"重新生成失败: {str(e)}"
            }
    
    def regenerate_scenes_batch(self, scene_numbers: list, **kwargs) -> Dict[str, Any]:
        """
        工具：批量重新生成多个场景
        
        Args:
            scene_numbers: 场景编号列表
            
        Returns:
            执行结果
        """
        print(f"🎨 正在批量重新生成 {len(scene_numbers)} 个场景...")
        
        results = []
        for scene_num in scene_numbers:
            result = self.regenerate_scene(scene_num)
            results.append({
                "scene": scene_num,
                "status": result["status"]
            })
        
        success_count = sum(1 for r in results if r["status"] == "success")
        
        return {
            "status": "success" if success_count == len(scene_numbers) else "partial",
            "total": len(scene_numbers),
            "success": success_count,
            "failed": len(scene_numbers) - success_count,
            "message": f"批量重新生成完成: {success_count}/{len(scene_numbers)} 成功"
        }
    
    def refine_prompts(self, **kwargs) -> Dict[str, Any]:
        """
        工具：自动优化所有提示词（精简长度、检查质量）
        
        Returns:
            优化结果
        """
        print("✨ 正在优化提示词...")
        
        try:
            import json
            from pathlib import Path
            
            prompts_file = self.generator.project_dir / "Prompts.json"
            if not prompts_file.exists():
                return {
                    "status": "error",
                    "message": "提示词文件不存在"
                }
            
            with open(prompts_file, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
            
            scene_prompts = prompts_data.get('scene_prompts', [])
            optimized_count = 0
            issues_fixed = []
            
            for i, scene in enumerate(scene_prompts, 1):
                prompt = scene['prompt']
                original_length = len(prompt.split())
                
                # 检查长度
                if original_length > 60:
                    # 简化提示词：移除冗余词汇
                    prompt = prompt.replace('masterpiece, best quality, highly detailed, anime', '')
                    prompt = prompt.replace('masterpiece, best quality, anime', '')
                    prompt = prompt.replace(', masterpiece, best quality', '')
                    prompt = prompt.replace('highly detailed, ', '')
                    prompt = prompt.replace(', highly detailed', '')
                    prompt = prompt.strip(', ')
                    
                    new_length = len(prompt.split())
                    if new_length < original_length:
                        scene['prompt'] = prompt
                        optimized_count += 1
                        issues_fixed.append(f"场景{i}: {original_length}词 → {new_length}词")
            
            # 保存优化后的提示词
            if optimized_count > 0:
                with open(prompts_file, 'w', encoding='utf-8') as f:
                    json.dump(prompts_data, f, ensure_ascii=False, indent=2)
                
                print(f"✓ 已优化 {optimized_count} 个提示词")
                for issue in issues_fixed:
                    print(f"  • {issue}")
            
            return {
                "status": "success",
                "optimized_count": optimized_count,
                "total_count": len(scene_prompts),
                "issues_fixed": issues_fixed,
                "message": f"提示词优化完成: {optimized_count}/{len(scene_prompts)} 个需要优化"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"优化失败: {str(e)}"
            }
    
    def validate_prompts(self, **kwargs) -> Dict[str, Any]:
        """
        工具：验证提示词质量
        
        Returns:
            验证结果和问题列表
        """
        print("🔍 正在验证提示词质量...")
        
        try:
            import json
            
            prompts_file = self.generator.project_dir / "Prompts.json"
            if not prompts_file.exists():
                return {
                    "status": "error",
                    "message": "提示词文件不存在"
                }
            
            with open(prompts_file, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
            
            scene_prompts = prompts_data.get('scene_prompts', [])
            issues = []
            
            for i, scene in enumerate(scene_prompts, 1):
                prompt = scene['prompt']
                word_count = len(prompt.split())
                
                # 检查长度
                if word_count > 60:
                    issues.append({
                        "scene": i,
                        "type": "too_long",
                        "message": f"场景{i}提示词过长（{word_count}词），建议≤60词"
                    })
                
                # 检查是否包含角色通配符
                if '{' not in prompt and '}' not in prompt:
                    issues.append({
                        "scene": i,
                        "type": "missing_character",
                        "message": f"场景{i}缺少角色通配符"
                    })
                
                # 检查是否有场景
                if 'background' not in prompt.lower() and 'interior' not in prompt and 'street' not in prompt and 'battlefield' not in prompt:
                    issues.append({
                        "scene": i,
                        "type": "missing_scene",
                        "message": f"场景{i}可能缺少场景描述"
                    })
            
            return {
                "status": "success",
                "total_scenes": len(scene_prompts),
                "issues_count": len(issues),
                "issues": issues,
                "message": f"验证完成: 发现 {len(issues)} 个问题"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"验证失败: {str(e)}"
            }
    
    def check_image_quality(self, **kwargs) -> Dict[str, Any]:
        """
        工具：检查所有图像质量
        
        Returns:
            质量检查结果和问题图像列表
        """
        print("🔍 正在检查图像质量...")
        
        try:
            from pathlib import Path
            import json
            
            # 检查图像文件
            image_files = list(self.generator.imgs_dir.glob("scene_*.png"))
            
            # 获取预期数量
            prompts_file = self.generator.project_dir / "Prompts.json"
            expected_count = 0
            if prompts_file.exists():
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    prompts_data = json.load(f)
                    expected_count = len(prompts_data.get('scene_prompts', []))
            
            issues = []
            
            # 检查完整性
            if len(image_files) < expected_count:
                missing = expected_count - len(image_files)
                issues.append({
                    "type": "incomplete",
                    "severity": "high",
                    "message": f"图像不完整：缺少 {missing} 张图像"
                })
            
            # 检查文件大小（太小可能是生成失败）
            for img_file in image_files:
                size_kb = img_file.stat().st_size / 1024
                if size_kb < 100:  # 小于100KB可能有问题
                    scene_num = int(img_file.stem.split('_')[1])
                    issues.append({
                        "type": "small_file",
                        "severity": "medium",
                        "scene": scene_num,
                        "message": f"场景{scene_num}文件过小（{size_kb:.1f}KB），可能生成失败"
                    })
            
            return {
                "status": "success",
                "total_images": len(image_files),
                "expected_images": expected_count,
                "issues_count": len(issues),
                "issues": issues,
                "message": f"质量检查完成: 发现 {len(issues)} 个问题"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"检查失败: {str(e)}"
            }
    
    def auto_fix_issues(self, **kwargs) -> Dict[str, Any]:
        """
        工具：自动修复检测到的问题
        
        Returns:
            修复结果
        """
        print("🔧 正在自动修复问题...")
        
        try:
            # 先检查问题
            check_result = self.check_image_quality()
            
            if check_result["status"] != "success":
                return check_result
            
            issues = check_result.get("issues", [])
            if not issues:
                return {
                    "status": "success",
                    "message": "没有发现需要修复的问题"
                }
            
            fixed_count = 0
            actions = []
            
            for issue in issues:
                if issue["type"] == "incomplete":
                    # 图像不完整，需要重新生成
                    actions.append("需要执行 generate_images 补全图像")
                    fixed_count += 1
                    
                elif issue["type"] == "small_file":
                    # 文件过小，删除并标记重新生成
                    scene_num = issue["scene"]
                    img_file = self.generator.imgs_dir / f"scene_{scene_num:04d}.png"
                    if img_file.exists():
                        img_file.unlink()
                        actions.append(f"已删除问题图像: 场景{scene_num}")
                        fixed_count += 1
            
            return {
                "status": "success",
                "issues_found": len(issues),
                "fixed_count": fixed_count,
                "actions": actions,
                "message": f"自动修复完成: {fixed_count}/{len(issues)} 个问题已处理，请执行 generate_images 重新生成"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"修复失败: {str(e)}"
            }
    
    def change_style(self, new_style_id: str, **kwargs) -> Dict[str, Any]:
        """
        工具：更换整个项目的风格
        
        Args:
            new_style_id: 新风格ID
            
        Returns:
            执行结果
        """
        print(f"🎨 正在切换风格到: {new_style_id}...")
        
        try:
            import json
            from sdxl.style_manager import StyleManager
            
            # 检查风格是否存在
            style_manager = StyleManager()
            if not style_manager.preset_exists(new_style_id):
                available = style_manager.list_presets(include_advanced=False)
                return {
                    "status": "error",
                    "message": f"风格不存在: {new_style_id}",
                    "available_styles": [p['id'] for p in available]
                }
            
            # 更新Prompts.json中的风格
            prompts_file = self.generator.project_dir / "Prompts.json"
            if not prompts_file.exists():
                return {
                    "status": "error",
                    "message": "提示词文件不存在，请先生成提示词"
                }
            
            with open(prompts_file, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
            
            # 更新风格
            if 'story_metadata' not in prompts_data:
                prompts_data['story_metadata'] = {}
            
            old_style = prompts_data['story_metadata'].get('style_preset', '无')
            prompts_data['story_metadata']['style_preset'] = new_style_id
            
            with open(prompts_file, 'w', encoding='utf-8') as f:
                json.dump(prompts_data, f, ensure_ascii=False, indent=2)
            
            # 删除所有旧图像
            deleted_count = 0
            for img_file in self.generator.imgs_dir.glob("scene_*.png"):
                img_file.unlink()
                deleted_count += 1
            
            print(f"✓ 风格已切换: {old_style} → {new_style_id}")
            print(f"✓ 已删除 {deleted_count} 张旧图像")
            
            return {
                "status": "success",
                "old_style": old_style,
                "new_style": new_style_id,
                "deleted_images": deleted_count,
                "message": f"风格已切换到 {new_style_id}，请执行 generate_images 重新生成图像"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"切换失败: {str(e)}"
            }
    
    def set_llm_client(self, llm_client):
        """设置 LLM 客户端"""
        self.llm_client = llm_client
    
    def generate_audio(self, **kwargs) -> Dict[str, Any]:
        """
        工具：生成音频和字幕
        
        Returns:
            执行结果
        """
        print("🎙️ 正在生成音频和字幕...")
        
        try:
            success = self.generator.step1_generate_audio()
            
            if not success:
                return {
                    "status": "error",
                    "message": "音频生成失败"
                }
            
            # 检查字幕文件（兼容新旧格式）
            subtitle_path = self.generator.project_dir / "Audio" / "Subtitles.json"
            if subtitle_path.exists():
                with open(subtitle_path, 'r', encoding='utf-8') as f:
                    subtitles = json.load(f)
                
                # 新格式：parent_scenes
                if 'parent_scenes' in subtitles:
                    parent_count = subtitles.get('total_parent_scenes', 0)
                    child_count = subtitles.get('total_child_scenes', 0)
                    
                    if parent_count == 0:
                        return {
                            "status": "error",
                            "message": "字幕生成失败：父分镜数量为0"
                        }
                    
                    return {
                        "status": "success",
                        "parent_count": parent_count,
                        "child_count": child_count,
                        "message": f"成功生成 {parent_count} 个父分镜（图片），{child_count} 个子分镜（字幕）"
                    }
                else:
                    # 旧格式：subtitles
                    subtitle_count = len(subtitles.get("subtitles", []))
                    
                    if subtitle_count == 0:
                        return {
                            "status": "error",
                            "message": "字幕生成失败：字幕数量为0"
                        }
                    
                    return {
                        "status": "success",
                        "subtitle_count": subtitle_count,
                        "message": f"成功生成 {subtitle_count} 条字幕"
                    }
            else:
                return {
                    "status": "error",
                    "message": "字幕文件不存在"
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"音频生成失败: {str(e)}"
            }
    
    def generate_prompts(self, **kwargs) -> Dict[str, Any]:
        """
        工具：生成图像提示词（Agent模式会智能选择风格）
        
        Returns:
            执行结果
        """
        print("📝 正在生成图像提示词...")
        
        # Agent模式：标记为auto模式，让系统智能选择风格
        kwargs['agent_mode'] = True
        
        try:
            success = self.generator.step2_generate_prompts(agent_mode=True)
            
            if not success:
                return {
                    "status": "error",
                    "message": "提示词生成失败"
                }
            
            # 检查提示词文件
            prompts_path = self.generator.project_dir / "Prompts.json"
            if not prompts_path.exists():
                return {
                    "status": "error",
                    "message": "提示词文件不存在"
                }
            
            with open(prompts_path, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
            
            scene_count = len(prompts_data.get("scene_prompts", []))
            
            if scene_count == 0:
                return {
                    "status": "error",
                    "message": "提示词生成失败：场景数量为0"
                }
            
            return {
                "status": "success",
                "scene_count": scene_count,
                "message": f"成功生成 {scene_count} 个分镜提示词"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"提示词生成失败: {str(e)}"
            }
    
    def generate_images(self, sampling_steps: int = 16, cfg_scale: float = 2.5, 
                       sampler: str = "EulerA", **kwargs) -> Dict[str, Any]:
        """
        工具：生成图像
        
        Args:
            sampling_steps: 采样步数
            cfg_scale: CFG Scale
            sampler: 采样器
            
        Returns:
            执行结果
        """
        print(f"🎨 正在生成图像...")
        print(f"   参数: steps={sampling_steps}, cfg={cfg_scale}, sampler={sampler}")
        
        try:
            success = self.generator.step3_generate_images()
            
            if not success:
                return {
                    "status": "error",
                    "message": "图像生成失败"
                }
            
            # 统计生成的图像
            imgs_dir = self.generator.project_dir / "Imgs"
            if not imgs_dir.exists():
                return {
                    "status": "error",
                    "message": "图像目录不存在"
                }
            
            image_files = list(imgs_dir.glob("scene_*.png"))
            
            if len(image_files) == 0:
                return {
                    "status": "error",
                    "message": "图像生成失败：图像数量为0"
                }
            
            return {
                "status": "success",
                "image_count": len(image_files),
                "message": f"成功生成 {len(image_files)} 张图像"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"图像生成失败: {str(e)}"
            }
    
    def compose_video(self, **kwargs) -> Dict[str, Any]:
        """
        工具：合成视频
        
        Returns:
            执行结果
        """
        print("🎬 正在合成视频...")
        
        try:
            success = self.generator.step4_compose_video()
            
            if not success:
                return {
                    "status": "error",
                    "message": "视频合成失败"
                }
            
            # 查找生成的视频
            videos_dir = self.generator.project_dir / "Videos"
            if not videos_dir.exists():
                return {
                    "status": "error",
                    "message": "视频目录不存在"
                }
            
            video_files = list(videos_dir.glob("*.mp4"))
            if not video_files:
                return {
                    "status": "error",
                    "message": "视频文件不存在"
                }
            
            video_path = str(video_files[0])
            
            return {
                "status": "success",
                "video_path": video_path,
                "message": f"视频合成完成: {video_path}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"视频合成失败: {str(e)}"
            }
    
    def evaluate_quality(self, **kwargs) -> Dict[str, Any]:
        """
        工具：评估生成质量
        
        使用 LLM 评估当前生成结果的质量
        
        Returns:
            质量评估结果
        """
        print("🔍 正在评估质量...")
        
        try:
            # 收集当前状态信息
            project_dir = self.generator.project_dir
            
            # 检查各个步骤的完成情况
            has_audio = (project_dir / "Audio" / "audio.mp3").exists()
            has_subtitles = (project_dir / "Audio" / "Subtitles.json").exists()
            has_prompts = (project_dir / "Prompts.json").exists()
            
            imgs_dir = project_dir / "Imgs"
            image_count = len(list(imgs_dir.glob("scene_*.png"))) if imgs_dir.exists() else 0
            
            videos_dir = project_dir / "Videos"
            has_video = len(list(videos_dir.glob("*.mp4"))) > 0 if videos_dir.exists() else False
            
            # 读取字幕数量
            subtitle_count = 0
            if has_subtitles:
                with open(project_dir / "Audio" / "Subtitles.json", 'r', encoding='utf-8') as f:
                    subtitles = json.load(f)
                    subtitle_count = len(subtitles)
            
            # 读取场景数量
            scene_count = 0
            if has_prompts:
                with open(project_dir / "Prompts.json", 'r', encoding='utf-8') as f:
                    prompts_data = json.load(f)
                    scene_count = len(prompts_data.get("scene_prompts", []))
            
            # 使用 LLM 评估质量
            if self.llm_client:
                evaluation = self._llm_evaluate_quality(
                    has_audio, has_subtitles, has_prompts, 
                    image_count, scene_count, subtitle_count, has_video
                )
            else:
                # 简单评估（无 LLM）
                evaluation = self._simple_evaluate_quality(
                    has_audio, has_subtitles, has_prompts,
                    image_count, scene_count, subtitle_count, has_video
                )
            
            print(f"   总体质量: {evaluation['overall_score']:.2f}")
            print(f"   完整性: {evaluation['completeness']:.2f}")
            
            return evaluation
            
        except Exception as e:
            print(f"⚠️ 质量评估失败: {e}")
            return {
                "status": "error",
                "overall_score": 0.5,
                "completeness": 0.5,
                "issues": [f"评估失败: {str(e)}"],
                "suggestions": ["请检查生成流程"]
            }
    
    def _llm_evaluate_quality(self, has_audio, has_subtitles, has_prompts,
                             image_count, scene_count, subtitle_count, has_video) -> Dict[str, Any]:
        """使用 LLM 评估质量"""
        
        prompt = f"""请评估图像生成质量（0-1分）：

**只关注图像质量，不评估音频！**

当前状态：
- 提示词文件: {"✓" if has_prompts else "✗"} ({scene_count} 个场景)
- 生成图像: {image_count} 张 (预期 {scene_count} 张)
- 最终视频: {"✓" if has_video else "✗"}

评估标准（只看图像）：
1. 图像完整性 (0-1): 图像数量是否匹配场景数量
2. 图像一致性 (0-1): 图像风格是否统一
3. 内容匹配度 (0-1): 图像内容是否匹配对应的字幕和提示词

请以JSON格式回答（只返回JSON）：
{{
    "overall_score": 0.85,
    "completeness": 1.0,
    "consistency": 0.9,
    "quality": 0.8,
    "issues": ["问题描述"],
    "suggestions": ["改进建议"]
}}"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client.chat(messages)
            
            if not response:
                raise Exception("LLM返回为空")
            
            # 提取JSON
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            evaluation = json.loads(response)
            return evaluation
            
        except Exception as e:
            print(f"⚠️ LLM评估失败: {e}")
            # 降级到简单评估
            return self._simple_evaluate_quality(
                has_audio, has_subtitles, has_prompts,
                image_count, scene_count, subtitle_count, has_video
            )
    
    def _simple_evaluate_quality(self, has_audio, has_subtitles, has_prompts,
                                 image_count, scene_count, subtitle_count, has_video) -> Dict[str, Any]:
        """简单质量评估（不使用 LLM）- 只关注图像质量"""
        
        # 计算完整性（只看关键步骤）
        completeness_score = 0.0
        if has_prompts:
            completeness_score += 0.25
        if image_count > 0:
            completeness_score += 0.5  # 图像最重要
        if has_video:
            completeness_score += 0.25
        
        # 计算一致性（图像数量是否匹配场景）
        consistency_score = 1.0
        if scene_count > 0 and image_count != scene_count:
            consistency_score = image_count / scene_count if image_count < scene_count else scene_count / image_count
        
        # 总体分数 - 重点关注图像
        overall_score = (completeness_score * 0.5 + consistency_score * 0.5)
        
        # 发现的问题 - 只关注图像相关
        issues = []
        if not has_prompts:
            issues.append("缺少提示词文件")
        if image_count == 0:
            issues.append("未生成图像")
        elif image_count != scene_count:
            issues.append(f"图像数量({image_count})与场景数量({scene_count})不匹配")
        if not has_video:
            issues.append("未生成最终视频")
        
        # 改进建议
        suggestions = []
        if image_count == 0:
            suggestions.append("需要生成图像")
        elif image_count != scene_count:
            suggestions.append("需要补充缺失的图像")
        elif overall_score < 0.8:
            suggestions.append("建议检查图像质量")
        else:
            suggestions.append("图像生成完整，质量良好")
        
        return {
            "overall_score": overall_score,
            "completeness": completeness_score,
            "consistency": consistency_score,
            "quality": overall_score,
            "issues": issues,
            "suggestions": suggestions
        }
    
    def adjust_parameters(self, evaluation: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        工具：根据评估结果调整参数
        
        Args:
            evaluation: 质量评估结果
            
        Returns:
            新的参数配置
        """
        print("⚙️ 正在调整参数...")
        
        try:
            overall_score = evaluation.get("overall_score", 0.5)
            
            # 使用 LLM 决定参数调整
            if self.llm_client:
                new_params = self._llm_adjust_parameters(evaluation)
            else:
                # 简单规则调整
                new_params = self._simple_adjust_parameters(overall_score)
            
            print(f"   新参数: {json.dumps(new_params, ensure_ascii=False)}")
            
            return new_params
            
        except Exception as e:
            print(f"⚠️ 参数调整失败: {e}")
            return {
                "sampling_steps": 16,
                "cfg_scale": 2.5,
                "sampler": "EulerA"
            }
    
    def _llm_adjust_parameters(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """使用 LLM 调整参数"""
        
        prompt = f"""根据质量评估结果，建议调整生成参数：

评估结果：
{json.dumps(evaluation, ensure_ascii=False, indent=2)}

当前参数：
- 采样步数: 12
- CFG Scale: 2.5
- 采样器: EulerA

参数范围：
- 采样步数: 4-16
- CFG Scale: 1.5-4.0
- 采样器: EulerA, DPM++SDE, DDIM

请建议新的参数配置。以JSON格式回答（只返回JSON）：
{{
    "sampling_steps": 16,
    "cfg_scale": 3.0,
    "sampler": "EulerA",
    "reason": "调整原因"
}}"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client.chat(messages)
            
            if not response:
                raise Exception("LLM返回为空")
            
            # 提取JSON
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            new_params = json.loads(response)
            return new_params
            
        except Exception as e:
            print(f"⚠️ LLM参数调整失败: {e}")
            return self._simple_adjust_parameters(evaluation.get("overall_score", 0.5))
    
    def _simple_adjust_parameters(self, overall_score: float) -> Dict[str, Any]:
        """简单参数调整规则"""
        
        if overall_score < 0.5:
            # 质量很差，大幅调整
            return {
                "sampling_steps": 16,
                "cfg_scale": 3.5,
                "sampler": "EulerA",
                "reason": "质量过低，增加采样步数和CFG"
            }
        elif overall_score < 0.7:
            # 质量一般，微调
            return {
                "sampling_steps": 14,
                "cfg_scale": 3.0,
                "sampler": "EulerA",
                "reason": "质量一般，适度提升参数"
            }
        else:
            # 质量良好，保持
            return {
                "sampling_steps": 16,
                "cfg_scale": 2.5,
                "sampler": "EulerA",
                "reason": "质量良好，保持当前参数"
            }
    
    def get_all_tools(self) -> Dict[str, callable]:
        """获取所有工具的字典"""
        return {
            # 核心工作流工具
            "inspect_and_continue": self.inspect_and_continue,  # 🆕 检查并继续（推荐）
            "inspect_project": self.inspect_project,  # 项目状态检查
            "generate_audio": self.generate_audio,
            "generate_prompts": self.generate_prompts,
            "generate_images": self.generate_images,
            "compose_video": self.compose_video,
            "evaluate_quality": self.evaluate_quality,
            
            # 图像处理工具
            "regenerate_scene": self.regenerate_scene,  # 🆕 重新生成单个场景
            "regenerate_scenes_batch": self.regenerate_scenes_batch,  # 🆕 批量重新生成
            
            # 提示词处理工具
            "refine_prompts": self.refine_prompts,  # 🆕 自动优化提示词
            "validate_prompts": self.validate_prompts,  # 🆕 验证提示词质量
            
            # 质量控制工具
            "check_image_quality": self.check_image_quality,  # 🆕 检查图像质量
            "auto_fix_issues": self.auto_fix_issues,  # 🆕 自动修复问题
            
            # 风格管理工具
            "change_style": self.change_style,  # 🆕 切换风格
            
            # 参数调整工具
            "adjust_parameters": self.adjust_parameters
        }
