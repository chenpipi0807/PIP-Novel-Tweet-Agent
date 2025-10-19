"""
启动Web服务
"""
import sys
from pathlib import Path

# 检查依赖
try:
    import flask
except ImportError:
    print("❌ Flask未安装")
    print("请运行: pip install flask")
    sys.exit(1)

# 检查ffmpeg
from tools.check_ffmpeg import check_ffmpeg
if not check_ffmpeg():
    print("\n⚠ ffmpeg未安装，视频合成功能将无法使用")
    print("运行以下命令安装: python tools/install_ffmpeg.py")
    print("\n是否继续启动Web服务? (y/n): ", end='')
    
    choice = input().strip().lower()
    if choice != 'y':
        sys.exit(0)

print("\n" + "=" * 70)
print("启动短剧AI生成系统 Web服务")
print("=" * 70)
print("\n访问地址: http://localhost:5000")
print("按 Ctrl+C 停止服务\n")

# 启动Flask应用
from app import app
app.run(debug=True, host='0.0.0.0', port=5000)
