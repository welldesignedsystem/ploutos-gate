import os
from dataclasses import dataclass, field


@dataclass
class RedditConfig:
    client_id: str = ""
    client_secret: str = ""
    user_agent: str = "ploutos-gate:1.0.0 (by /u/ploutos-gate-bot)"
    username: str = ""
    password: str = ""

    subreddit_allowlist: list[str] = field(default_factory=list)
    subreddit_blocklist: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "RedditConfig":
        allow = os.environ.get("REDDIT_SUBREDDIT_ALLOWLIST", "")
        block = os.environ.get("REDDIT_SUBREDDIT_BLOCKLIST", "")
        return cls(
            client_id=os.environ.get("REDDIT_CLIENT_ID", ""),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET", ""),
            user_agent=os.environ.get("REDDIT_USER_AGENT", cls.user_agent),
            username=os.environ.get("REDDIT_USERNAME", ""),
            password=os.environ.get("REDDIT_PASSWORD", ""),
            subreddit_allowlist=[s.strip().lower() for s in allow.split(",") if s.strip()],
            subreddit_blocklist=[s.strip().lower() for s in block.split(",") if s.strip()],
        )

    def is_subreddit_allowed(self, subreddit: str) -> bool:
        name = subreddit.lower()
        if name in self.subreddit_blocklist:
            return False
        if self.subreddit_allowlist:
            return name in self.subreddit_allowlist
        return True
