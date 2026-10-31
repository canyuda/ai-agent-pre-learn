""""
健壮的 LLM API 调用： 写一个函数 call_llm_api(prompt: str, api_key: str) -> str，功能是调用 OpenAI Chat Completions API。要求：
正确处理 200、401、429、500 四种状态码
对 429 实现指数退避重试（最多 3 次）
对 500 实现固定 2 秒间隔重试（最多 2 次）
设置 30 秒超时
```python
 # 框架代码
 import httpx
 import time

 def call_llm_api(prompt: str, api_key: str) -> str:
     url = "https://api.openai.com/v1/chat/completions"
     headers = {
         "Authorization": f"Bearer {api_key}",
         "Content-Type": "application/json",
     }
     body = {
         "model": "gpt-4o",
         "messages": [{"role": "user", "content": prompt}],
     }
     # TODO: 实现你的重试逻辑
     pass
```
"""

import time

import httpx


class LLMAPIError(Exception):
    """Base error for LLM API calls."""

class LLMAuthError(LLMAPIError):
    """401 - invalid key; retrying cannot fix it."""

class LLMRateLimitError(LLMAPIError):
    """429 - rate limit, retries exhausted."""

class LLMServerError(LLMAPIError):
    """5xx - server error, retries exhausted."""


def call_llm_api(prompt: str, api_key: str) -> str:
    """Call OpenAI Chat Completions with per-status retry policies.

    - 200: return the reply text
    - 401: raise immediately (retrying cannot fix a bad key)
    - 429: exponential backoff 1s/2s/4s, up to 3 retries
    - 500: fixed 2s interval, up to 2 retries
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    body = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
    }

    retries_429 = 0
    retries_500 = 0

    while True:
        try:
            response = httpx.post(url, headers=headers, json=body, timeout=30)
        except httpx.TimeoutException as e:
            raise LLMAPIError(f"request timed out after 30s: {e}") from e

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]

        if response.status_code == 401:
            raise LLMAuthError("invalid API key (401) - retrying is useless, check the credential")

        if response.status_code == 429:
            if retries_429 >= 3:
                raise LLMRateLimitError("rate limited (429) - retries exhausted")
            # exponential backoff: 2^0=1s -> 2^1=2s -> 2^2=4s
            delay = 2 ** retries_429
            # honor the server-advised wait if it is longer (Retry-After in seconds)
            delay = max(delay, float(response.headers.get("retry-after", 0)))
            retries_429 += 1
            print(f"429: retry {retries_429}/3 in {delay:.1f}s")
            time.sleep(delay)
            continue

        if response.status_code == 500:
            if retries_500 >= 2:
                raise LLMServerError(f"server error (500) - retries exhausted: {response.text[:200]}")
            retries_500 += 1
            print(f"500: retry {retries_500}/2 in 2.0s")
            time.sleep(2)
            continue

        # status outside the spec: fail fast
        raise LLMAPIError(f"unexpected HTTP {response.status_code}: {response.text[:200]}")