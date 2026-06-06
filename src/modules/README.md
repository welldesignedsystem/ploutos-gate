# modules

Domain packages for `ploutos-gate` project. Each subdirectory is a self-contained Python package.

| Package | Description |
|---------|-------------|
| `reddit/` | Reddit MCP server — search, browse, info, write, monitor tools via PRAW |

Packages are importable directly (no `modules.` prefix):

```python
from reddit.client import RedditClient
from reddit.config import RedditConfig

config = RedditConfig.from_env()
client = RedditClient(config)
posts = client.search_posts("keyword", limit=5)
```
