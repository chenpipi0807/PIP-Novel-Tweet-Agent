"""
项目管理模块
扫描本地项目，检测项目状态和进度
"""
import json
from pathlib import Path
from datetime import datetime


class ProjectManager:
    """项目管理器"""
    
    def __init__(self, projects_dir="projects"):
        self.projects_dir = Path(projects_dir)
        self.projects_dir.mkdir(exist_ok=True)
    
    def scan_projects(self):
        """扫描所有本地项目"""
        projects = []
        
        if not self.projects_dir.exists():
            return projects
        
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                project_info = self.get_project_status(project_dir.name)
                if project_info:
                    projects.append(project_info)
        
        return projects
    
    def get_project_status(self, project_name):
        """获取项目状态和进度"""
        project_dir = self.projects_dir / project_name
        
        if not project_dir.exists():
            return None
        
        audio_dir = project_dir / "Audio"
        imgs_dir = project_dir / "Imgs"
        videos_dir = project_dir / "Videos"
        
        subtitle_file = audio_dir / "Subtitles.json"
        prompts_file = project_dir / "Prompts.json"
        
        # 检测各步骤完成情况
        status = {
            'project_name': project_name,
            'step1_audio': False,
            'step2_prompts': False,
            'step3_images': False,
            'step4_video': False,
            'total_scenes': 0,
            'completed_scenes': 0,
            'missing_scenes': [],
            'current_step': 0,
            'progress': 0,
            'status': 'incomplete',
            'created_time': None,
            'modified_time': None
        }
        
        # 获取创建和修改时间
        if project_dir.exists():
            status['created_time'] = datetime.fromtimestamp(project_dir.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            status['modified_time'] = datetime.fromtimestamp(project_dir.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # 步骤1: 检查音频和字幕
        if subtitle_file.exists():
            status['step1_audio'] = True
            status['current_step'] = max(status['current_step'], 1)
            
            # 读取字幕数量
            try:
                with open(subtitle_file, 'r', encoding='utf-8') as f:
                    subtitle_data = json.load(f)
                    status['total_scenes'] = subtitle_data.get('total_sentences', 0)
            except:
                pass
        
        # 步骤2: 检查提示词
        if prompts_file.exists():
            status['step2_prompts'] = True
            status['current_step'] = max(status['current_step'], 2)
            
            # 读取提示词数量
            try:
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    prompts_data = json.load(f)
                    scene_prompts = prompts_data.get('scene_prompts', [])
                    if status['total_scenes'] == 0:
                        status['total_scenes'] = len(scene_prompts)
            except:
                pass
        
        # 步骤3: 检查图像
        if imgs_dir.exists():
            img_files = list(imgs_dir.glob("scene_*.png"))
            status['completed_scenes'] = len(img_files)
            
            if status['completed_scenes'] > 0:
                status['step3_images'] = status['completed_scenes'] == status['total_scenes']
                status['current_step'] = max(status['current_step'], 3)
                
                # 找出缺失的分镜
                if status['total_scenes'] > 0:
                    existing_indices = set()
                    for img_file in img_files:
                        try:
                            index = int(img_file.stem.split('_')[1])
                            existing_indices.add(index)
                        except:
                            pass
                    
                    for i in range(1, status['total_scenes'] + 1):
                        if i not in existing_indices:
                            status['missing_scenes'].append(i)
        
        # 步骤4: 检查视频
        if videos_dir.exists():
            video_files = list(videos_dir.glob("*.mp4"))
            if video_files:
                status['step4_video'] = True
                status['current_step'] = 4
                status['status'] = 'completed'
        
        # 计算进度
        if status['current_step'] == 0:
            status['progress'] = 0
        elif status['current_step'] == 1:
            status['progress'] = 10
        elif status['current_step'] == 2:
            status['progress'] = 30
        elif status['current_step'] == 3:
            if status['total_scenes'] > 0:
                status['progress'] = 50 + int((status['completed_scenes'] / status['total_scenes']) * 30)
            else:
                status['progress'] = 50
        elif status['current_step'] == 4:
            status['progress'] = 100
        
        # 判断状态
        if status['progress'] == 100:
            status['status'] = 'completed'
        elif status['progress'] > 0:
            status['status'] = 'incomplete'
        else:
            status['status'] = 'empty'
        
        return status
    
    def get_next_step(self, project_name):
        """获取项目下一步需要执行的步骤"""
        status = self.get_project_status(project_name)
        
        if not status:
            return None
        
        if not status['step1_audio']:
            return 'step1_audio'
        elif not status['step2_prompts']:
            return 'step2_prompts'
        elif not status['step3_images']:
            return 'step3_images'
        elif not status['step4_video']:
            return 'step4_video'
        else:
            return 'completed'
    
    def can_continue(self, project_name):
        """判断项目是否可以继续"""
        status = self.get_project_status(project_name)
        
        if not status:
            return False
        
        return status['status'] == 'incomplete' and status['progress'] > 0


if __name__ == "__main__":
    # 测试
    manager = ProjectManager()
    projects = manager.scan_projects()
    
    print(f"找到 {len(projects)} 个项目:\n")
    
    for project in projects:
        print(f"项目: {project['project_name']}")
        print(f"  状态: {project['status']}")
        print(f"  进度: {project['progress']}%")
        print(f"  当前步骤: {project['current_step']}")
        print(f"  分镜: {project['completed_scenes']}/{project['total_scenes']}")
        if project['missing_scenes']:
            print(f"  缺失分镜: {project['missing_scenes']}")
        print()
