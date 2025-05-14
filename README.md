[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/sligter-mcp-newsnow-badge.png)](https://mseep.ai/app/sligter-mcp-newsnow)

# MCP NewNow Server

[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-blue)](https://github.com/anthropics/anthropic-tools)

一个基于 Model Context Protocol (MCP) 的新闻聚合服务器，通过 [Newsnow](https://github.com/ourongxing/newsnow) API 提供多平台热点新闻和趋势话题。

## 功能特点

- **多平台热点聚合**：一站式获取来自酷安、知乎、微博、B站、抖音、GitHub等14+平台的热点内容
- **中英文源名识别**：支持中英文新闻源名称，并提供模糊匹配功能
- **自定义API端点**：通过环境变量或命令行参数配置NewNow API端点


## 安装方法

### 方法一：从 PyPI 安装

```bash
# 使用 pip 安装
pip install mcp-newsnow

# 或使用 uv 安装
uv pip install mcp-newsnow
```

### 方法二：配置 Claude Desktop

在 Claude Desktop 配置文件中添加服务器配置：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

添加以下配置：

```json
{
  "mcpServers": {
    "get_news": {
      "command": "uvx",
      "args": [
        "mcp-newsnow"
      ]
    }
  }
}
```

## 使用方法

### 使用 Claude Desktop

1. 安装并配置 Claude Desktop
2. 在配置文件中添加上述 MCP 服务器配置
3. 重启 Claude Desktop
4. 在对话中使用新闻相关工具

### 使用 MCP CLI 进行开发

```bash
# 通过环境变量设置API端点
NEWS_API_URL=https://newsnow.example.com

# 运行测试
mcp test server.py
```

## 可用工具

### 1. 获取单一源新闻 (get_newsnow)

```python
async def get_newsnow(source: str) -> dict[str, Any] | None
```

从指定源获取最新新闻。

**参数**:
- `source`: 新闻源名称 (支持中英文，例如"知乎"、"zhihu"、"B站"等)

**返回**: 包含新闻数据的字典

### 2. 获取多源新闻 (get_multi_news)

```python
async def get_multi_news(sources: list[str] = None) -> dict[str, Any]
```

从多个源获取最新新闻 (最多5个)。

**参数**:
- `sources`: 新闻源名称列表

**返回**: 包含多个新闻源数据的字典

### 3. 获取所有源新闻 (get_all_news)

```python
async def get_all_news() -> dict[str, Any]
```

获取所有配置的新闻源数据。

**返回**: 包含所有新闻源数据和元数据的字典

### 4. 列出可用新闻源 (list_sources)

```python
async def list_sources() -> dict[str, str]
```

列出所有可用的新闻源及其中文名称。

**返回**: 新闻源ID到中文名称的映射字典

## 环境变量

- `NEWS_API_URL`: Newsnow API的基础URL (默认: "https://newsnow.busiyi.world/")

## 支持的新闻源

- 酷安 (coolapk)
- B站热搜 (bilibili-hot-search)
- 知乎 (zhihu)
- 微博 (weibo)
- 今日头条 (toutiao)
- 抖音 (douyin)
- GitHub趋势 (github-trending-today)
- Linux热榜 (linuxdo-hot)
- 贴吧 (tieba)
- 华尔街见闻 (wallstreetcn)
- 澎湃新闻 (thepaper)
- 财联社 (cls-hot)
- 雪球 (xueqiu)
- 快手 (kuaishou)

## 贡献指南

欢迎提交问题和拉取请求！以下是一些潜在的改进方向：

- 添加更多新闻源支持
- 增强内容提取和处理能力
- 添加缓存层减少API调用
- 改进错误处理和重试机制
- 添加结果过滤和分类功能

## 许可证

本项目采用 MIT 许可证。