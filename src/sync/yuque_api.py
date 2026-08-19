"""
语雀 API 客户端
===============
直接调用语雀 API，实现限流最佳实践：
1. 监控 X-RateLimit-* 响应头，实时掌握剩余配额
2. 指数退避重试（429 时不立即重试，等待时间逐渐增加）
3. 主动请求间隔（默认 0.5s，可配置）
4. 合法 User-Agent

用途：
- elog CLI 同步前预检（看限流是否恢复）
- elog CLI 不可用时作为 fallback 直接拉取文档
- 监控语雀 API 健康状态
"""

import time
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)


@dataclass
class RateLimitInfo:
    """语雀 API 限流信息（从响应头解析）"""
    limit: Optional[int] = None        # 总配额（X-RateLimit-Limit）
    remaining: Optional[int] = None    # 剩余配额（X-RateLimit-Remaining）
    reset_at: Optional[str] = None     # 重置时间（X-RateLimit-Reset）
    last_updated: float = field(default_factory=time.time)


class YuqueAPIClient:
    """语雀 API 客户端（带限流处理）"""

    def __init__(
        self,
        token: str = "",
        user_agent: str = "Larkwell/1.0 (https://github.com/Yixi233-mo/Larkwell)",
        request_interval: float = 0.5,
        max_retries: int = 5,
        backoff_base: float = 2.0,
    ):
        """
        初始化语雀 API 客户端

        Args:
            token: 语雀 API Token（不传则从 config 读取）
            user_agent: 合法的 User-Agent
            request_interval: 主动请求间隔（秒），默认 0.5s
            max_retries: 429 错误最大重试次数
            backoff_base: 指数退避基数（秒），实际等待 = backoff_base ** retry_count
        """
        config = get_config()
        self.token = token or config.YUQUE_TOKEN
        if not self.token:
            raise ValueError("语雀 Token 未配置（YUQUE_TOKEN）")

        self.user_agent = user_agent
        self.request_interval = request_interval
        self.max_retries = max_retries
        self.backoff_base = backoff_base

        self.base_url = "https://www.yuque.com/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            "X-Auth-Token": self.token,
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        })

        # 限流信息缓存
        self.rate_limit = RateLimitInfo()
        # 上次请求时间戳
        self._last_request_time = 0.0

    def _wait_for_interval(self) -> None:
        """主动请求间隔控制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_interval:
            wait = self.request_interval - elapsed
            time.sleep(wait)

    def _update_rate_limit(self, resp: requests.Response) -> None:
        """从响应头更新限流信息"""
        headers = resp.headers
        try:
            if "X-RateLimit-Limit" in headers:
                self.rate_limit.limit = int(headers["X-RateLimit-Limit"])
            if "X-RateLimit-Remaining" in headers:
                self.rate_limit.remaining = int(headers["X-RateLimit-Remaining"])
            if "X-RateLimit-Reset" in headers:
                self.rate_limit.reset_at = headers["X-RateLimit-Reset"]
            self.rate_limit.last_updated = time.time()

            if self.rate_limit.remaining is not None and self.rate_limit.remaining < 10:
                logger.warning(
                    f"语雀 API 剩余配额低: {self.rate_limit.remaining}/"
                    f"{self.rate_limit.limit}，重置时间: {self.rate_limit.reset_at}"
                )
        except (ValueError, TypeError) as e:
            logger.debug(f"解析限流响应头失败: {e}")

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """
        发起请求，带指数退避重试

        Args:
            method: HTTP 方法
            endpoint: API 路径（如 /repos/xxx/yyy/docs）
            **kwargs: 传给 requests 的其他参数

        Returns:
            Response 对象，失败返回 None
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(1, self.max_retries + 1):
            # 1. 主动请求间隔
            self._wait_for_interval()

            try:
                resp = self.session.request(method, url, timeout=30, **kwargs)
                self._last_request_time = time.time()

                # 2. 更新限流信息
                self._update_rate_limit(resp)

                # 3. 处理 429
                if resp.status_code == 429:
                    if attempt < self.max_retries:
                        wait = self.backoff_base ** attempt  # 2, 4, 8, 16, 32
                        logger.warning(
                            f"语雀 API 429 限流，第 {attempt}/{self.max_retries} 次重试，"
                            f"等待 {wait}s 后重试"
                        )
                        time.sleep(wait)
                        continue
                    else:
                        logger.error(
                            f"语雀 API 429 限流，已达最大重试次数 {self.max_retries}"
                        )
                        return None

                # 4. 其他错误
                if resp.status_code != 200:
                    logger.error(
                        f"语雀 API 请求失败: HTTP {resp.status_code} - {resp.text[:200]}"
                    )
                    return None

                return resp

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"网络连接失败: {e}")
                if attempt < self.max_retries:
                    wait = self.backoff_base ** attempt
                    time.sleep(wait)
                    continue
                return None

            except requests.exceptions.Timeout:
                logger.warning(f"请求超时: {url}")
                if attempt < self.max_retries:
                    wait = self.backoff_base ** attempt
                    time.sleep(wait)
                    continue
                return None

        return None

    # ==================== API 端点 ====================

    def check_rate_limit(self) -> Dict[str, Any]:
        """
        预检：检查语雀 API 是否可用，不消耗大量配额

        Returns:
            {"available": bool, "rate_limit": RateLimitInfo, "status_code": int}
        """
        logger.info("语雀 API 预检...")
        # 用最轻量的接口（获取单个 repo 信息）做预检
        config = get_config()
        endpoint = f"/repos/{config.YUQUE_LOGIN}/{config.YUQUE_REPO}"

        resp = self._request("GET", endpoint)
        if resp is None:
            return {
                "available": False,
                "rate_limit": None,
                "status_code": None,
            }

        return {
            "available": True,
            "rate_limit": {
                "limit": self.rate_limit.limit,
                "remaining": self.rate_limit.remaining,
                "reset_at": self.rate_limit.reset_at,
            },
            "status_code": resp.status_code,
        }

    def list_docs(self, namespace: str = "", book_slug: str = "") -> Optional[List[Dict]]:
        """
        列出知识库下的所有文档

        Args:
            namespace: 用户命名空间（不传用 config）
            book_slug: 知识库 slug（不传用 config）

        Returns:
            文档列表，失败返回 None
        """
        config = get_config()
        namespace = namespace or config.YUQUE_LOGIN
        book_slug = book_slug or config.YUQUE_REPO

        endpoint = f"/repos/{namespace}/{book_slug}/docs"
        resp = self._request("GET", endpoint)
        if resp is None:
            return None

        data = resp.json()
        return data.get("data", [])

    def get_doc_detail(self, namespace: str, book_slug: str, slug: str) -> Optional[Dict]:
        """
        获取单篇文档详情（含 body）

        Args:
            namespace: 用户命名空间
            book_slug: 知识库 slug
            slug: 文档 slug

        Returns:
            文档对象，失败返回 None
        """
        endpoint = f"/repos/{namespace}/{book_slug}/docs/{slug}"
        resp = self._request("GET", endpoint)
        if resp is None:
            return None

        data = resp.json()
        return data.get("data")

    def get_rate_limit_info(self) -> RateLimitInfo:
        """获取当前限流信息"""
        return self.rate_limit


def check_yuque_available() -> bool:
    """
    便捷函数：检查语雀 API 是否可用

    Returns:
        True 表示可用，False 表示不可用（限流/网络问题/Token 错误）
    """
    try:
        client = YuqueAPIClient()
        result = client.check_rate_limit()
        if result["available"]:
            rl = result["rate_limit"]
            if rl and rl.get("remaining") is not None:
                logger.info(
                    f"语雀 API 可用，剩余配额: {rl['remaining']}/{rl['limit']}，"
                    f"重置时间: {rl['reset_at']}"
                )
            else:
                logger.info("语雀 API 可用")
            return True
        else:
            logger.warning("语雀 API 不可用（限流或网络问题）")
            return False
    except Exception as e:
        logger.error(f"语雀 API 预检失败: {e}")
        return False


if __name__ == "__main__":
    # 直接运行此模块可做语雀 API 预检
    result = check_yuque_available()
    print(f"语雀 API 可用: {result}")
