import os

from reddit.config import RedditConfig


def test_from_env_defaults():
    for key in (
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
        "REDDIT_SUBREDDIT_ALLOWLIST",
        "REDDIT_SUBREDDIT_BLOCKLIST",
        "REDDIT_USER_AGENT",
    ):
        os.environ.pop(key, None)

    cfg = RedditConfig.from_env()
    assert cfg.client_id == ""
    assert cfg.client_secret == ""
    assert cfg.username == ""
    assert cfg.password == ""
    assert cfg.subreddit_allowlist == []
    assert cfg.subreddit_blocklist == []
    assert cfg.user_agent == "ploutos-gate:1.0.0 (by /u/ploutos-gate-bot)"


def test_from_env_parses_all():
    os.environ["REDDIT_CLIENT_ID"] = "cid123"
    os.environ["REDDIT_CLIENT_SECRET"] = "secret456"
    os.environ["REDDIT_USERNAME"] = "testuser"
    os.environ["REDDIT_PASSWORD"] = "testpass"
    os.environ["REDDIT_USER_AGENT"] = "custom-agent"
    os.environ["REDDIT_SUBREDDIT_ALLOWLIST"] = "python, rust,   golang"
    os.environ["REDDIT_SUBREDDIT_BLOCKLIST"] = "nsfw, politics"

    cfg = RedditConfig.from_env()
    assert cfg.client_id == "cid123"
    assert cfg.client_secret == "secret456"
    assert cfg.username == "testuser"
    assert cfg.password == "testpass"
    assert cfg.user_agent == "custom-agent"
    assert cfg.subreddit_allowlist == ["python", "rust", "golang"]
    assert cfg.subreddit_blocklist == ["nsfw", "politics"]


def test_from_env_strips_whitespace():
    os.environ["REDDIT_SUBREDDIT_ALLOWLIST"] = "  a , b , c  "
    cfg = RedditConfig.from_env()
    assert cfg.subreddit_allowlist == ["a", "b", "c"]


def test_from_env_empty_strings_produce_empty_lists():
    os.environ["REDDIT_SUBREDDIT_ALLOWLIST"] = ""
    os.environ["REDDIT_SUBREDDIT_BLOCKLIST"] = ""
    cfg = RedditConfig.from_env()
    assert cfg.subreddit_allowlist == []
    assert cfg.subreddit_blocklist == []


class TestIsSubredditAllowed:
    def test_allow_all_when_no_lists(self):
        cfg = RedditConfig()
        assert cfg.is_subreddit_allowed("anything") is True
        assert cfg.is_subreddit_allowed("python") is True

    def test_blocklist_excludes(self):
        cfg = RedditConfig(subreddit_blocklist=["nsfw", "politics"])
        assert cfg.is_subreddit_allowed("nsfw") is False
        assert cfg.is_subreddit_allowed("politics") is False
        assert cfg.is_subreddit_allowed("python") is True

    def test_blocklist_is_case_insensitive(self):
        cfg = RedditConfig(subreddit_blocklist=["NSFW"])
        assert cfg.is_subreddit_allowed("nsfw") is False
        assert cfg.is_subreddit_allowed("NSFW") is False

    def test_allowlist_restricts(self):
        cfg = RedditConfig(subreddit_allowlist=["python", "rust"])
        assert cfg.is_subreddit_allowed("python") is True
        assert cfg.is_subreddit_allowed("rust") is True
        assert cfg.is_subreddit_allowed("golang") is False

    def test_allowlist_is_case_insensitive(self):
        cfg = RedditConfig(subreddit_allowlist=["Python"])
        assert cfg.is_subreddit_allowed("python") is True
        assert cfg.is_subreddit_allowed("PYTHON") is True

    def test_blocklist_takes_priority_over_allowlist(self):
        cfg = RedditConfig(
            subreddit_allowlist=["python", "nsfw"],
            subreddit_blocklist=["nsfw"],
        )
        assert cfg.is_subreddit_allowed("python") is True
        assert cfg.is_subreddit_allowed("nsfw") is False
