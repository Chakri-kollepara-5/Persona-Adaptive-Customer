# API Authentication Guide

## Authentication Overview
All API requests to the SaaS platform must be authenticated. We use API keys passed in the HTTP authorization headers to authenticate requests.

## How to Authenticate
To authenticate an API request, include your secret API key in the `Authorization` header as a Bearer token:

```http
Authorization: Bearer YOUR_API_KEY
```

Replace `YOUR_API_KEY` with the actual key generated from your Developer Dashboard.

## Generating and Rotating Keys
1. Log in to the platform and navigate to **Settings > Developer Portal > API Keys**.
2. Click **Generate New Key**. Provide a descriptive name and select the permissions (Read-only, Read/Write, Admin).
3. Copy the key immediately. For security reasons, the full API key is only shown once and cannot be retrieved later.
4. **Key Rotation**: We recommend rotating API keys every 90 days. To rotate, generate a new key, update your services, verify successful authentication, and then delete the old key.

## Common Error Codes
* **401 Unauthorized**: The API key is missing, invalid, or expired. Double-check your authorization header format and ensure the key is active.
* **403 Forbidden**: The API key does not have the required permissions for the endpoint. Check the key scopes in the settings dashboard.\n