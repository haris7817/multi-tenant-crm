"""
Slack connector (13.3).

Uses the tenant's Slack OAuth token from the Phase 12 connection framework
(stored encrypted) to post messages. ``_slack_post`` is the single HTTP call,
kept separate so tests can mock it.
"""
import json
import urllib.request

SLACK_POST_URL = "https://slack.com/api/chat.postMessage"


def _slack_post(token: str, channel: str, text: str) -> bool:
    body = json.dumps({"channel": channel, "text": text}).encode()
    req = urllib.request.Request(
        SLACK_POST_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return bool(data.get("ok"))


def channel_for(connection) -> str:
    return (connection.metadata or {}).get("channel", "#sales")
