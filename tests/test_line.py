import base64
import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from rest_framework_simplejwt.tokens import RefreshToken

LINE_SECRET = 'test_channel_secret'
LINE_TOKEN = 'test_access_token'


def _make_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode('utf-8')


def _get_token(line_user):
    refresh = RefreshToken()
    refresh['line_user_id'] = line_user.line_user_id
    return str(refresh.access_token)


# ─── Webhook ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
@override_settings(LINE_CHANNEL_SECRET=LINE_SECRET)
def test_webhook_valid_signature(client):
    body = json.dumps({'events': []}).encode('utf-8')
    sig = _make_signature(LINE_SECRET, body)
    response = client.post(
        '/api/line/webhook/',
        data=body,
        content_type='application/json',
        HTTP_X_LINE_SIGNATURE=sig,
    )
    assert response.status_code == 200
    assert response.data['status'] == 'ok'


@pytest.mark.django_db
@override_settings(LINE_CHANNEL_SECRET=LINE_SECRET)
def test_webhook_invalid_signature(client):
    body = json.dumps({'events': []}).encode('utf-8')
    response = client.post(
        '/api/line/webhook/',
        data=body,
        content_type='application/json',
        HTTP_X_LINE_SIGNATURE='invalidsignature==',
    )
    assert response.status_code == 401


@pytest.mark.django_db
@override_settings(LINE_CHANNEL_SECRET=LINE_SECRET)
def test_webhook_missing_signature(client):
    body = json.dumps({'events': []}).encode('utf-8')
    response = client.post(
        '/api/line/webhook/',
        data=body,
        content_type='application/json',
    )
    assert response.status_code == 401


@pytest.mark.django_db
@override_settings(LINE_CHANNEL_SECRET=LINE_SECRET)
def test_webhook_follow_event(client):
    payload = {
        'events': [{
            'type': 'follow',
            'replyToken': 'test_reply_token',
            'source': {'type': 'user', 'userId': 'U12345'},
        }]
    }
    body = json.dumps(payload).encode('utf-8')
    sig = _make_signature(LINE_SECRET, body)
    response = client.post(
        '/api/line/webhook/',
        data=body,
        content_type='application/json',
        HTTP_X_LINE_SIGNATURE=sig,
    )
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(LINE_CHANNEL_SECRET=LINE_SECRET)
def test_webhook_message_event(client):
    payload = {
        'events': [{
            'type': 'message',
            'replyToken': 'test_reply_token',
            'source': {'type': 'user', 'userId': 'U12345'},
            'message': {'type': 'text', 'text': 'Hello'},
        }]
    }
    body = json.dumps(payload).encode('utf-8')
    sig = _make_signature(LINE_SECRET, body)
    response = client.post(
        '/api/line/webhook/',
        data=body,
        content_type='application/json',
        HTTP_X_LINE_SIGNATURE=sig,
    )
    assert response.status_code == 200


# ─── Push ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
@override_settings(LINE_CHANNEL_SECRET=LINE_SECRET, LINE_CHANNEL_ACCESS_TOKEN=LINE_TOKEN)
def test_push_text_message(client, line_user):
    token = _get_token(line_user)
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = lambda: None
    with patch('foodlocker.line_service.requests.post', return_value=mock_resp):
        response = client.post(
            '/api/line/push/',
            data=json.dumps({'to': 'U12345', 'message': 'Hello'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
    assert response.status_code == 200
    assert response.data['status'] == 'ok'


@pytest.mark.django_db
def test_push_requires_auth(client):
    response = client.post(
        '/api/line/push/',
        data=json.dumps({'to': 'U12345', 'message': 'Hello'}),
        content_type='application/json',
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_push_missing_to(client, line_user):
    token = _get_token(line_user)
    response = client.post(
        '/api/line/push/',
        data=json.dumps({'message': 'Hello'}),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 400
