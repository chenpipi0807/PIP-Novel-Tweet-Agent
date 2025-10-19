"""
自动下载安装ffmpeg
无需管理员权限，自动配置环境变量
"""
import os
import sys
import urllib.request
import zipfile
import winreg
from pathlib import Path


def download_ffmpeg():
    """下载ffmpeg"""
    print("=" * 70)
    print("自动安装 ffmpeg")
    print("=" * 70)
    
    # 使用GitHub镜像下载（更稳定）
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    # 下载到当前目录
    download_path = Path("ffmpeg.zip")
    install_dir = Path("C:/PIP_Agent/ffmpeg")
    
    print(f"\n1. 下载ffmpeg...")
    print(f"   URL: {ffmpeg_url}")
    print(f"   这可能需要几分钟...")
    
    try:
        # 下载文件
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100)
            print(f"\r   进度: {percent:.1f}%", end='')
        
        urllib.request.urlretrieve(ffmpeg_url, download_path, show_progress)
        print("\n   ✓ 下载完成")
        
    except Exception as e:
        print(f"\n   ❌ 下载失败: {e}")
        print("\n   请手动下载:")
        print(f"   1. 访问: https://github.com/BtbN/FFmpeg-Builds/releases")
        print(f"   2. 下载: ffmpeg-master-latest-win64-gpl.zip")
        print(f"   3. 解压到: {install_dir}")
        return None
    
    # 解压
    print(f"\n2. 解压到 {install_dir}...")
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            # 获取顶层目录名
            top_dir = zip_ref.namelist()[0].split('/')[0]
            
            # 解压
            zip_ref.extractall(install_dir.parent)
            
            # 重命名为ffmpeg
            extracted_dir = install_dir.parent / top_dir
            if extracted_dir.exists() and extracted_dir != install_dir:
                if install_dir.exists():
                    import shutil
                    shutil.rmtree(install_dir)
                extracted_dir.rename(install_dir)
        
        print("   ✓ 解压完成")
        
        # 删除下载的zip
        download_path.unlink()
        
    except Exception as e:
        print(f"   ❌ 解压失败: {e}")
        return None
    
    # 找到ffmpeg.exe路径
    ffmpeg_bin = install_dir / "bin"
    ffmpeg_exe = ffmpeg_bin / "ffmpeg.exe"
    
    if not ffmpeg_exe.exists():
        print(f"   ❌ 找不到ffmpeg.exe")
        return None
    
    print(f"   ✓ ffmpeg位置: {ffmpeg_exe}")
    
    return str(ffmpeg_bin)


def add_to_user_path(new_path):
    """添加到用户PATH环境变量（无需管理员权限）"""
    print(f"\n3. 添加到PATH环境变量...")
    
    try:
        # 打开用户环境变量注册表
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Environment',
            0,
            winreg.KEY_READ | winreg.KEY_WRITE
        )
        
        # 读取当前PATH
        try:
            current_path, _ = winreg.QueryValueEx(key, 'Path')
        except FileNotFoundError:
            current_path = ''
        
        # 检查是否已存在
        paths = [p.strip() for p in current_path.split(';') if p.strip()]
        
        if new_path in paths:
            print(f"   ✓ PATH中已存在")
            winreg.CloseKey(key)
            return True
        
        # 添加新路径
        paths.append(new_path)
        new_path_value = ';'.join(paths)
        
        # 写入注册表
        winreg.SetValueEx(
            key,
            'Path',
            0,
            winreg.REG_EXPAND_SZ,
            new_path_value
        )
        
        winreg.CloseKey(key)
        
        # 通知系统环境变量已更改
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x1A
        SMTO_ABORTIFHUNG = 0x0002
        result = ctypes.c_long()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            'Environment',
            SMTO_ABORTIFHUNG,
            5000,
            ctypes.byref(result)
        )
        
        print(f"   ✓ 已添加到用户PATH")
        print(f"   ⚠ 需要重启终端才能生效")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 添加PATH失败: {e}")
        print(f"\n   请手动添加:")
        print(f"   1. Win+R 输入: sysdm.cpl")
        print(f"   2. 高级 -> 环境变量")
        print(f"   3. 用户变量 -> Path -> 编辑")
        print(f"   4. 新建 -> 输入: {new_path}")
        return False


def verify_installation():
    """验证安装"""
    print(f"\n4. 验证安装...")
    
    # 临时添加到当前进程的PATH
    ffmpeg_bin = Path("C:/PIP_Agent/ffmpeg/bin")
    if ffmpeg_bin.exists():
        os.environ['PATH'] = str(ffmpeg_bin) + os.pathsep + os.environ['PATH']
    
    try:
        import subprocess
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"   ✓ ffmpeg安装成功!")
            print(f"   {version}")
            return True
        else:
            print(f"   ❌ ffmpeg无法运行")
            return False
            
    except FileNotFoundError:
        print(f"   ⚠ 当前终端中ffmpeg不可用")
        print(f"   请重启终端后再试")
        return True  # 实际已安装，只是需要重启
    except Exception as e:
        print(f"   ❌ 验证失败: {e}")
        return False


def main():
    """主函数"""
    # 检查是否已安装
    try:
        import subprocess
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ ffmpeg已安装，无需重复安装")
            return
    except:
        pass
    
    # 下载安装
    ffmpeg_bin = download_ffmpeg()
    
    if not ffmpeg_bin:
        print("\n❌ 安装失败")
        sys.exit(1)
    
    # 添加到PATH
    add_to_user_path(ffmpeg_bin)
    
    # 验证
    if verify_installation():
        print("\n" + "=" * 70)
        print("✓ 安装完成！")
        print("=" * 70)
        print("\n下一步:")
        print("  1. 重启PowerShell终端")
        print("  2. 运行: python test_full_pipeline.py")
        print("\n或者在当前终端直接运行（临时生效）:")
        print(f"  $env:PATH = \"{ffmpeg_bin};$env:PATH\"")
        print("  python test_full_pipeline.py")
    else:
        print("\n⚠ 安装可能未完全成功，请检查上述错误信息")


if __name__ == "__main__":
    main()
