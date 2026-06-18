# Webhook Integration Troubleshooting Guide

Webhooks send automated, HTTP POST payloads to your application server when events happen. If you are not receiving webhook events, follow this diagnostic checklist.

## Webhook Delivery Rules
* **Timeout**: Our server expects a response within **5 seconds**. If your endpoint does not respond within this window, we record a timeout failure.
* **Acceptable Status Codes**: To mark a delivery as successful, your endpoint must return a **2xx status code** (e.g., `200 OK`, `202 Accepted`). Redirection codes (3xx) or error codes (4xx/5xx) are treated as delivery failures.

## Automatic Retry Schedule
If a webhook delivery fails, our platform schedules automatic retries using exponential backoff:
1. **Attempt 2**: 2 minutes after initial failure.
2. **Attempt 3**: 15 minutes after initial failure.
3. **Attempt 4**: 1 hour after initial failure.
4. **Attempt 5 (Final)**: 6 hours after initial failure.
If all 5 attempts fail, the webhook status is marked as 'Failed' in the developer dashboard, and delivery is deactivated for that specific event ID.

## Verification of Payload Security (HMAC-SHA256)
Ensure your endpoint is validating the request signature. The signature is computed using your Webhook Secret Key:
* Header: `X-Hub-Signature-256`
* Format: `sha256=HEX_ENCODED_SIGNATURE`
Compare this against the computed HMAC of the raw request body. If the signature doesn't match, verify that your Webhook Secret Key has not been rotated or misconfigured.\n