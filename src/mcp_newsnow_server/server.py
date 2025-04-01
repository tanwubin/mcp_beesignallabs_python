import os
import sys
import logging
import argparse
from pathlib import Path
import httpx
from typing import Any
import asyncio
import datetime
import json

from mcp.server.fastmcp import FastMCP

# 修复Windows上的编码问题
if sys.platform == "win32" and os.environ.get('PYTHONIOENCODING') is None:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 判断运行方式并获取配置
def get_base_url():
    # 优先使用环境变量
    env_url = os.environ.get('NEWS_API_URL')
    if env_url:
        return env_url
    
    # 检测脚本运行方式
    is_direct_run = len(sys.argv) > 0 and Path(sys.argv[0]).name == 'server.py'
    
    # 如果是直接运行脚本，则解析命令行参数
    if is_direct_run:
        try:
            parser = argparse.ArgumentParser(description="新闻MCP服务")
            parser.add_argument('--url', type=str, default="https://newsnow.busiyi.world",
                               help='新闻API的基础URL')
            args, _ = parser.parse_known_args()  # 使用parse_known_args忽略未知参数
            return args.url
        except Exception as e:
            logging.warning(f"解析命令行参数失败: {e}")
    
    # 默认URL
    return "https://newsnow.busiyi.world"

# 获取基础URL
BASE_URL = get_base_url()

logger = logging.getLogger('mcp_news_server')
logger.info(f"启动新闻MCP服务器，API基础URL: {BASE_URL}")

# 可用的新闻源列表
sources_list=["coolapk","bilibili-hot-search","zhihu","weibo","toutiao","douyin","github-trending-today",
              "linuxdo-hot","tieba","wallstreetcn","thepaper","cls-hot","xueqiu","kuaishou"]

# 新闻源名称映射表：包含中文名、别名等
SOURCE_MAPPINGS = {
    # 常用平台映射
    "酷安": "coolapk",
    "coolapk": "coolapk",
    "酷安网": "coolapk",
    
    "b站": "bilibili-hot-search",
    "哔哩哔哩": "bilibili-hot-search",
    "bilibili": "bilibili-hot-search",
    "哔哩": "bilibili-hot-search",
    
    "知乎": "zhihu",
    "zhihu": "zhihu",
    
    "微博": "weibo",
    "weibo": "weibo",
    "新浪微博": "weibo",
    
    "头条": "toutiao",
    "今日头条": "toutiao",
    "toutiao": "toutiao",
    
    "抖音": "douyin",
    "douyin": "douyin",
    "tiktok": "douyin",
    
    "github": "github-trending-today",
    "github热榜": "github-trending-today",
    
    "linux": "linuxdo-hot",
    "linux热榜": "linuxdo-hot",
    "linuxdo": "linuxdo-hot",
    
    "贴吧": "tieba",
    "百度贴吧": "tieba",
    "tieba": "tieba",
    
    "华尔街见闻": "wallstreetcn",
    "wallstreetcn": "wallstreetcn",
    "华尔街": "wallstreetcn",
    
    "澎湃": "thepaper",
    "澎湃新闻": "thepaper",
    "thepaper": "thepaper",
    
    "财联社": "cls-hot",
    "财联": "cls-hot",
    "cls": "cls-hot",
    
    "雪球": "xueqiu",
    "xueqiu": "xueqiu",
    
    "快手": "kuaishou",
    "kuaishou": "kuaishou",
}

# 初始化 FastMCP 服务器
mcp = FastMCP("newsnow")

class NewsManager:
    def __init__(self, base_url):
        self.news_cache = {}
        self.latest_headlines = []
        self.base_url = base_url
        
    def normalize_source(self, source: str) -> str:
        """将输入的新闻源名称转换为标准名称"""
        # 转小写并去除空格
        normalized = source.lower().strip()
        
        # 从映射表中查找
        if normalized in SOURCE_MAPPINGS:
            return SOURCE_MAPPINGS[normalized]
        
        # 模糊匹配：检查是否包含关键词
        for key, value in SOURCE_MAPPINGS.items():
            if normalized in key or key in normalized:
                return value
        
        # 如果输入的是标准名称，直接返回
        if normalized in sources_list:
            return normalized
            
        # 找不到匹配，返回特殊标记
        logger.warning(f"无法识别的新闻源: {source}")
        return "__UNKNOWN_SOURCE__"
        
    def get_available_sources_formatted(self) -> str:
        """返回格式化的可用新闻源列表，包含中英文名称"""
        result = "无法识别您提供的新闻源，可用的新闻源包括:\n\n"
        
        # 获取每个源的中文名称
        sources_info = {}
        for source in sources_list:
            # 寻找对应的中文名
            cn_name = source  # 默认使用标准名称
            for name, std in SOURCE_MAPPINGS.items():
                if std == source and not name.isascii():  # 筛选出中文名称
                    cn_name = name
                    break
            sources_info[source] = cn_name
        
        # 格式化输出
        for source, cn_name in sources_info.items():
            if source == cn_name:
                result += f"- {source}\n"
            else:
                result += f"- {cn_name} ({source})\n"
                
        return result
        
    async def fetch_news(self, source: str) -> dict[str, Any] | None:
        """从新闻API获取数据并处理错误"""
        # 标准化新闻源名称
        normalized_source = self.normalize_source(source)
        
        # 检查是否为未知源
        if normalized_source == "__UNKNOWN_SOURCE__":
            # 返回可用源列表
            return {
                "error": "unknown_source",
                "message": f"未知的新闻源: {source}",
                "available_sources": self.get_available_sources_formatted()
            }
        
        headers = {
            "Accept": "application/json"
        }
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # 设置300秒超时
                try:
                    logger.debug(f"正在获取新闻，来源: {normalized_source} (原输入: {source})")
                    response = await client.get(self.base_url+f"/api/s?id={normalized_source}&latest", headers=headers)
                    response.raise_for_status()
                    return response.text
                except httpx.TimeoutException:
                    logger.error(f"获取新闻超时: {normalized_source}")
                    return f"获取新闻源 {normalized_source} 超时"
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP错误: {str(e)}")
                    return f"HTTP错误: {e.response.status_code} - {str(e)}"
                except Exception as e:
                    logger.error(f"获取新闻时出错: {str(e)}")
                    return f"未知错误: {str(e)}"
        except Exception as e:
            logger.error(f"创建HTTP客户端时出错: {str(e)}")
            return f"客户端错误: {str(e)}"

    async def fetch_multi_sources(self, sources: list[str]) -> dict[str, Any]:
        """从多个来源获取新闻"""
        results = {}
        unknown_sources = []
        
        for source in sources:
            # 标准化新闻源名称
            normalized_source = self.normalize_source(source)
            
            # 检查是否为未知源
            if normalized_source == "__UNKNOWN_SOURCE__":
                unknown_sources.append(source)
                continue
                
            logger.debug(f"批量获取新闻，处理来源: {normalized_source} (原输入: {source})")
            result = await self.fetch_news(normalized_source)
            
            try:
                # 如果result是JSON字符串，先解析成Python对象
                if isinstance(result, str) and (result.startswith('{') or result.startswith('[')):
                    parsed_result = json.loads(result)
                    results[normalized_source] = parsed_result
                else:
                    results[normalized_source] = result
            except Exception as e:
                logger.warning(f"解析结果失败，使用原始文本: {str(e)}")
                results[normalized_source] = result
        
        # 如果所有源都未知，返回一个字符串而不是对象
        if not results and unknown_sources:
            return f"未知的新闻源: {', '.join(unknown_sources)}\n{self.get_available_sources_formatted()}"
        
        # 如果有部分未知源，添加警告信息
        if unknown_sources:
            results["warnings"] = f"以下新闻源无法识别: {', '.join(unknown_sources)}"
        
        return results
    
    def get_headlines(self) -> str:
        """返回最新的头条新闻列表"""
        if not self.latest_headlines:
            return "当前没有可用的新闻头条。"
        
        headlines = "\n".join([f"- {headline}" for headline in self.latest_headlines[-10:]])
        return f"最新头条新闻:\n\n{headlines}"

    def get_available_sources(self) -> list[str]:
        """返回所有可用的新闻来源列表"""
        return sources_list

# 创建新闻管理器实例，传入基础URL
news_mgr = NewsManager(BASE_URL)

@mcp.tool()
async def get_newsnow(source: str) -> dict[str, Any] | None:
    """从指定源获取最新新闻"""
    return await news_mgr.fetch_news(source)

@mcp.tool()
async def get_multi_news(sources: list[str] = None) -> str:
    """从多个源获取最新新闻"""
    # 获取原始结果
    results = await news_mgr.fetch_multi_sources(sources)
    
    return json.dumps(results, ensure_ascii=False)

@mcp.tool()
async def get_all_news() -> dict[str, Any]:
    """获取所有配置的新闻源的数据
    
    Returns:
        包含所有新闻源数据的字典
    """
    try:
        all_results = {}
        total_sources = len(sources_list)
        logger.info(f"开始获取所有{total_sources}个新闻源的数据")
        
        # 减少并发数和超时设置，增加稳定性
        semaphore = asyncio.Semaphore(3)  # 最多同时3个请求
        
        # 创建错误列表
        errors = []
        
        async def fetch_with_timeout(source):
            try:
                # 使用信号量限制并发
                async with semaphore:
                    # 直接调用fetch_news，依赖其内部的超时处理
                    result = await news_mgr.fetch_news(source)
                    return source, result
            except Exception as e:
                logger.error(f"获取新闻源 {source} 时出错: {str(e)}")
                return source, f"获取错误: {str(e)}"
        
        # 逐个处理源，而不是使用gather
        for source in sources_list:
            try:
                source_normalized = news_mgr.normalize_source(source)
                logger.info(f"处理新闻源: {source_normalized}")
                result = await fetch_with_timeout(source)
                if isinstance(result, tuple):
                    src, data = result
                    all_results[src] = data
                else:
                    all_results[source] = f"意外的结果类型: {type(result)}"
            except Exception as e:
                logger.error(f"处理源 {source} 时出现异常: {str(e)}")
                all_results[source] = f"处理错误: {str(e)}"
        
        return all_results
    except Exception as e:
        # 捕获所有可能的错误并返回友好的错误信息
        logger.error(f"获取所有新闻源时发生错误: {str(e)}")
        return f"执行get_all_news工具时出错: {str(e)}"

@mcp.tool()
async def list_sources() -> dict[str, str]:
    """列出所有可用的新闻来源和对应的中文名称"""
    # 创建反向映射，找出每个标准源对应的第一个中文名称
    result = {}
    for source in sources_list:
        # 默认使用标准名称
        result[source] = source
        
        # 寻找对应的中文名
        for cn_name, std_name in SOURCE_MAPPINGS.items():
            if std_name == source and not cn_name.isascii():  # 筛选出中文名称
                result[source] = cn_name
                break
    
    return result

@mcp.resource(uri="news://headlines")
async def headlines() -> str:
    """获取最新头条新闻列表"""
    return news_mgr.get_headlines()

@mcp.resource(uri="news://sources")
async def sources() -> str:
    """获取可用新闻源列表"""
    sources = news_mgr.get_available_sources()
    return f"可用新闻来源:\n\n" + "\n".join([f"- {source}" for source in sources])

@mcp.prompt()
async def news_summary(source: str) -> str:
    """获取特定源的新闻总结提示"""
    return f"请帮我总结来自{source}的最新新闻，并给出访问链接。"

@mcp.prompt()
async def multi_news_summary(sources: str = "") -> str:
    """获取多源新闻总结提示"""
    if sources:
        sources_list = [s.strip() for s in sources.split(",")]
        return f"请帮我总结来自以下来源的最新新闻：{', '.join(sources_list)}。请总结各个平台的热点话题，并提供访问链接。"
    else:
        return f"请帮我总结最新的热点新闻。我已经通过API获取了以下平台的信息：{', '.join(sources_list[:5])}等。请分析热点话题，并提供访问链接。"

if __name__ == "__main__":
    # 初始化并运行服务器
    mcp.run(transport='stdio')