"""
短剧AI生成系统 - 主控制流程
从小说文本到完整视频的自动化生成

支持两种模式：
1. 传统模式 (Workflow) - 按固定流程执行
2. Agent模式 (Agent) - 智能决策和质量控制
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加tools目录到路径
sys.path.append(str(Path(__file__).parent / "tools"))

from generate_prompts import PromptGenerator
from kimi_api import KimiAPI

# Agent相关导入
from agent import NovelToVideoAgent
from agent_tools import AgentTools


class VideoGenerator:
    def __init__(self, project_name, novel_text, timbre=None):
        """
        初始化视频生成器
        
        Args:
            project_name: 项目名称
            novel_text: 小说文本
            timbre: 音色文件名（可选）
        """
        self.project_name = project_name
        self.novel_text = novel_text
        self.timbre = timbre
        
        # 创建项目目录结构
        self.project_dir = Path("projects") / project_name
        self.audio_dir = self.project_dir / "Audio"
        self.imgs_dir = self.project_dir / "Imgs"
        self.videos_dir = self.project_dir / "Videos"
        
        # 创建所有必要目录
        for dir_path in [self.audio_dir, self.imgs_dir, self.videos_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 文件路径
        self.subtitle_file = self.audio_dir / "Subtitles.json"
        self.prompts_file = self.project_dir / "Prompts.json"
        
        print(f"✓ 项目初始化: {project_name}")
        print(f"  项目目录: {self.project_dir}")
    
    # Agent调用的简化方法名
    def step1_generate_audio(self, skip_if_exists=True):
        """步骤1: 生成音频（Agent调用）"""
        return self.step1_generate_audio_and_subtitles(skip_if_exists)
    
    def step3_generate_images(self, skip_if_exists=True):
        """步骤3: 生成图像（Agent调用）"""
        return self.step3_generate_images_batch(skip_if_exists)
    
    def step4_compose_video(self, skip_if_exists=True):
        """步骤4: 合成视频（Agent调用）"""
        return self.step4_generate_video()
    
    def step1_generate_audio_and_subtitles(self, skip_if_exists=True):
        """
        步骤1: 生成音频和字幕文件
        调用TTS系统生成音频和字幕
        
        Args:
            skip_if_exists: 如果字幕文件已存在则跳过
        """
        print("\n" + "=" * 70)
        print("步骤 1/5: 生成音频和字幕")
        print("=" * 70)
        
        # 检查是否已完成
        if skip_if_exists and self.subtitle_file.exists():
            print(f"✓ 字幕文件已存在，跳过此步骤")
            print(f"  文件: {self.subtitle_file}")
            return True
        
        # 导入TTS模块
        try:
            from tts_generator import generate_audio_and_subtitles
            
            # 调用TTS生成
            result = generate_audio_and_subtitles(
                text=self.novel_text,
                project_name=self.project_name,
                timbre_name=self.timbre
            )
            
            if result and self.subtitle_file.exists():
                print(f"✓ 字幕文件已生成: {self.subtitle_file}")
                
                # 读取字幕统计信息（兼容新旧格式）
                with open(self.subtitle_file, 'r', encoding='utf-8') as f:
                    subtitles = json.load(f)
                    # 新格式：parent_scenes + child_scenes
                    if 'parent_scenes' in subtitles:
                        total_scenes = subtitles.get('total_parent_scenes', 0)
                        total_children = subtitles.get('total_child_scenes', 0)
                        print(f"  父分镜（图片）: {total_scenes} 个")
                        print(f"  子分镜（字幕）: {total_children} 个")
                    else:
                        # 旧格式：subtitles
                        print(f"  总句数: {subtitles.get('total_sentences', 0)}")
                    print(f"  总时长: {subtitles.get('total_duration', 0):.2f}秒")
                
                return True
            else:
                print("❌ 字幕文件生成失败")
                return False
                
        except Exception as e:
            print(f"❌ 步骤1失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step2_generate_prompts(self, skip_if_exists=True, agent_mode=False):
        """
        步骤2: 生成AI绘画提示词
        调用Kimi API处理字幕文件
        
        Args:
            skip_if_exists: 如果提示词文件已存在则跳过
        """
        print("\n" + "=" * 70)
        print("步骤 2/5: 生成AI绘画提示词")
        print("=" * 70)
        
        # 检查是否已完成
        if skip_if_exists and self.prompts_file.exists():
            print(f"✓ 提示词文件已存在，跳过此步骤")
            print(f"  文件: {self.prompts_file}")
            return True
        
        if not self.subtitle_file.exists():
            print(f"❌ 字幕文件不存在: {self.subtitle_file}")
            return False
        
        try:
            # 使用PromptGenerator（传递agent_mode）
            generator = PromptGenerator(self.project_name, agent_mode=agent_mode)
            prompts = generator.generate_prompts(str(self.subtitle_file))
            
            # 保存到项目目录
            generator.save_prompts(prompts, str(self.prompts_file))
            
            # 打印摘要
            generator.print_summary(prompts)
            
            return True
            
        except Exception as e:
            print(f"❌ 步骤2失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step3_generate_images(self, skip_if_exists=True):
        """
        步骤3: 生成分镜图像
        调用SDXL生成所有分镜图片
        
        Args:
            skip_if_exists: 如果图片已存在则跳过
        """
        print("\n" + "=" * 70)
        print("步骤 3/5: 生成分镜图像")
        print("=" * 70)
        
        if not self.prompts_file.exists():
            print(f"❌ 提示词文件不存在: {self.prompts_file}")
            return False
        
        try:
            # 清理显存（确保TTS模型已卸载）
            import torch
            import gc
            
            print("清理显存...")
            torch.cuda.empty_cache()
            gc.collect()
            
            # 读取提示词
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
            
            scene_prompts = prompts_data.get('scene_prompts', [])
            total = len(scene_prompts)
            
            # 检查已生成的图像
            existing_images = list(self.imgs_dir.glob("scene_*.png"))
            if skip_if_exists and len(existing_images) == total:
                print(f"✓ 所有图像已存在（{total}张），跳过此步骤")
                return True
            
            print(f"需要生成 {total} 张图像")
            if existing_images:
                print(f"  已存在 {len(existing_images)} 张，将跳过")
            
            print("加载SDXL模型...")
            
            # 导入SDXL生成模块
            from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler
            from pathlib import Path
            
            # 加载模型 - 仅使用 Prefect Illustrious XL 40
            model_dir = Path("sdxl/models/prefectIllustriousXL_40")
            model_path_file = model_dir / "prefectIllustriousXL_40.safetensors"
            if not model_path_file.exists():
                raise FileNotFoundError("未找到模型: sdxl/models/prefectIllustriousXL_40/prefectIllustriousXL_40.safetensors")
            print("✓ 使用模型: Prefect Illustrious XL 40")
            model_path = str(model_path_file)
            config_path = str(model_dir)
            
            pipe = StableDiffusionXLPipeline.from_single_file(
                model_path,
                torch_dtype=torch.float16,
                config=config_path,
                local_files_only=True
            ).to("cuda")
            
            # 加载LoRA（仅DMD2加速）
            dmd2_lora_path = Path("sdxl/models/loras/dmd2_sdxl_4step_lora.safetensors")
            use_dmd2 = False
            if dmd2_lora_path.exists():
                pipe.load_lora_weights(
                    str(dmd2_lora_path.parent), 
                    weight_name=dmd2_lora_path.name,
                    adapter_name="dmd2"
                )
                pipe.set_adapters(["dmd2"], adapter_weights=[0.8])
                use_dmd2 = True
                print("✓ DMD2加速LoRA已加载（权重0.8）")
            
            # 使用Euler Ancestral调度器（原始配置）
            pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
                pipe.scheduler.config
            )
            print("✓ 使用调度器: Euler Ancestral")
            
            pipe.enable_attention_slicing()
            pipe.enable_vae_slicing()
            
            print("✓ 模型加载完成")
            
            # 生成图像
            for i, scene in enumerate(scene_prompts, 1):
                index = scene['index']
                prompt = scene['prompt']
                
                # 检查是否已存在
                img_filename = f"scene_{index:04d}.png"
                img_path = self.imgs_dir / img_filename
                
                if skip_if_exists and img_path.exists():
                    print(f"\n[{i}/{total}] 分镜 {index} 已存在，跳过")
                    continue
                
                print(f"\n[{i}/{total}] 生成分镜 {index}...")
                print(f"提示词: {prompt[:80]}...")
                
                # 生成图像（使用随机种子）
                torch.cuda.empty_cache()
                import random
                seed = random.randint(0, 2**32 - 1)
                generator_obj = torch.Generator(device="cuda").manual_seed(seed)
                
                # 负面词（Illustrious专用 - 更全面的质量控制）
                negative_prompt = "lazyneg, lazyhand, child, (censored, mosaic censoring, bar_censor), lowres, text, error, cropped, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, out of frame, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, username, watermark, signature"
                
                # 添加质量标签到提示词（Illustrious专用PE格式）
                quality_tags = "score_9, score_8_up, score_7_up, masterpiece, best quality, amazing quality, absurdres, newest"
                enhanced_prompt = f"{quality_tags}, BREAK {prompt}"
                
                # 使用DMD2 LoRA（原始配置）
                if use_dmd2:
                    # DMD2: 12步，CFG=2.5（原始稳定配置）
                    image = pipe(
                        prompt=enhanced_prompt,
                        negative_prompt=negative_prompt,
                        num_inference_steps=12,
                        guidance_scale=2.5,
                        width=1024,
                        height=1024,
                        generator=generator_obj,
                        clip_skip=2
                    ).images[0]
                else:
                    # 标准模式: 20步，CFG=7.0（原始配置）
                    image = pipe(
                        prompt=enhanced_prompt,
                        negative_prompt=negative_prompt,
                        num_inference_steps=20,
                        guidance_scale=7.0,
                        width=1024,
                        height=1024,
                        generator=generator_obj,
                        clip_skip=2
                    ).images[0]
                
                # 保存图像
                img_filename = f"scene_{index:04d}.png"
                img_path = self.imgs_dir / img_filename
                image.save(img_path)
                
                print(f"✓ 已保存: {img_filename}")
            
            print(f"\n✓ 所有图像生成完成！共 {total} 张")
            
            # 卸载模型，释放显存
            print("释放显存...")
            del pipe
            torch.cuda.empty_cache()
            gc.collect()
            
            return True
            
        except Exception as e:
            print(f"❌ 步骤3失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step4_generate_video(self):
        """
        步骤4: 合成视频
        将图片和音频合成为视频，添加随机转场
        """
        print("\n" + "=" * 70)
        print("步骤 4/5: 合成视频")
        print("=" * 70)
        
        # 检查ffmpeg
        from check_ffmpeg import check_ffmpeg
        if not check_ffmpeg():
            print("\n请先安装ffmpeg后再继续")
            return False
        
        try:
            # 导入视频合成模块（增强版：支持运镜和字幕）
            from video_composer_enhanced import compose_video
            
            video_path = compose_video(
                project_dir=str(self.project_dir),
                subtitle_file=str(self.subtitle_file),
                imgs_dir=str(self.imgs_dir),
                audio_dir=str(self.audio_dir),
                output_dir=str(self.videos_dir)
            )
            
            if video_path:
                print(f"✓ 视频生成完成: {video_path}")
                return True
            else:
                print("❌ 视频生成失败")
                return False
                
        except Exception as e:
            print(f"❌ 步骤4失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self):
        """执行完整流程"""
        print("\n" + "=" * 70)
        print(f"短剧AI生成系统 - {self.project_name}")
        print("=" * 70)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = datetime.now()
        
        # 执行各步骤
        steps = [
            ("生成音频和字幕", self.step1_generate_audio_and_subtitles),
            ("生成AI绘画提示词", self.step2_generate_prompts),
            ("生成分镜图像", self.step3_generate_images),
            ("合成视频", self.step4_generate_video),
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ 流程中断于: {step_name}")
                return False
        
        # 完成
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 70)
        print("✓ 全部流程完成！")
        print("=" * 70)
        print(f"总耗时: {elapsed:.1f}秒 ({elapsed/60:.1f}分钟)")
        print(f"项目目录: {self.project_dir.absolute()}")
        print(f"视频输出: {self.videos_dir.absolute()}")
        
        return True
    
    def run_with_agent(self, quality_target=0.8, task=None):
        """
        使用Agent模式运行
        
        Agent会自主决策、评估质量、优化参数
        
        Args:
            quality_target: 目标质量分数 (0-1)
            task: Task对象（用于实时更新状态）
            
        Returns:
            Agent执行结果
        """
        print("\n" + "=" * 70)
        print("🤖 Agent模式启动")
        print("=" * 70)
        print(f"目标质量: {quality_target}")
        print("Agent将自主决策和优化生成过程...")
        
        start_time = datetime.now()
        
        try:
            # 加载配置
            config_path = Path("config.json")
            if not config_path.exists():
                print("❌ 未找到config.json，请先配置Kimi API Key")
                return None
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            kimi_api_key = config.get("kimi_api_key")
            if not kimi_api_key or kimi_api_key == "sk-your-kimi-api-key":
                print("❌ 请在config.json中配置有效的Kimi API Key")
                return None
            
            # 创建LLM客户端
            llm_client = KimiAPI(kimi_api_key)
            
            # 创建工具集
            agent_tools = AgentTools(self)
            agent_tools.set_llm_client(llm_client)
            
            # 创建Agent
            agent = NovelToVideoAgent(
                llm_client=llm_client,
                tools=agent_tools.get_all_tools(),
                task=task  # 传递task对象用于实时更新
            )
            
            # 运行Agent
            result = agent.run(
                project_name=self.project_name,
                novel_text=self.novel_text,
                quality_target=quality_target
            )
            
            # 完成
            elapsed = (datetime.now() - start_time).total_seconds()
            print("\n" + "=" * 70)
            print("✓ Agent任务完成！")
            print("=" * 70)
            print(f"总耗时: {elapsed:.1f}秒 ({elapsed/60:.1f}分钟)")
            print(f"质量分数: {result['quality_score']:.2f}")
            print(f"尝试次数: {result['attempts']}")
            print(f"项目目录: {self.project_dir.absolute()}")
            if result.get('video_path'):
                print(f"视频输出: {result['video_path']}")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Agent执行失败: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='短剧AI生成系统')
    parser.add_argument('project_name', help='项目名称')
    parser.add_argument('--text', help='小说文本（直接输入）')
    parser.add_argument('--file', help='小说文本文件路径')
    parser.add_argument('--mode', choices=['workflow', 'agent'], default='workflow',
                       help='运行模式: workflow(传统流程) 或 agent(智能Agent)')
    parser.add_argument('--quality', type=float, default=0.8,
                       help='Agent模式的目标质量分数 (0-1)')
    
    args = parser.parse_args()
    
    # 获取小说文本
    if args.text:
        novel_text = args.text
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            novel_text = f.read()
    else:
        print("错误: 必须提供 --text 或 --file 参数")
        return
    
    # 创建生成器
    generator = VideoGenerator(args.project_name, novel_text)
    
    # 根据模式运行
    if args.mode == 'agent':
        print("\n🤖 使用Agent模式")
        generator.run_with_agent(quality_target=args.quality)
    else:
        print("\n📋 使用传统工作流模式")
        generator.run()


if __name__ == "__main__":
    main()
