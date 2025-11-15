"""Base scraper class with common functionality."""
import asyncio
import time
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

import aiohttp
from loguru import logger

from ..config import settings


class BaseScraper(ABC):
    """Base class for all scrapers."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_delay = settings.request_delay
        self.max_retries = settings.max_retries
        self.last_request_time = 0

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'AgentKataster/0.1.0 (Land Registry Data Collector)'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _rate_limit(self):
        """Implement rate limiting between requests."""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()

    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[Any]:
        """Make HTTP request with retry logic."""
        await self._rate_limit()

        for attempt in range(self.max_retries):
            try:
                async with self.session.request(
                    method, url, params=params, data=data, **kwargs
                ) as response:
                    response.raise_for_status()

                    content_type = response.headers.get('Content-Type', '')
                    if 'json' in content_type:
                        return await response.json()
                    elif 'xml' in content_type or 'gml' in content_type:
                        return await response.text()
                    else:
                        return await response.read()

            except aiohttp.ClientError as e:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Max retries reached for URL: {url}")
                    raise

        return None

    @abstractmethod
    async def scrape(self, *args, **kwargs):
        """Main scraping method - must be implemented by subclasses."""
        pass
