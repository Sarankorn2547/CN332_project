import base64
import hashlib
import hmac

import requests
from django.conf import settings


class LineService:
    PUSH_URL = 'https://api.line.me/v2/bot/message/push'

    @staticmethod
    def verify_signature(body: bytes, signature: str) -> bool:
        """Verify X-Line-Signature using HMAC-SHA256."""
        secret = settings.LINE_CHANNEL_SECRET.encode('utf-8')
        digest = hmac.new(secret, body, hashlib.sha256).digest()
        expected = base64.b64encode(digest).decode('utf-8')
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def push_text(to: str, text: str) -> dict:
        return LineService._push(to, [{'type': 'text', 'text': text}])

    @staticmethod
    def push_image(to: str, image_url: str) -> dict:
        msg = {
            'type': 'image',
            'originalContentUrl': image_url,
            'previewImageUrl': image_url,
        }
        return LineService._push(to, [msg])

    @staticmethod
    def push_text_and_image(to: str, text: str, image_url: str) -> dict:
        messages = [
            {'type': 'text', 'text': text},
            {
                'type': 'image',
                'originalContentUrl': image_url,
                'previewImageUrl': image_url,
            },
        ]
        return LineService._push(to, messages)

    @staticmethod
    def _push(to: str, messages: list) -> dict:
        headers = {
            'Authorization': f'Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json',
        }
        resp = requests.post(
            LineService.PUSH_URL,
            json={'to': to, 'messages': messages},
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()
