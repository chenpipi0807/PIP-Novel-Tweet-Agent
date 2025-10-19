# IndexTTS 依赖安装脚本（绕过完整安装）
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IndexTTS 1.5 依赖安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python版本
Write-Host "检查Python版本..." -ForegroundColor Yellow
python --version

Write-Host ""
Write-Host "开始安装核心依赖..." -ForegroundColor Green
Write-Host ""

# 核心依赖列表
$packages = @(
    "omegaconf",
    "gradio",
    "inflect",
    "unidecode", 
    "encodec",
    "vocos",
    "vector-quantize-pytorch",
    "rotary-embedding-torch",
    "transformers",
    "librosa",
    "soundfile",
    "tqdm",
    "pyyaml",
    "numpy",
    "scipy",
    "pypinyin",
    "audioread",
    "resampy",
    "numba",
    "scikit-learn",
    "joblib",
    "msgpack",
    "lazy-loader",
    "soxr",
    "pooch"
)

foreach ($package in $packages) {
    Write-Host "安装 $package ..." -ForegroundColor Cyan
    pip install $package --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $package 安装成功" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $package 安装失败" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：运行测试" -ForegroundColor Yellow
Write-Host "  python test_simple.py" -ForegroundColor White
Write-Host ""
