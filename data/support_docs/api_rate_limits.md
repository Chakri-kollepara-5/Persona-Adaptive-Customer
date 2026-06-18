# API Rate Limits and Backoff Policy

## Rate Limit Tiers
To ensure service reliability and prevent abuse of our API infrastructure, we enforce rate limits on all incoming requests. Rate limits are calculated on a per-minute rolling window basis.

* **Free Trial Plan**: 60 requests per minute (RPM)
* **Growth Plan**: 600 requests per minute (RPM)
* **Enterprise Plan**: 6,000 requests per minute (RPM)

## Rate Limit Response Headers
Every API response includes metadata headers indicating your current usage limits:
* `X-RateLimit-Limit`: The total number of requests permitted per minute.
* `X-RateLimit-Remaining`: The remaining number of requests allowed in the current 1-minute window.
* `X-RateLimit-Reset`: The UNIX timestamp indicating when the current rate limit window resets.

## Handling HTTP 429 Errors
If you exceed your rate limit, the API will reject subsequent requests and return an `HTTP 429 Too Many Requests` status code. The response body will contain:
```json
{
  "error": "Rate limit exceeded. Please try again later.",
  "retry_after_seconds": 12
}
```
**Recommended Backoff Strategy**: When receiving an HTTP 429, check the `Retry-After` header or parse the `retry_after_seconds` value. Your client should temporarily pause operations and retry using exponential backoff with jitter to prevent server hammering.\n