# Export-Zhihu-Collections

## 项目介绍
一个功能强大的知乎收藏夹导出工具，支持将知乎收藏夹（公开和私密）批量导出为 Markdown 格式文件。支持自定义输出路径、跨平台兼容、图片下载和 Obsidian 兼容格式。

## 主要特性

- 📚 **批量处理**: 支持同时处理多个收藏夹
- 📂 **自定义输出**: 支持用户指定输出目录
- 🖥️ **跨平台兼容**: 支持 Windows、Linux、macOS 等系统
- ✨ **智能去重**: 自动检查已存在文件，避免重复下载
- 🖼️ **图片下载**: 自动下载并保存文章中的图片
- 📝 **Obsidian 兼容**: 输出的 Markdown 格式完全兼容 Obsidian
- 📈 **详细日志**: 生成处理日志，记录每篇文章的下载状态


# 安装
**Python 安装**：
首先，确保您的系统已安装 Python。

**依赖安装**：
使用以下命令安装所需的依赖项：
```bash
pip install -r requirements.txt
```


# 使用指南

## 快速开始

### 1. 配置文件设置
首先创建主配置文件：
```bash
# 复制配置示例文件
cp config_examples.json config.json
```

编辑 `config.json` 文件，配置你的收藏夹信息：
```json
{
  "zhihuUrls": [
    {
      "name": "收藏夹名称",
      "url": "https://www.zhihu.com/collection/123456789"
    },
    {
      "name": "另一个收藏夹",
      "url": "https://www.zhihu.com/collection/987654321"
    }
  ],
  "outputPath": "/path/to/your/output/directory",
  "os": "linux"
}
```

### 2. 运行程序
```bash
python main.py
```

## 配置选项说明

### 基本配置
- **zhihuUrls**: 收藏夹列表，每个收藏夹包含名称和 URL
- **outputPath**: 自定义输出路径（可选，留空使用默认路径）
- **os**: 操作系统类型（可选，留空自动检测）

### 支持的操作系统和路径格式
- **Windows**: `"D:\\Documents\\ZhihuExports"` 或 `"D:/Documents/ZhihuExports"`
- **Linux/Unix**: `"/usr/local/share/zhihu-exports"`
- **macOS**: `"~/Documents/ZhihuExports"`
- **Cygwin**: `"/cygdrive/d/Documents/ZhihuExports"`

### 私密收藏夹访问
对于私密收藏夹，需要创建 `cookies.json` 文件：
```json
[
  {"name": "cookie_name", "value": "cookie_value"},
  {"name": "another_cookie", "value": "another_value"}
]
```


## 输出结果

### 文件结构
```
输出目录/
├── 收藏夹名称1/
│   ├── 文章1.md
│   ├── 文章2.md
│   └── assets/
│       ├── image1.jpg
│       └── image2.png
├── 收藏夹名称2/
└── logs/
    ├── debug_20240101_120000.log
    └── 20240101_120000.json
```

### 默认输出位置
- **默认路径**: 项目目录下的 `downloads/` 文件夹
- **自定义路径**: 在 `config.json` 中指定 `outputPath`
- **图片存储**: 每个收藏夹目录下的 `assets/` 文件夹
- **日志文件**: 输出目录下的 `logs/` 文件夹


# BUG 反馈
若您在使用过程中遇到任何问题，请在 issue 中提供 BUG 信息。为了方便我复现并解决该问题，请务必附上问题报错的提示或者相关网址。


# 建议
若您有任何建议，欢迎在 issue 中发起讨论

## 更新日志

### v2.0 新增功能
- ✨ 批量处理多个收藏夹
- ⚙️ 配置文件系统 (config.json)
- 📂 自定义输出路径支持
- 🖥️ 跨平台路径处理
- ✨ 智能文件去重功能
- 📈 详细处理日志系统
- 🔄 向后兼容旧版配置文件

## Todo
- 优化抓取速度
- 增加更多导出格式支持
- GUI 界面开发