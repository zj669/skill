# 日志分析快速启动脚本 (PowerShell 版本)
# 使用方法: .\analyze.ps1 {FeatureName} [日志文件名]

param(
    [Parameter(Mandatory=$true)]
    [string]$FeatureName,
    
    [Parameter(Mandatory=$false)]
    [string]$LogFileName = $null
)

# 脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 计算 .business 目录（向上 3 层）
$BusinessDir = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptDir))

# Feature 目录
$FeatureDir = Join-Path $BusinessDir $FeatureName
$ExecuteLogsDir = Join-Path $FeatureDir "executelogs"

# 检查目录
if (-not (Test-Path $FeatureDir)) {
    Write-Host "❌ 错误：Feature 目录不存在: $FeatureDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ExecuteLogsDir)) {
    Write-Host "❌ 错误：日志目录不存在: $ExecuteLogsDir" -ForegroundColor Red
    exit 1
}

# 确定日志文件
if ($LogFileName) {
    $LogFile = Join-Path $ExecuteLogsDir $LogFileName
} else {
    # 自动选择最新的日志文件
    $LogFiles = Get-ChildItem -Path $ExecuteLogsDir -Filter "*.log" | Sort-Object LastWriteTime -Descending
    if ($LogFiles.Count -eq 0) {
        Write-Host "❌ 错误：未在 $ExecuteLogsDir 找到日志文件" -ForegroundColor Red
        exit 1
    }
    
    $LogFile = $LogFiles[0].FullName
    Write-Host "📄 自动选择最新日志: $($LogFiles[0].Name)" -ForegroundColor Cyan
}

# 检查日志文件
if (-not (Test-Path $LogFile)) {
    Write-Host "❌ 错误：日志文件不存在: $LogFile" -ForegroundColor Red
    exit 1
}

# 报告输出路径
$ReportFile = Join-Path $FeatureDir "Bug_Report.md"

# log_analyzer.py 路径
$LogAnalyzer = Join-Path $ScriptDir "log_analyzer.py"

# 显示信息
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host "🔧 日志分析工具" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host "Feature: $FeatureName"
Write-Host "日志文件: $(Resolve-Path -Relative $LogFile)"
Write-Host "报告输出: $(Resolve-Path -Relative $ReportFile)"
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host ""

# 执行分析
python $LogAnalyzer -l $LogFile -o $ReportFile --bug-report

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Gray
    Write-Host "✅ 分析完成！" -ForegroundColor Green
    Write-Host "📊 报告位置: $ReportFile" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Gray
} else {
    Write-Host "❌ 分析失败" -ForegroundColor Red
    exit 1
}
