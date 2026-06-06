import time
from collections.abc import Generator

import praw
import praw.models

from .config import RedditConfig


class RedditClient:
    def __init__(self, config: RedditConfig | None = None):
        self.config = config or RedditConfig.from_env()
        self._praw = praw.Reddit(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            user_agent=self.config.user_agent,
            username=self.config.username or None,
            password=self.config.password or None,
        )
        self._last_call = 0.0

    def _throttle(self):
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self._last_call = time.time()

    def _check_subreddit(self, name: str):
        if not self.config.is_subreddit_allowed(name):
            raise PermissionError(f"Subreddit r/{name} is not allowed")

    def search_posts(
        self, query: str, subreddit: str | None = None, sort: str = "relevance",
        limit: int = 10, time_filter: str = "all",
    ) -> list[dict]:
        self._throttle()
        if subreddit:
            self._check_subreddit(subreddit)
            results = self._praw.subreddit(subreddit).search(query, sort=sort, limit=limit, time_filter=time_filter)
        else:
            results = self._praw.subreddit("all").search(query, sort=sort, limit=limit, time_filter=time_filter)
        return [self._post_to_dict(p) for p in results]

    def get_post(self, post_id: str) -> dict:
        self._throttle()
        submission = self._praw.submission(id=post_id)
        submission.comments.replace_more(limit=0)
        comments = []
        for c in submission.comments.list():
            if isinstance(c, praw.models.Comment):
                comments.append({
                    "id": c.id,
                    "author": str(c.author) if c.author else "[deleted]",
                    "body": c.body,
                    "score": c.score,
                    "created_utc": c.created_utc,
                })
        return {
            **self._post_to_dict(submission),
            "comments": comments,
        }

    def read_subreddit(
        self, subreddit: str, sort: str = "hot", limit: int = 25,
        time_filter: str | None = None,
    ) -> list[dict]:
        self._check_subreddit(subreddit)
        self._throttle()
        sub = self._praw.subreddit(subreddit)
        method = getattr(sub, sort, sub.hot)
        kwargs = {"limit": limit}
        if sort in ("top", "controversial") and time_filter:
            kwargs["time_filter"] = time_filter
        return [self._post_to_dict(p) for p in method(**kwargs)]

    def subreddit_info(self, subreddit: str) -> dict:
        self._check_subreddit(subreddit)
        self._throttle()
        sub = self._praw.subreddit(subreddit)
        sub._fetch()
        return {
            "display_name": sub.display_name,
            "title": sub.title,
            "description": sub.public_description,
            "subscribers": sub.subscribers,
            "active_user_count": sub.active_user_count,
            "created_utc": sub.created_utc,
            "over18": sub.over18,
        }

    def user_info(self, username: str) -> dict:
        self._throttle()
        user = self._praw.redditor(name=username)
        user._fetch()
        return {
            "name": user.name,
            "comment_karma": user.comment_karma,
            "link_karma": user.link_karma,
            "created_utc": user.created_utc,
            "is_employee": user.is_employee,
            "is_mod": user.is_mod,
        }

    def create_post(self, subreddit: str, title: str, text: str | None = None, url: str | None = None) -> dict:
        self._check_subreddit(subreddit)
        self._throttle()
        sub = self._praw.subreddit(subreddit)
        if url:
            submission = sub.submit(title, url=url)
        else:
            submission = sub.submit(title, selftext=text or "")
        return self._post_to_dict(submission)

    def reply(self, parent_id: str, body: str) -> dict:
        self._throttle()
        item = self._praw.submission(id=parent_id) if len(parent_id) >= 6 else self._praw.comment(id=parent_id)
        reply = item.reply(body)
        return {
            "id": reply.id,
            "body": reply.body,
            "created_utc": reply.created_utc,
        }

    def track_mentions(
        self, keywords: list[str], subreddits: list[str] | None = None,
        limit: int = 100, time_filter: str = "week",
    ) -> list[dict]:
        results = []
        sources = subreddits or ["all"]
        for kw in keywords:
            for src in sources:
                if src != "all":
                    self._check_subreddit(src)
                self._throttle()
                for post in self._praw.subreddit(src).search(kw, limit=limit, time_filter=time_filter):
                    results.append({
                        "keyword": kw,
                        "subreddit": post.subreddit.display_name,
                        **self._post_to_dict(post),
                    })
        return results

    @staticmethod
    def _post_to_dict(post: praw.models.Submission) -> dict:
        return {
            "id": post.id,
            "title": post.title,
            "author": str(post.author) if post.author else "[deleted]",
            "score": post.score,
            "upvote_ratio": post.upvote_ratio,
            "num_comments": post.num_comments,
            "url": post.url,
            "permalink": post.permalink,
            "selftext": getattr(post, "selftext", "")[:500],
            "created_utc": post.created_utc,
            "subreddit": post.subreddit.display_name,
        }
