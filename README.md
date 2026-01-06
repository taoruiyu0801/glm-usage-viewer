# GLM Usage Viewer

> 智谱 AI (ZHIPU) Coding Plan 配额查询与可视化工具

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.8+-yellow)

[English](./README_EN.md) | 简体中文

</div>

## 功能特点

- 📊 **美观的可视化界面** - Web 界面展示配额使用情况
- 📈 **24小时趋势图** - 直观显示模型和工具使用趋势
- 🔔 **实时更新** - 一键刷新获取最新数据
- 🎨 **进度条展示** - Token 和 MCP 配额使用率一目了然
- 💻 **命令行支持** - 提供终端版本，快速查看
- 🚀 **开箱即用** - 自动读取 Claude Code 配置

## 预览

### Web 界面

![Web Dashboard](screenshot.png)

### 终端版本

```
┌──────────────────────────┐
│ GLM Coding Plan 使用统计 │
└──────────────────────────┘

┌─────────────┬────────────────────┐
│ 指标        │               数值 │
├─────────────┼────────────────────┤
│ 总调用次数  │             14,329 │
│ 总Token使用 │        671,319,433 │
│ 高峰时段    │ 2026-01-05 22:00   │
└─────────────┴────────────────────┘
```

## 安装

### 方式一：下载 EXE（Windows 推荐）

1. 下载 [releases](https://github.com/yourusername/glm-usage-viewer/releases) 中的 `GLM配额查询.exe`
2. 直接双击运行

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/yourusername/glm-usage-viewer.git
cd glm-usage-viewer

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### Web 界面

```bash
# 启动 Web 服务器
python src/server.py

# 浏览器会自动打开 http://localhost:8848
```

### 命令行版本

```bash
# 直接运行
python src/cli.py
```

### 启动脚本（Windows）

双击 `启动网页版.bat` 即可启动 Web 界面。

## 配置

程序会自动读取 Claude Code 的配置文件：

- **Windows**: `%USERPROFILE%\.claude\settings.json`
- **Linux/Mac**: `~/.claude/settings.json`

确保你的配置文件中包含：

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "your-token-here",
    "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic"
  }
}
```

## 项目结构

```
glm-usage-viewer/
├── src/
│   ├── cli.py          # 命令行版本
│   ├── server.py       # Web 服务器
│   └── viewer.html     # Web 界面
├── dist/
│   └── GLM配额查询.exe # Windows 可执行文件
├── requirements.txt    # Python 依赖
├── README.md          # 项目说明
└── LICENSE           # MIT 许可证
```

## 开发

### 构建 EXE

```bash
pyinstaller --onefile --name "GLM配额查询" src/cli.py
```

### 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

[MIT License](LICENSE)

## 致谢

- [Rich](https://github.com/Textualize/rich) - 美化终端输出
- 智谱 AI - API 服务

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/glm-usage-viewer&type=Date)](https://star-history.com/#yourusername/glm-usage-viewer&Date)

---

<div align="center">

Made with ❤️ by [Your Name](https://github.com/yourusername)

</div>
