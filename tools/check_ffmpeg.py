"""
检查ffmpeg是否可用
"""
import subprocess
import sys


def check_ffmpeg():
    """检查ffmpeg是否安装"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✓ ffmpeg已安装: {version}")
            return True
    except FileNotFoundError:
        print("❌ ffmpeg未安装或不在PATH中")
        print("\n安装方法:")
        print("1. 下载: https://www.gyan.dev/ffmpeg/builds/")
        print("2. 解压到任意目录（如 C:\\ffmpeg）")
        print("3. 添加到PATH:")
        print("   - 右键'此电脑' -> 属性 -> 高级系统设置")
        print("   - 环境变量 -> 系统变量 -> Path -> 编辑")
        print("   - 新建 -> 输入 C:\\ffmpeg\\bin")
        print("   - 确定并重启终端")
        print("\n或使用chocolatey安装:")
        print("   choco install ffmpeg")
        return False
    except Exception as e:
        print(f"❌ 检查ffmpeg时出错: {e}")
        return False


if __name__ == "__main__":
    if not check_ffmpeg():
        sys.exit(1)
