"""
智能视频生成 Agent
基于单个 LLM 实现真正的 Agent 架构
"""
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path


class NovelToVideoAgent:
    """
    小说转视频智能 Agent
    
    核心能力：
    1. 自主决策 - 根据情况选择最佳行动
    2. 质量评估 - 评估生成结果并决定是否重试
    3. 参数调优 - 根据反馈自动调整参数
    4. 记忆学习 - 记住成功经验，优化后续决策
    """
    
    def __init__(self, llm_client, tools: Dict[str, callable], task=None):
        """
        初始化 Agent
        
        Args:
            llm_client: LLM 客户端（Kimi API）
            tools: 可用工具字典 {工具名: 工具函数}
            task: Task对象（用于实时更新状态）
        """
        self.llm = llm_client
        self.tools = tools
        self.task = task  # Task对象，用于实时更新
        
        # Agent 的记忆系统
        self.memory = {
            "current_state": {},      # 当前状态
            "history": [],            # 历史记录
            "user_messages": [],      # 用户消息
            "learned_params": {},     # 学习到的最佳参数
            "quality_threshold": 0.8  # 质量目标
        }
        
        # Agent 的思考日志
        self.thinking_log = []
        
    def run(self, project_name: str, novel_text: str, quality_target: float = 0.8) -> Dict[str, Any]:
        """
        Agent 主循环
        
        Args:
            project_name: 项目名称
            novel_text: 小说文本
            quality_target: 目标质量分数 (0-1)
            
        Returns:
            生成结果和 Agent 思考过程
        """
        print("\n" + "="*80)
        print("🤖 智能 Agent 启动")
        print("="*80)
        
        # 初始化状态
        self.memory["current_state"] = {
            "project_name": project_name,
            "novel_text": novel_text,
            "goal": f"生成质量分数>{quality_target}的视频",
            "quality_target": quality_target,
            "steps_completed": [],
            "current_step": "初始化",
            "quality_score": 0.0,
            "attempts": 0,
            "max_attempts": 3,
            "issues": [],
            "video_path": None
        }
        
        self._log_thinking("🎯 目标设定", f"生成质量>{quality_target}的视频")
        
        # Agent 主循环
        try:
            while not self._is_goal_achieved():
                # 检查尝试次数
                if self.memory["current_state"]["attempts"] >= self.memory["current_state"]["max_attempts"]:
                    self._log_thinking("⚠️ 达到最大尝试次数", "停止循环，返回当前最佳结果")
                    break
                
                # 1. 观察当前状态
                observation = self._observe()
                
                # 2. LLM 思考和决策
                thought = self._think(observation)
                action = self._decide(observation, thought)
                
                # 3. 执行动作
                result = self._execute(action)
                
                # 4. 更新记忆
                self._update_memory(action, result)
                
                # 5. 短暂休息（避免API限流）
                time.sleep(1)
                
        except Exception as e:
            self._log_thinking("❌ 错误", f"Agent遇到错误: {str(e)}")
            raise
        
        # 获取最终状态
        state = self.memory["current_state"]
        
        print("\n" + "=" * 80)
        print("🎉 Agent 完成任务")
        
        # 如果还没评估过，执行最终评估
        if state["quality_score"] == 0 and "compose_video" in state["steps_completed"]:
            print("\n📊 执行最终质量评估...")
            eval_result = self._execute({"tool": "evaluate_quality", "parameters": {}})
            if isinstance(eval_result, dict):
                state["quality_score"] = eval_result.get("overall_score", 0)
                state["issues"] = eval_result.get("issues", [])
        
        print(f"   质量分数: {state['quality_score']:.2f}")
        print(f"   尝试次数: {state['attempts']}")
        print("=" * 80)
        
        # 更新task的最终状态
        if self.task:
            self.task.quality_score = state["quality_score"]
            self.task.current_step = f"✓ 完成 (质量: {state['quality_score']:.2f})"
        
        return {
            "success": True,
            "quality_score": state["quality_score"],
            "attempts": state["attempts"],
            "video_path": state.get("video_path"),
            "thinking_log": self.thinking_log
        }
    
    def _observe(self) -> Dict[str, Any]:
        """观察当前状态"""
        state = self.memory["current_state"]
        
        # 检查用户消息
        user_messages = []
        if self.task:
            from app import user_messages as global_user_messages
            task_messages = global_user_messages.get(self.task.task_id, [])
            # 只获取新消息
            new_messages = task_messages[len(self.memory["user_messages"]):]
            if new_messages:
                user_messages = [msg['message'] for msg in new_messages]
                self.memory["user_messages"].extend(new_messages)
                print(f"📬 收到用户消息: {user_messages}")
                
                # 记录到日志
                for msg in user_messages:
                    self._log_thinking("📬 用户消息", msg)
        
        observation = {
            "current_step": state["current_step"],
            "steps_completed": state["steps_completed"],
            "quality_score": state["quality_score"],
            "quality_target": state["quality_target"],
            "attempts": state["attempts"],
            "issues": state.get("issues", []),
            "user_messages": user_messages  # 添加用户消息
        }
        
        return observation
    
    def _think(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """让 LLM 思考当前情况"""
        self._log_thinking("🧠 思考中", "分析当前状态...")
        
        prompt = f"""你是一个智能视频生成 Agent。请分析当前状态并给出建议。

当前状态：
{json.dumps(observation, ensure_ascii=False, indent=2)}

**重要规则**：
- 音频生成完成后，直接进行下一步（generate_prompts），不需要评估音频质量
- 按照工作流顺序执行：音频 → 提示词 → 图像 → 视频
- 不要建议优化或重新生成已完成的步骤

请分析：
1. 当前进度如何？已完成哪些步骤？
2. 下一步应该做什么？（按工作流顺序）

请以JSON格式回答（只返回JSON，不要其他内容）：
{{
    "progress_analysis": "进度分析",
    "next_step_suggestion": "建议的下一步操作",
    "reasoning": "推理过程"
}}"""

        try:
            # 构造消息列表
            messages = [
                {"role": "user", "content": prompt}
            ]
            response = self.llm.chat(messages)
            
            if not response:
                raise Exception("LLM返回为空")
            
            # 提取JSON
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            thought = json.loads(response)
            self._log_thinking("💭 分析结果", thought["reasoning"])
            return thought
            
        except Exception as e:
            print(f"⚠️ LLM思考失败: {e}")
            # 返回默认思考
            return {
                "progress_analysis": "无法分析",
                "quality_analysis": "无法评估",
                "problems": [],
                "next_step_suggestion": "继续下一步",
                "reasoning": f"LLM调用失败: {str(e)}"
            }
    
    def _decide(self, observation: Dict[str, Any], thought: Dict[str, Any]) -> Dict[str, Any]:
        """决定下一步行动"""
        self._log_thinking("🎬 决策中", "选择下一个动作...")
        
        state = self.memory["current_state"]
        
        # 用户消息提示
        user_msg_hint = ""
        if observation.get("user_messages"):
            user_msg_hint = f"\n\n**用户消息**：\n"
            for msg in observation["user_messages"]:
                user_msg_hint += f"- {msg}\n"
            user_msg_hint += "\n请考虑用户的建议！"
        
        prompt = f"""你是一个智能视频生成 Agent。根据分析结果，决定下一步行动。

当前状态：
- 已完成步骤: {state["steps_completed"]}
- 当前质量: {state["quality_score"]}
- 目标质量: {state["quality_target"]}{user_msg_hint}

可用工具：
0. inspect_project - 检查项目状态（恢复任务时优先使用）
1. generate_audio - 生成音频和字幕（第一步）
2. generate_prompts - 生成图像提示词（需要音频完成）
3. generate_images - 生成图像（需要提示词完成）
4. compose_video - 合成视频（需要图像完成）
5. evaluate_quality - 评估质量（视频完成后）
6. adjust_parameters - 调整参数（质量不达标时）

**严格的决策规则（按顺序执行，不跳过）**：
1. ⚠️ **inspect_project 只在第一次执行，不要重复执行**
2. generate_audio 未完成 → 执行 generate_audio
3. generate_audio 完成 且 generate_prompts 未完成 → 执行 generate_prompts
4. generate_prompts 完成 且 generate_images 未完成 → 执行 generate_images
5. generate_images 完成 且 compose_video 未完成 → 执行 compose_video
6. 全部完成 → 任务完成

**重要**：如果刚刚执行了 inspect_project，下一步必须根据检查结果执行对应的工具，不要再次执行 inspect_project！

**禁止的操作**：
- ❌ 不要评估音频质量（音频完成后直接生成提示词）
- ❌ 不要重新生成已完成的步骤
- ❌ 不要跳过任何步骤
- ❌ 没有图像不能执行 compose_video
- ❌ 没有音频不能执行 generate_prompts

请严格按照上述顺序，以JSON格式回答（只返回JSON）：
{{
    "tool": "工具名称",
    "parameters": {{"参数名": "参数值"}},
    "reason": "选择这个动作的原因"
}}"""

        try:
            # 构造消息列表
            messages = [
                {"role": "user", "content": prompt}
            ]
            response = self.llm.chat(messages)
            
            if not response:
                raise Exception("LLM返回为空")
            
            # 提取JSON
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            action = json.loads(response)
            
            # 验证决策是否合法
            state = self.memory["current_state"]
            completed = state["steps_completed"]
            tool = action['tool']
            
            # 防止重复执行 inspect_project
            history = self.memory["history"]
            if tool == 'inspect_project' and len(history) > 0:
                last_action = history[-1].get("action", {}).get("tool")
                if last_action == 'inspect_project':
                    print("⚠️ LLM决策错误：重复执行 inspect_project，强制按流程执行")
                    return self._get_default_action()
            
            # 强制检查顺序
            if tool == 'generate_prompts' and 'generate_audio' not in completed:
                print("⚠️ LLM决策错误：试图跳过音频生成，强制执行 generate_audio")
                return self._get_default_action()
            elif tool == 'generate_images' and 'generate_prompts' not in completed:
                print("⚠️ LLM决策错误：试图跳过提示词生成，强制执行 generate_prompts")
                return self._get_default_action()
            elif tool == 'compose_video' and 'generate_images' not in completed:
                print("⚠️ LLM决策错误：试图跳过图像生成，强制执行 generate_images")
                return self._get_default_action()
            
            self._log_thinking("🎬 决策", f"{action['tool']} - {action['reason']}")
            return action
            
        except Exception as e:
            print(f"⚠️ LLM决策失败: {e}")
            # 返回默认动作：按流程继续
            return self._get_default_action()
    
    def _get_default_action(self) -> Dict[str, Any]:
        """获取默认动作（当LLM失败时）"""
        state = self.memory["current_state"]
        completed = state["steps_completed"]
        
        if "generate_audio" not in completed:
            return {
                "tool": "generate_audio",
                "parameters": {},
                "reason": "按流程生成音频"
            }
        elif "generate_prompts" not in completed:
            return {
                "tool": "generate_prompts",
                "parameters": {},
                "reason": "按流程生成提示词"
            }
        elif "generate_images" not in completed:
            return {
                "tool": "generate_images",
                "parameters": {},
                "reason": "按流程生成图像"
            }
        elif "compose_video" not in completed:
            return {
                "tool": "compose_video",
                "parameters": {},
                "reason": "按流程合成视频"
            }
        else:
            return {
                "tool": "evaluate_quality",
                "parameters": {},
                "reason": "评估最终质量"
            }
    
    def _execute(self, action: Dict[str, Any]) -> Any:
        """执行动作"""
        tool_name = action["tool"]
        parameters = action.get("parameters", {})
        
        self._log_thinking("🔧 执行工具", f"{tool_name}")
        self._log_thinking("📋 原因", action.get("reason", ""))
        
        print("\n" + "=" * 60)
        print(f"🔧 执行工具: {tool_name}")
        print(f"📋 原因: {action.get('reason', '')}")
        if parameters:
            print(f"⚙️  参数: {json.dumps(parameters, ensure_ascii=False)}")
        print(f"{'='*60}\n")
        
        # 更新工具状态为运行中
        if self.task:
            self.task.current_step = f"🔧 {tool_name}"
        
        try:
            if tool_name not in self.tools:
                return {"status": "error", "message": f"未知工具: {tool_name}"}
            
            # 执行工具
            tool_func = self.tools[tool_name]
            result = tool_func(**parameters)
            
            print(f"✅ 工具执行成功\n")
            return result
            
        except Exception as e:
            print(f"❌ 工具执行失败: {e}\n")
            return {"status": "error", "message": str(e)}
    
    def _update_memory(self, action: Dict[str, Any], result: Any):
        """更新 Agent 记忆"""
        state = self.memory["current_state"]
        
        # 记录历史
        self.memory["history"].append({
            "action": action,
            "result": result,
            "timestamp": time.time()
        })
        
        # 更新状态
        tool_name = action["tool"]
        
        # inspect_project 特殊处理：同步项目实际状态到内存
        if tool_name == "inspect_project" and isinstance(result, dict) and result.get("status") == "success":
            # 从检查结果更新内存状态
            if "steps_completed" in result:
                state["steps_completed"] = result["steps_completed"]
                print(f"✅ 状态已同步: 已完成 {len(result['steps_completed'])}/4 步")
            if "current_step" in result:
                state["current_step"] = result["current_step"]
            if "issues" in result:
                state["issues"] = result["issues"]
        
        # 只有工具成功执行才标记为完成
        elif tool_name in ["generate_audio", "generate_prompts", "generate_images", "compose_video"]:
            if isinstance(result, dict) and result.get("status") == "success":
                if tool_name not in state["steps_completed"]:
                    state["steps_completed"].append(tool_name)
                    state["current_step"] = tool_name
                    print(f"✅ 步骤完成: {tool_name}")
            elif isinstance(result, dict) and result.get("status") == "error":
                print(f"❌ 步骤失败: {tool_name} - {result.get('message', '未知错误')}")
        
        # 更新质量分数
        if tool_name == "evaluate_quality" and isinstance(result, dict):
            state["quality_score"] = result.get("overall_score", 0)
            state["issues"] = result.get("issues", [])
        
        # 更新视频路径
        if tool_name == "compose_video" and isinstance(result, dict):
            state["video_path"] = result.get("video_path")
        
        # 只在重新生成图像时增加尝试次数（表示重试）
        # 正常流程不应该增加尝试次数
        if tool_name == "generate_images" and "generate_images" in state["steps_completed"]:
            # 这是重新生成，增加尝试次数
            state["attempts"] += 1
    
    def _is_goal_achieved(self) -> bool:
        """检查是否达成目标"""
        state = self.memory["current_state"]
        
        # 检查是否所有步骤完成
        required_steps = ["generate_audio", "generate_prompts", "generate_images", "compose_video"]
        all_steps_done = all(step in state["steps_completed"] for step in required_steps)
        
        # 检查质量是否达标
        quality_ok = state["quality_score"] >= state["quality_target"]
        
        return all_steps_done and (quality_ok or state["attempts"] >= state["max_attempts"])
    
    def _log_thinking(self, category: str, content: str):
        """记录 Agent 思考过程"""
        from pathlib import Path
        from datetime import datetime
        
        log_entry = {
            "timestamp": time.time(),
            "category": category,
            "content": content
        }
        self.thinking_log.append(log_entry)
        print(f"\n{category}: {content}")
        
        # 写入日志文件
        if self.task:
            try:
                log_file = Path('projects') / self.task.project_name / 'agent.log'
                log_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(log_file, 'a', encoding='utf-8') as f:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"[{timestamp}] {category}: {content}\n")
            except Exception as e:
                print(f"⚠️ 写入日志失败: {e}")
        
        # 实时更新task对象
        if self.task:
            self.task.thinking_log = self.thinking_log.copy()
            self.task.current_step = content[:50]  # 显示前50个字符
            
            # 根据步骤更新进度
            state = self.memory.get("current_state", {})
            completed = state.get("steps_completed", [])
            total_steps = 4  # audio, prompts, images, video
            self.task.progress = int((len(completed) / total_steps) * 90)  # 最多90%，留10%给评估
            
            # 更新质量分数
            if state.get("quality_score"):
                self.task.quality_score = state["quality_score"]

            # SSE: 推送思考日志作为助手消息，并更新任务进度/步骤
            try:
                from app import broadcast_event  # 延迟导入避免循环引用
                # 助手消息
                broadcast_event({
                    'type': 'agent_message',
                    'task_id': self.task.task_id,
                    'role': 'assistant',
                    'message': f"{category}: {content}",
                    'timestamp': time.time()
                })
                # 任务更新
                if hasattr(self.task, 'to_dict'):
                    broadcast_event({
                        'type': 'task_update',
                        'task': self.task.to_dict()
                    })
            except Exception:
                pass
    
    def get_thinking_log(self) -> List[Dict[str, Any]]:
        """获取思考日志"""
        return self.thinking_log
