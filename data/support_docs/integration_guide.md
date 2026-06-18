# Third-Party Integration and Database Sync Guide

## Integration Architecture
Our platform supports seamless integration with databases, data warehouses, and CRMs. Integrations are managed via OAuth 2.0 authentication or secret connector tokens.

## Step-by-Step Webhook Setup
Webhooks enable real-time notifications to your application server whenever an event occurs on your SaaS workspace (e.g., user created, payment completed).

1. Log in and navigate to **Settings > Integrations > Webhooks**.
2. Click **Add Endpoint**.
3. Input your destination server URL (must support HTTPS).
4. Select the event triggers you want to listen to (e.g., `user.created`, `invoice.paid`).
5. Copy the **Webhook Secret Key** generated. You will use this key to verify payload authenticity.
6. Click **Save Webhook**.

## Code Snippet: Webhook Signature Verification (Python)
To ensure webhook payloads are actually sent by our server, you must verify the signature included in the `X-Platform-Signature` header:

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)
```

## Troubleshooting Integrations
If data is not syncing:
* Check your target server's log for incoming requests.
* Ensure your server responds to webhook events with a `200 OK` status code within 5 seconds.
* Check the integration error log in the developer dashboard for specific response error codes.\n