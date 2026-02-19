"""Slack integration for news moderation workflow."""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import requests


class SlackModerator:
    """Send news to Slack for moderation with approve/reject buttons."""

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Slack moderator.

        Args:
            webhook_url: Slack webhook URL (defaults to env var SLACK_WEBHOOK_URL)
        """
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')
        if not self.webhook_url:
            raise ValueError("SLACK_WEBHOOK_URL must be set")

    def send_for_moderation(
        self,
        news_items: List[Dict],
        channel: Optional[str] = None
    ) -> Dict:
        """Send news items to Slack for moderation.

        Args:
            news_items: List of news items with title, summary, url, hot_score, etc.
            channel: Optional Slack channel (overrides webhook default)

        Returns:
            Response from Slack API with message timestamp
        """
        if not news_items:
            return {"ok": False, "error": "No news items to send"}

        blocks = self._build_message_blocks(news_items)

        payload = {
            "blocks": blocks,
            "text": f"📰 {len(news_items)} news items for moderation"
        }

        if channel:
            payload["channel"] = channel

        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            return {
                "ok": False,
                "error": f"Slack API error: {response.status_code} - {response.text}"
            }

        return {"ok": True, "response": response.text}

    def _build_message_blocks(self, news_items: List[Dict]) -> List[Dict]:
        """Build Slack Block Kit message blocks.

        Args:
            news_items: List of news items

        Returns:
            List of Slack blocks
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📰 {len(news_items)} Hot News for Moderation",
                    "emoji": True
                }
            },
            {
                "type": "divider"
            }
        ]

        for i, item in enumerate(news_items, 1):
            # News item section
            hot_score = item.get('hot_score', 0)
            score_emoji = self._get_score_emoji(hot_score)

            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*#{i}. {item.get('title', 'No title')}*\n\n"
                            f"{item.get('summary', 'No summary')[:300]}...\n\n"
                            f"{score_emoji} *Hot Score:* {hot_score:.2f} | "
                            f"📅 {item.get('published', 'Unknown date')}\n"
                            f"🔗 <{item.get('url', '#')}|Read original>"
                        )
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Rewritten post:*\n```{item.get('rewritten_text', 'N/A')}```"
                    }
                },
                {
                    "type": "actions",
                    "block_id": f"news_{i}",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Approve",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": json.dumps({
                                "action": "approve",
                                "news_id": item.get('id', i),
                                "url": item.get('url')
                            }),
                            "action_id": f"approve_{i}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "❌ Reject",
                                "emoji": True
                            },
                            "style": "danger",
                            "value": json.dumps({
                                "action": "reject",
                                "news_id": item.get('id', i),
                                "url": item.get('url')
                            }),
                            "action_id": f"reject_{i}"
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ])

        # Add footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 🤖 AI News Curator"
                }
            ]
        })

        return blocks

    def _get_score_emoji(self, score: float) -> str:
        """Get emoji for hot score visualization.

        Args:
            score: Hot score value (0-1)

        Returns:
            Emoji string
        """
        if score >= 0.7:
            return "🔥"
        elif score >= 0.5:
            return "🌡️"
        elif score >= 0.3:
            return "📊"
        else:
            return "❄️"

    def send_simple_message(self, text: str, channel: Optional[str] = None) -> Dict:
        """Send a simple text message to Slack.

        Args:
            text: Message text
            channel: Optional Slack channel

        Returns:
            Response from Slack API
        """
        payload = {"text": text}
        if channel:
            payload["channel"] = channel

        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            return {
                "ok": False,
                "error": f"Slack API error: {response.status_code} - {response.text}"
            }

        return {"ok": True, "response": response.text}


def send_moderation_request(news_items: List[Dict]) -> Dict:
    """Helper function to send news for moderation.

    Args:
        news_items: List of news items

    Returns:
        Response from Slack API
    """
    moderator = SlackModerator()
    return moderator.send_for_moderation(news_items)
