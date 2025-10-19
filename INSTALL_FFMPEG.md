# FFmpeg 安装指南

由于 FFmpeg 二进制文件太大（>100MB），无法上传到 GitHub。请按以下步骤安装：

## Windows 安装

### 方式一：自动安装（推荐）

运行项目中的安装脚本：

```bash
python tools/install_ffmpeg.py
```

### 方式二：手动安装

1. **下载 FFmpeg**

访问官方网站下载：
- https://www.gyan.dev/ffmpeg/builds/
- 选择 "ffmpeg-release-essentials.zip"

2. **解压文件**

将下载的 zip 文件解压到项目目录：
```
PIP_Agent/
└── ffmpeg/
    └── bin/
        ├── ffmpeg.exe
        ├── ffplay.exe
        └── ffprobe.exe
```

3. **验证安装**

```bash
python tools/check_ffmpeg.py
```

### 方式三：使用包管理器

使用 Chocolatey：
```bash
choco install ffmpeg
```

使用 Scoop：
```bash
scoop install ffmpeg
```

## Linux 安装

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install ffmpeg
```

### CentOS/RHEL

```bash
sudo yum install ffmpeg
```

### Arch Linux

```bash
sudo pacman -S ffmpeg
```

## macOS 安装

使用 Homebrew：

```bash
brew install ffmpeg
```

## 验证安装

运行以下命令验证 FFmpeg 是否正确安装：

```bash
ffmpeg -version
```

应该看到 FFmpeg 的版本信息。

## 常见问题

### Q: 找不到 ffmpeg 命令
**A:** 确保 FFmpeg 的 bin 目录已添加到系统 PATH 环境变量。

### Q: Windows 上提示缺少 DLL 文件
**A:** 下载完整版的 FFmpeg（不是 essentials 版本）。

### Q: 权限错误
**A:** 在 Linux/macOS 上，可能需要使用 sudo 运行安装命令。

## 项目使用

安装完成后，项目会自动检测并使用 FFmpeg 进行视频合成。

如有问题，请查看 `tools/check_ffmpeg.py` 脚本进行诊断。
