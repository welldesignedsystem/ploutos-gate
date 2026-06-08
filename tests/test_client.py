from unittest.mock import MagicMock, patch

import praw.models
import pytest

from reddit.client import RedditClient
from reddit.config import RedditConfig


@pytest.fixture
def mock_praw():
    with patch("reddit.client.praw.Reddit") as mock:
        yield mock


@pytest.fixture
def config():
    return RedditConfig(
        client_id="test-id",
        client_secret="test-secret",
    )


@pytest.fixture
def client(config, mock_praw):
    return RedditClient(config)


def make_mock_submission(**kwargs):
    sub = MagicMock()
    sub.id = kwargs.get("id", "abc123")
    sub.title = kwargs.get("title", "Test Post")
    sub.author = MagicMock()
    sub.author.__str__.return_value = kwargs.get("author", "testuser")
    sub.score = kwargs.get("score", 42)
    sub.upvote_ratio = kwargs.get("upvote_ratio", 0.95)
    sub.num_comments = kwargs.get("num_comments", 10)
    sub.url = kwargs.get("url", "https://reddit.com/r/test/comments/abc123")
    sub.permalink = kwargs.get("permalink", "/r/test/comments/abc123/test_post/")
    sub.selftext = kwargs.get("selftext", "")
    sub.created_utc = kwargs.get("created_utc", 1717000000.0)
    sub.subreddit = MagicMock()
    sub.subreddit.display_name = kwargs.get("subreddit", "test")
    return sub


def make_mock_comment(**kwargs):
    c = MagicMock(spec=praw.models.Comment)
    c.id = kwargs.get("id", "def456")
    c.author = MagicMock()
    c.author.__str__.return_value = kwargs.get("author", "commenter")
    c.body = kwargs.get("body", "Great post!")
    c.score = kwargs.get("score", 5)
    c.created_utc = kwargs.get("created_utc", 1717000100.0)
    return c


class TestRedditClientInit:
    def test_creates_praw_instance(self, mock_praw, config):
        RedditClient(config)
        mock_praw.assert_called_once_with(
            client_id="test-id",
            client_secret="test-secret",
            user_agent="ploutos-gate:1.0.0 (by /u/ploutos-gate-bot)",
            username=None,
            password=None,
        )

    def test_uses_env_config_when_none_provided(self, mock_praw):
        RedditClient()
        mock_praw.assert_called_once()


class TestSubredditFiltering:
    def test_blocked_subreddit_raises(self, client):
        client.config.subreddit_blocklist = ["blocked"]
        with pytest.raises(PermissionError, match="Subreddit r/blocked"):
            client.search_posts("query", subreddit="blocked")

    def test_allowlist_restricts_search(self, client):
        client.config.subreddit_allowlist = ["allowed"]
        with pytest.raises(PermissionError, match="not allowed"):
            client.search_posts("query", subreddit="notallowed")

    def test_allowed_subreddit_passes(self, client, mock_praw):
        client.config.subreddit_allowlist = ["allowed"]
        client.search_posts("query", subreddit="allowed")
        assert True  # no PermissionError


class TestSearchPosts:
    def test_calls_praw_search(self, client, mock_praw):
        mock_sub = make_mock_submission()
        mock_praw.return_value.subreddit.return_value.search.return_value = [mock_sub]

        result = client.search_posts("test query", subreddit="python", limit=5, time_filter="year")

        mock_praw.return_value.subreddit.assert_called_with("python")
        mock_praw.return_value.subreddit.return_value.search.assert_called_with(
            "test query", sort="relevance", limit=5, time_filter="year"
        )
        assert len(result) == 1
        assert result[0]["title"] == "Test Post"

    def test_searches_all_when_no_subreddit(self, client, mock_praw):
        mock_praw.return_value.subreddit.return_value.search.return_value = []
        client.search_posts("query")
        mock_praw.return_value.subreddit.assert_called_with("all")


class TestGetPost:
    def test_returns_post_with_comments(self, client, mock_praw):
        mock_sub = make_mock_submission()
        mock_comment = make_mock_comment()
        mock_sub.comments.replace_more = MagicMock()
        mock_sub.comments.list.return_value = [mock_comment]
        mock_praw.return_value.submission.return_value = mock_sub

        result = client.get_post("abc123")

        mock_praw.return_value.submission.assert_called_with(id="abc123")
        assert result["title"] == "Test Post"
        assert len(result["comments"]) == 1
        assert result["comments"][0]["body"] == "Great post!"

    def test_handles_deleted_author(self, client, mock_praw):
        mock_sub = make_mock_submission()
        mock_sub.author = None
        mock_sub.comments.replace_more = MagicMock()
        mock_sub.comments.list.return_value = []
        mock_praw.return_value.submission.return_value = mock_sub

        result = client.get_post("abc123")
        assert result["author"] == "[deleted]"  # via _post_to_dict


class TestReadSubreddit:
    def test_defaults_to_hot(self, client, mock_praw):
        mock_sub = make_mock_submission()
        mock_praw.return_value.subreddit.return_value.hot.return_value = [mock_sub]

        result = client.read_subreddit("python")

        assert len(result) == 1

    def test_top_with_time_filter(self, client, mock_praw):
        mock_praw.return_value.subreddit.return_value.top.return_value = []
        client.read_subreddit("python", sort="top", time_filter="month")
        mock_praw.return_value.subreddit.return_value.top.assert_called_with(
            limit=25, time_filter="month"
        )

    def test_new_no_time_filter(self, client, mock_praw):
        mock_praw.return_value.subreddit.return_value.new.return_value = []
        client.read_subreddit("python", sort="new")
        mock_praw.return_value.subreddit.return_value.new.assert_called_with(limit=25)

    def test_unknown_sort_falls_back_to_hot(self, client, mock_praw):
        result = client.read_subreddit("python", sort="invalid_sort")
        assert result == []


class TestSubredditInfo:
    def test_fetches_subreddit_metadata(self, client, mock_praw):
        mock_sub = MagicMock()
        mock_sub.display_name = "python"
        mock_sub.title = "Python"
        mock_sub.public_description = "All things Python"
        mock_sub.subscribers = 900000
        mock_sub.active_user_count = 50000
        mock_sub.created_utc = 1200000000.0
        mock_sub.over18 = False
        mock_praw.return_value.subreddit.return_value = mock_sub

        result = client.subreddit_info("python")

        assert result["display_name"] == "python"
        assert result["subscribers"] == 900000
        assert result["over18"] is False
        mock_sub._fetch.assert_called_once()


class TestUserInfo:
    def test_fetches_user_data(self, client, mock_praw):
        mock_user = MagicMock()
        mock_user.name = "testuser"
        mock_user.comment_karma = 100
        mock_user.link_karma = 50
        mock_user.created_utc = 1500000000.0
        mock_user.is_employee = False
        mock_user.is_mod = True
        mock_praw.return_value.redditor.return_value = mock_user

        result = client.user_info("testuser")

        assert result["name"] == "testuser"
        assert result["is_mod"] is True
        mock_user._fetch.assert_called_once()


class TestCreatePost:
    def test_self_post(self, client, mock_praw):
        mock_sub = make_mock_submission(title="Hello", subreddit="python")
        mock_praw.return_value.subreddit.return_value.submit.return_value = mock_sub

        result = client.create_post("python", "Hello", text="World")

        mock_praw.return_value.subreddit.return_value.submit.assert_called_with(
            "Hello", selftext="World"
        )
        assert result["title"] == "Hello"

    def test_link_post(self, client, mock_praw):
        mock_sub = make_mock_submission(title="Link")
        mock_praw.return_value.subreddit.return_value.submit.return_value = mock_sub

        client.create_post("python", "Link", url="https://example.com")

        mock_praw.return_value.subreddit.return_value.submit.assert_called_with(
            "Link", url="https://example.com"
        )


class TestReply:
    def test_reply_to_submission(self, client, mock_praw):
        mock_item = MagicMock()
        mock_reply = MagicMock()
        mock_reply.id = "xyz789"
        mock_reply.body = "Nice!"
        mock_reply.created_utc = 1717000200.0
        mock_item.reply.return_value = mock_reply
        mock_praw.return_value.submission.return_value = mock_item

        result = client.reply("abcdef", "Nice!")

        mock_praw.return_value.submission.assert_called_with(id="abcdef")
        assert result["id"] == "xyz789"

    def test_reply_to_comment(self, client, mock_praw):
        mock_item = MagicMock()
        mock_reply = MagicMock()
        mock_reply.id = "xyz789"
        mock_reply.body = "Thanks!"
        mock_reply.created_utc = 1717000300.0
        mock_item.reply.return_value = mock_reply
        mock_praw.return_value.comment.return_value = mock_item

        result = client.reply("abcde", "Thanks!")  # < 6 chars = comment

        mock_praw.return_value.comment.assert_called_with(id="abcde")
        assert result["id"] == "xyz789"


class TestTrackMentions:
    def test_searches_all_subreddits(self, client, mock_praw):
        mock_sub = make_mock_submission(subreddit="python")
        mock_praw.return_value.subreddit.return_value.search.return_value = [mock_sub]

        result = client.track_mentions(["python"], limit=10, time_filter="week")

        assert len(result) == 1
        assert result[0]["keyword"] == "python"
        assert result[0]["subreddit"] == "python"

    def test_searches_specific_subreddits(self, client, mock_praw):
        mock_praw.return_value.subreddit.return_value.search.return_value = []
        client.track_mentions(["rust"], subreddits=["rust", "programming"])
        assert mock_praw.return_value.subreddit.call_count == 2


class TestThrottle:
    def test_throttle_sleeps_when_called_too_soon(self, client, mock_praw):
        with patch("reddit.client.time") as mock_time:
            mock_time.time.side_effect = [0.0, 0.0]  # two calls, 0 elapsed
            client._throttle()
            mock_time.sleep.assert_called_once_with(1.0)

    def test_throttle_does_not_sleep_when_enough_time_passed(self, client, mock_praw):
        client._last_call = 5.0
        with patch("reddit.client.time") as mock_time:
            mock_time.time.return_value = 7.0  # 2s elapsed since last_call
            client._throttle()
            mock_time.sleep.assert_not_called()
