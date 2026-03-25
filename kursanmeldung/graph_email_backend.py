"""
Custom Django E-Mail-Backend für Microsoft Graph API (App-only / client credentials).

Benötigte .env-Einstellungen:
    EMAIL_BACKEND=kursanmeldung.graph_email_backend.GraphEmailBackend
    MS_TENANT_ID=<dein-Azure-Tenant-ID>
    MS_CLIENT_ID=<App-Registrierung Client-ID>
    MS_CLIENT_SECRET=<App-Registrierung Client-Secret>
    MS_SENDER=<absender@domain.de>  # lizenziertes Postfach mit Mail.Send-Berechtigung

Benötigte API-Berechtigung in der Azure App-Registrierung:
    Graph API → Application permissions → Mail.Send
"""

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class GraphEmailBackend(BaseEmailBackend):
    """Sendet E-Mails über Microsoft Graph API mit App-only-Authentifizierung."""

    def _get_access_token(self) -> str:
        tenant_id     = getattr(settings, 'MS_TENANT_ID', '')
        client_id     = getattr(settings, 'MS_CLIENT_ID', '')
        client_secret = getattr(settings, 'MS_CLIENT_SECRET', '')

        if not all([tenant_id, client_id, client_secret]):
            raise RuntimeError(
                'Microsoft Graph nicht konfiguriert. '
                'MS_TENANT_ID, MS_CLIENT_ID und MS_CLIENT_SECRET in .env setzen.'
            )

        resp = requests.post(
            f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
            data={
                'grant_type':    'client_credentials',
                'client_id':     client_id,
                'client_secret': client_secret,
                'scope':         'https://graph.microsoft.com/.default',
            },
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.json().get('access_token', '')
        if not token:
            raise RuntimeError(f'Kein Access-Token erhalten: {resp.text}')
        return token

    def send_messages(self, email_messages) -> int:
        if not email_messages:
            return 0

        sender = getattr(settings, 'MS_SENDER', getattr(settings, 'DEFAULT_FROM_EMAIL', ''))

        try:
            token = self._get_access_token()
        except Exception as exc:
            if not self.fail_silently:
                raise
            return 0

        sent = 0
        for msg in email_messages:
            content_type = 'HTML' if getattr(msg, 'content_subtype', 'plain') == 'html' else 'Text'

            payload = {
                'message': {
                    'subject': msg.subject,
                    'body': {
                        'contentType': content_type,
                        'content': msg.body,
                    },
                    'toRecipients': [
                        {'emailAddress': {'address': addr}} for addr in msg.to
                    ],
                },
                'saveToSentItems': False,
            }

            if msg.cc:
                payload['message']['ccRecipients'] = [
                    {'emailAddress': {'address': addr}} for addr in msg.cc
                ]
            if msg.bcc:
                payload['message']['bccRecipients'] = [
                    {'emailAddress': {'address': addr}} for addr in msg.bcc
                ]

            try:
                resp = requests.post(
                    f'https://graph.microsoft.com/v1.0/users/{sender}/sendMail',
                    json=payload,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json',
                    },
                    timeout=15,
                )
                if resp.status_code == 202:
                    sent += 1
                else:
                    if not self.fail_silently:
                        raise RuntimeError(
                            f'Graph API Fehler {resp.status_code}: {resp.text}'
                        )
            except Exception:
                if not self.fail_silently:
                    raise

        return sent
