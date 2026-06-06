# reddit — Reddit MCP module

FastMCP server exposing Reddit API as MCP tools. Built on PRAW.

## Tools

| Tool | Action |
|------|--------|
| `reddit_search_posts` | Search posts by keyword |
| `reddit_get_post` | Fetch post + top comments |
| `reddit_read_subreddit` | Browse subreddit (hot/new/top) |
| `reddit_subreddit_info` | Subreddit metadata |
| `reddit_user_info` | User karma and stats |
| `reddit_create_post` | Submit text/link post |
| `reddit_reply` | Reply to post/comment |
| `reddit_track_mentions` | Track keywords across subreddits |

## Run

```bash
python -m reddit.server
```

Serves on `http://localhost:8000` with `streamable-http` transport.

## Env vars

| Variable | Required | For |
|----------|----------|-----|
| `REDDIT_CLIENT_ID` | Yes | Auth |
| `REDDIT_CLIENT_SECRET` | Yes | Auth |
| `REDDIT_USERNAME` | Write ops | Posting/replying |
| `REDDIT_PASSWORD` | Write ops | Posting/replying |
| `REDDIT_SUBREDDIT_ALLOWLIST` | No | Restrict to subreddits |
| `REDDIT_SUBREDDIT_BLOCKLIST` | No | Exclude subreddits |

## Files

- `server.py` — FastMCP app entrypoint
- `client.py` — PRAW wrapper with 1 req/s throttle
- `config.py` — RedditConfig from env vars
- `tools/` — one module per tool category
