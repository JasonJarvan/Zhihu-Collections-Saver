# Export-Zhihu-Collections

## 项目介绍
一个功能强大的知乎收藏夹导出工具，支持将知乎收藏夹（公开和私密）批量导出为 Markdown 格式文件。支持自定义输出路径、跨平台兼容、图片下载和 Obsidian 兼容格式。支持使用大模型API一键生成文章总结。

**同时提供 MCP Server**，可被 AI Agent (如 Claude Code) 直接调用，为大模型提供保存知乎收藏夹的能力。

## 主要特性

- 📚 **批量处理**: 支持同时处理多个收藏夹
- 📂 **自定义输出**: 支持用户指定输出目录
- 🖥️ **跨平台兼容**: 支持 Windows、Linux、macOS 等系统
- ✨ **智能去重**: 自动检查已存在文件，避免重复下载
- 🖼️ **图片下载**: 自动下载并保存文章中的图片
- 📝 **Obsidian 兼容**: 输出的 Markdown 格式完全兼容 Obsidian
- 📈 **实时日志**: 支持实时日志刷新，立即显示处理进度
- 🔍 **自动收藏夹获取**: 通过独立脚本自动获取用户收藏夹列表
- 🛠️ **健壮错误处理**: 单个文章失败不影响整体处理流程
- 🔧 **增强调试支持**: 自动生成调试文件，便于问题排查
- 🤖 **MCP 支持**: 提供 MCP Server，可被 AI Agent 调用

---

## 两种运行方式

### 方式一：命令行运行（传统方式）

适合直接在终端运行导出任务。

#### 安装
```bash
pip install -r requirements.txt
```

#### 配置文件设置

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

其中zhihuUrls的获取可看 ![](./readme/image.png)

#### 自动获取收藏夹（可选）

如果你想自动获取所有收藏夹，可以先运行：
```bash
python fetch_collections.py
```
这将自动更新 `config.json` 文件中的收藏夹列表。

#### 运行主程序
```bash
python main.py
```

---

### 方式二：MCP Server 运行（AI Agent 方式）

适合被 Claude Code 或其他 AI 工具集成调用。

#### 安装 MCP 依赖
```bash
# 安装MCP包
pip install mcp
```

#### 启动 MCP Server

```bash
python mcp_server.py
```

Server 会通过 stdio 通信，可以在 Claude Code 或其他 MCP 客户端中使用。

#### 可用工具

| 工具名 | 说明 |
|--------|------|
| `list_collections` | 列出配置文件中所有知乎收藏夹 |
| `export_collection` | 导出指定知乎收藏夹为Markdown文件 |
| `get_collection_info` | 获取指定收藏夹的基本信息（文章数量等） |
| `search_collections` | 在配置文件中搜索包含关键词的收藏夹 |

##### list_collections

```python
# 返回格式化的收藏夹列表
```

##### export_collection

参数：
- `collection_url` (必需): 收藏夹URL
- `collection_name` (可选): 收藏夹名称
- `output_dir` (可选): 输出目录

```python
# 示例
export_collection(
    collection_url="https://www.zhihu.com/collection/123456789",
    collection_name="Python学习",
    output_dir="my_downloads"
)
```

##### get_collection_info

参数：
- `collection_url` (必需): 收藏夹URL

##### search_collections

参数：
- `keyword` (必需): 搜索关键词

#### 在 Claude Code 中使用

在项目根目录的 `CLAUDE.md` 或用户配置文件中的 MCP 配置段添加服务器配置：

```json
{
  "mcpServers": {
    "zhihu-collections": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {},
      "cwd": "你的项目路径"
    }
  }
}
```

然后就可以用自然语言调用：

- "列出我的知乎收藏夹"
- "导出收藏夹 https://www.zhihu.com/collection/123456789"
- "搜索包含Python的收藏夹"
- "获取收藏夹 https://www.zhihu.com/collection/123456789 的文章数量"

---

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
├── logs/
│   ├── debug_20240101_120000.log
│   └── 20240101_120000.json
└── debug/
    ├── debug_answer_123456.html
    └── debug_post_789012.html
```

### 默认输出位置
- **默认路径**: 项目目录下的 `downloads/` 文件夹
- **自定义路径**: 在 `config.json` 中指定 `outputPath`
- **图片存储**: 每个收藏夹目录下的 `assets/` 文件夹
- **日志文件**: 输出目录下的 `logs/` 文件夹
- **调试文件**: 输出目录下的 `debug/` 文件夹（保存无法解析的页面HTML）


## 故障排除

### 常见问题
1. **内容下载失败**
   - 查看 `downloads/debug/` 目录中的HTML文件分析页面结构
   - 检查网络连接和cookies是否有效
   - 确认文章URL是否可正常访问

2. **日志文件为空**
   - 程序已修复了日志实时刷新问题
   - 如仍有问题，请检查输出目录的写入权限

3. **TypeError: cannot unpack non-iterable NoneType object**
   - 该问题已在v2.1版本中修复
   - 如仍遇到，请更新到最新版本

4. **专栏文章返回"该文章链接被404"但浏览器能正常打开**
   - v2.1版本新增了智能内容检测和精准错误分析
   - 检查debug目录中的HTML文件了解具体原因
   - 可能需要更新cookies或页面结构发生变化

### 调试支持
- **日志文件**: `downloads/logs/debug_*.log` 包含详细的处理信息
- **调试HTML**: `downloads/debug/debug_*.html` 保存无法解析的页面
- **测试脚本**: `test/` 目录包含各种功能测试脚本

# BUG 反馈
若您在使用过程中遇到任何问题，请在 issue 中提供 BUG 信息。为了方便我复现并解决该问题，请务必附上问题报错的提示或者相关网址。


# 建议
若您有任何建议，欢迎在 issue 中发起讨论

## 更新日志

### v2.2 MCP 支持
- 🤖 **MCP Server**: 新增 `mcp_server.py`，支持被 AI Agent 直接调用
- 📋 **4个工具**: 提供 list_collections / export_collection / get_collection_info / search_collections 工具
- 🔌 **标准协议**: 遵循 MCP 协议，支持 Claude Code 等主流 AI 工具集成

### v2.1 增强功能
- 🚀 **实时日志系统**: 支持实时日志刷新和立即显示处理进度
- 🛠️ **健壮错误处理**: 修复了 TypeError 等关键错误，单个文章失败不影响整体处理
- 🔍 **增强HTML解析**: 支持多种知乎页面结构，提高内容获取成功率
- 🔧 **调试文件生成**: 自动保存无法解析的页面HTML到 `debug/` 目录供分析
- 🔄 **自动收藏夹获取**: 新增 `fetch_collections.py` 独立脚本自动获取收藏夹列表
- 📊 **详细错误日志**: 记录具体错误信息和堆栈跟踪，便于问题定位
- 🎯 **智能内容检测**: 当标准CSS选择器失效时，自动启用智能算法检测文章内容
- 🔍 **精准错误分析**: 区分404、登录要求、权限问题等不同错误类型

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
- 第三方大模型API支持
