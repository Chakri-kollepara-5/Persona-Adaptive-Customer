import os
import sys

def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        import subprocess
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def generate_documents():
    # Ensure reportlab is installed before running
    install_and_import('reportlab')
    
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    # Directory setup
    output_dir = os.path.join("data", "support_docs")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory initialized at: {output_dir}")

    # 1. PDF File: password_reset_guide.pdf
    pdf_path = os.path.join(output_dir, "password_reset_guide.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom style for PDF body to support clean formatting
    body_style = ParagraphStyle(
        'KBBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=10
    )
    
    story = [
        Paragraph("SaaS Platform Support Guide: Password Reset and Multi-Factor Authentication", styles['Heading1']),
        Spacer(1, 12),
        Paragraph("<b>1. Standard Self-Service Password Reset Procedure</b>", styles['Heading2']),
        Paragraph("If you forgot your password or wish to update it, follow these steps:", body_style),
        Paragraph("1. Navigate to the login screen and click the 'Forgot Password' link below the login form.", body_style),
        Paragraph("2. Enter your registered email address and click 'Send Reset Link'.", body_style),
        Paragraph("3. Check your email inbox for a message from support@saasplatform.com. The email subject will be 'Reset Your Password'.", body_style),
        Paragraph("4. Click the link inside the email. Note that for security purposes, this password reset link is only active for 15 minutes.", body_style),
        Paragraph("5. Enter your new password, confirm it, and click 'Submit'. Your password must be at least 12 characters long, containing at least one uppercase letter, one lowercase letter, one number, and one special character.", body_style),
        Spacer(1, 10),
        Paragraph("<b>2. Troubleshooting Password Reset Link Issues</b>", styles['Heading2']),
        Paragraph("If you do not receive the email, please check your Spam or Junk folders. Some enterprise firewalls may delay or quarantine incoming automated emails; check with your IT administrator if the email does not arrive within 5 minutes. If the link is expired (showing an 'Expired Token' error), go back to the login page and trigger a new request.", body_style),
        Spacer(1, 10),
        Paragraph("<b>3. Multi-Factor Authentication (MFA / 2FA) Reset</b>", styles['Heading2']),
        Paragraph("If you have lost access to your MFA authentication app (e.g., Google Authenticator, Duo) and did not save your recovery codes, you will not be able to log in. In this scenario, you must contact your organization's Administrator. The Organization Admin can reset MFA for your user profile in the User Management settings panel. If you are the Owner or sole Admin of the account, you will need to contact our Customer Support team for manual security verification before we can reset your MFA configurations.", body_style)
    ]
    
    doc.build(story)
    print(f"Generated: {pdf_path}")

    # Define other files (TXT and MD)
    documents = {
        "api_authentication.md": """# API Authentication Guide

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
* **403 Forbidden**: The API key does not have the required permissions for the endpoint. Check the key scopes in the settings dashboard.
""",

        "billing_policy.txt": """SaaS Platform Billing Policy

1. Billing Cycles and Invoicing
All subscriptions are billed in advance on a recurring monthly or annual basis, depending on the plan selected during checkout.
Invoices are generated automatically on the first day of each billing cycle. A PDF copy of the invoice is sent to the registered billing email address and is also available in the dashboard under Settings > Billing > Invoice History.

2. Accepted Payment Methods
We accept major credit cards (Visa, MasterCard, American Express, Discover), ACH payments, and direct wire transfers (Enterprise subscriptions only). Payment information can be updated at any time by the Billing Owner in the console.

3. Grace Period and Dunning Process
If a payment fails, the system will automatically retry the card:
* Attempt 2: 3 days after first failure
* Attempt 3: 7 days after first failure
* Attempt 4 (Final): 14 days after first failure
During this 14-day grace period, your account remains active with a 'Payment Past Due' banner. If payment is not successfully processed by day 14, the account will be automatically suspended.

4. Sales Tax and Compliance
Prices shown are exclusive of VAT, GST, or local sales taxes. Taxes are calculated based on your corporate billing address and will be listed as a separate line item on the invoice where applicable.
""",

        "refund_policy.md": """# Refund Policy

## 30-Day Money-Back Guarantee
We want you to be completely satisfied with our platform. We offer a **30-day money-back guarantee** for all new subscriptions. If you are not satisfied with the software for any reason, you can request a full refund within 30 days of your initial purchase date.

## Refund Eligibility
* **First-time Subscriptions**: Refunds only apply to the initial purchase of a subscription plan. Subsequent monthly or annual renewals are not eligible for a refund.
* **Plan Upgrades**: Upgrading a plan is not eligible for a refund.
* **Enterprise Contracts**: Custom enterprise contracts are governed by their specific written agreement terms and are generally non-refundable unless specified.
* **Setup Fees**: Custom implementation or setup fees are non-refundable.

## Pro-rated Refunds
If you cancel your annual subscription after the 30-day window, you will not receive a refund. However, you will continue to have access to the platform services through the end of your prepaid billing period. We do not issue pro-rated refunds for unused partial billing cycles (e.g., canceling a monthly subscription midway through the month).

## Requesting a Refund
To request a refund, the Billing Owner must submit a formal request to support@saasplatform.com or file a support ticket from the dashboard under the 'Billing Support' category. Please include:
1. Account ID
2. Organization Name
3. Last 4 digits of the payment card or invoice number
4. Reason for cancellation (optional, but appreciated for feedback)

Approved refunds will be credited back to the original payment method within 5 to 10 business days depending on your bank.
""",

        "account_lockout.md": """# Account Lockout Policy and Security Settings

## Lockout Trigger
To protect our platform against brute-force and credential-stuffing attacks, we enforce a strict account lockout policy. 
* **Trigger**: If a user attempts to log in with an incorrect password **5 consecutive times**, their account will be automatically locked.
* **Lockout Duration**: The lockout is enforced for exactly **30 minutes**. During this window, any login attempts (even with the correct password) will be blocked and return an "Account Locked" error.

## Self-Service Unlock Procedure
After the 30-minute lockout window expires, the account is automatically unlocked, and the user can attempt to log in again.
If you need immediate access and cannot wait 30 minutes, you can unlock your account using the self-service method:
1. Click the **'Unlock Account'** link on the login error page.
2. Enter your registered email address.
3. An automated account unlock email will be sent containing a secure, single-use unlock code.
4. Enter the unlock code on the page to instantly clear the lockout and reset your failed attempts counter.

## Administrative Override
If the self-service unlock link is not working or you do not receive the unlock email:
* **Team Members**: Contact your organization's Admin. The admin can log in, go to the **User Management** panel, find your user record, and click **'Reset User Lockout'**.
* **Organization Owners**: If you are the primary owner and are unable to unlock your account, submit a ticket. For security compliance, support representatives will require multi-channel identity verification (e.g., verifying phone number and billing details) before manually unlocking an owner's account.
""",

        "integration_guide.md": """# Third-Party Integration and Database Sync Guide

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
* Check the integration error log in the developer dashboard for specific response error codes.
""",

        "dashboard_errors.md": """# Dashboard Error Code Troubleshooting Guide

If you experience unexpected behavior on the web dashboard, please check the error code displayed on the screen and apply the recommended troubleshooting steps below.

## Common Dashboard Errors

### Err-500: Internal Server Error
* **Description**: A temporary error on our server-side database or processing cluster.
* **Resolution**: 
  1. Wait 60 seconds and refresh your browser.
  2. Check our official status page (status.saasplatform.com) to verify service availability.
  3. Clear browser cache and cookies, then log in again.

### Err-404: Resource Not Found
* **Description**: The page, document, or workspace resource you are trying to access does not exist or has been deleted.
* **Resolution**:
  1. Double-check the URL format.
  2. Verify that another administrator did not delete the resource.
  3. Go to the dashboard home page and re-navigate to the item.

### Err-403: Forbidden Action
* **Description**: You do not have the necessary permissions to view this resource or perform this action.
* **Resolution**:
  1. Review your user role permissions (Settings > Team).
  2. If you are a Member or Viewer, contact your account Admin to upgrade your role to Editor or Billing Manager.
  3. Log out and log back in to force a refresh of your security tokens.

### Err-1002: Connection Timeout
* **Description**: The client browser was unable to establish a websocket or HTTP connection to our dashboard servers.
* **Resolution**:
  1. Check your internet connection.
  2. Ensure you are not behind a corporate proxy or VPN blocking websocket traffic (ports 80/443/8080).
  3. Try accessing the dashboard using cellular data or a different network.
""",

        "security_policy.md": """# Security Compliance and Data Protection Policy

## SOC2 Compliance
Our platform is fully SOC2 Type II audited and certified. We maintain strict physical, administrative, and technical safeguards to secure customer data.

## Data Encryption
* **In-Transit**: All data transmitted between user browsers and our API servers is encrypted using **TLS 1.3** and strong cipher suites.
* **At-Rest**: All customer data stored in our databases and file storage buckets is encrypted at rest using **AES-256** encryption keys, managed through AWS KMS.

## Single Sign-On (SSO) and Access Control
We support enterprise SSO integrations using **SAML 2.0** and **OpenID Connect (OIDC)**. To configure SSO:
1. Navigate to **Settings > Security > SSO Configuration**.
2. Upload your Identity Provider (IdP) metadata XML.
3. Map user attributes (Email, First Name, Last Name).
4. Enable 'Enforce SSO' to disable standard email/password logins for all organization users.

## Vulnerability Disclosure and Reporting
Security is our top priority. If you identify a potential security vulnerability in our platform, please do not exploit it. Report it immediately by emailing security@saasplatform.com. Include a detailed proof of concept. We do not offer public bug bounties but will provide official recognition and support for responsible disclosure.
""",

        "user_management.md": """# User Management and Organization Configuration

## Adding Team Members
To invite new members to your workspace:
1. Go to **Settings > Team Management**.
2. Click **Invite Member**.
3. Enter their email address and select their Role.
4. Click **Send Invitation**.
The invited user will receive an email link containing an invitation. They must click the link and register their profile within 7 days before the invitation token expires.

## User Roles and Permissions
We support five standard roles:
1. **Owner**: Full administrative control, billing ownership, ability to delete the workspace, and transfer ownership.
2. **Admin**: Can manage all users, billing profiles, integrations, and configurations. Cannot delete the workspace or demote the Owner.
3. **Editor**: Full read-and-write permissions on operational data. Cannot modify billing settings, API integrations, or manage team members.
4. **Billing Manager**: Exclusive permissions to update credit cards, pay invoices, and view billing history. Cannot modify operational data.
5. **Viewer**: Read-only access to dashboard statistics and configurations. Cannot make changes or view billing data.

## Custom Role Customization
Custom role mapping is exclusively available on the Enterprise plan. Enterprise admins can create granular permission policies (e.g., custom deployer role) under Settings > Roles > Create Custom Role.
""",

        "api_rate_limits.md": """# API Rate Limits and Backoff Policy

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
**Recommended Backoff Strategy**: When receiving an HTTP 429, check the `Retry-After` header or parse the `retry_after_seconds` value. Your client should temporarily pause operations and retry using exponential backoff with jitter to prevent server hammering.
""",

        "webhook_troubleshooting.md": """# Webhook Integration Troubleshooting Guide

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
Compare this against the computed HMAC of the raw request body. If the signature doesn't match, verify that your Webhook Secret Key has not been rotated or misconfigured.
""",

        "subscription_management.md": """# Subscription Management, Upgrades, and Cancellations

## Modifying Subscriptions
You can adjust your subscription level or billing interval (monthly or annual) at any time.
1. Navigate to **Settings > Billing > Subscription Plan**.
2. Review the feature grid and click **Upgrade Plan** or **Downgrade Plan** on your target tier.
3. If upgrading, the billing system computes the pro-rated difference and immediately charges your payment card. The upgraded features (e.g., higher API rate limits, SSO) are enabled instantly.
4. If downgrading, the downgrade remains pending until the end of your current billing period. Once the cycle resets, your plan updates, and future invoices reflect the lower rate.

## Account Cancellation
If you choose to cancel your subscription:
* Go to **Settings > Billing** and click **Cancel Subscription** at the bottom of the page.
* You will be asked to confirm the cancellation and complete a brief 3-question feedback survey.
* Upon completion, your account is scheduled for cancellation. Access will remain active until the end of your current billing cycle.
* **Important**: After your billing period ends, your account transitions to a suspended state. We retain your data for **90 days** post-cancellation, after which all database records, user profiles, and integrations are permanently deleted from our servers.

## Subscription Restoration
If your subscription is canceled or suspended due to payment failures, you can reactivate it within the 90-day retention window. Go to settings, update your payment card, and click 'Resume Subscription'.
""",

        "login_issues.md": """# Troubleshooting Common Login and Access Issues

If you are experiencing issues logging into the platform, please review this guide to identify the cause and apply the solution.

## 1. Credentials Mismatch / Forgotten Password
If you receive a "Invalid username or password" message:
* Verify that caps lock is turned off and you are typing your registered email address correctly.
* Try resetting your password using the 'Forgot Password' link. Note that passwords are case-sensitive.

## 2. SSO Authentication Errors
If your organization enforces Single Sign-On (SSO) and your login attempt fails:
* Ensure you click the "Log in with SSO" button instead of entering email/password.
* Contact your internal IT administrator to verify if your user profile is active in your Identity Provider (e.g., Okta, Azure AD).
* A common error is "SSO User Mapping Failed". This occurs when the email returned by your IdP does not match the email registered on our platform.

## 3. Browser Cache and Cookies Issues
Corrupted local storage or cookies can block authentication tokens:
* Open a private browsing session (Incognito window) and try logging in.
* If login succeeds in incognito, clear your main browser's cookies and site data for `app.saasplatform.com` and reload the page.
* Ensure third-party cookies are enabled in your browser settings, as they may be required for OAuth and authentication handshake protocols.
""",

        "data_export_guide.md": """# Workspace Data Export and Backup Procedures

## Manual Data Export
Organization Owners and Admins can export all workspace configuration, operational data, and activity logs at any time.

1. Navigate to **Settings > Workspace Settings > Data Export**.
2. Select the data categories you wish to export:
   * Users and Team Configurations (JSON)
   * Operational data / Transaction records (CSV)
   * Developer Logs and Audit Logs (CSV)
3. Click **Initiate Export**.
4. The system will compile the data. Depending on your database size, this can take between 5 to 30 minutes. Once completed, a secure download link will be emailed to you, and the file will appear in the export list. The link is active for 24 hours.

## Automated Daily Backups
Enterprise subscribers can schedule automated nightly backups:
* Backups are pushed directly to a customer-owned AWS S3 bucket or Google Cloud Storage bucket.
* To configure: Navigate to Settings > Integration > Backups, enter your cloud credentials, and specify the backup time.
* Data is exported in standardized JSON format, compressed using GZIP.

## Data Retention and Purging
* **Active Accounts**: We maintain live operational databases. Audit logs are retained for 1 year.
* **Canceled Accounts**: We retain account data for 90 days after subscription cancellation. Owners can download their final exports during this window. On day 91, all data is permanently purged from active systems and backups.
""",

        "team_permissions.md": """# Detailed Team Permissions and Role-Based Access Control (RBAC)

## RBAC System Overview
Our platform implements strict role-based access control (RBAC) to ensure that users have access only to the resources necessary for their job roles. Permissions are enforced at the API gateway level.

## Workspace Isolation
All workspaces are fully isolated. A user can be a member of multiple workspaces (e.g., Dev, Staging, Production) but must switch workspaces via the top dashboard menu. Permissions do not carry over between workspaces.

## Granular Permissions Grid
Here is the default matrix of permissions by user role:

| Action / Permission | Owner | Admin | Editor | Billing Manager | Viewer |
|---------------------|-------|-------|--------|-----------------|--------|
| Delete Workspace    | Yes   | No    | No     | No              | No     |
| Update Billing Card | Yes   | Yes   | No     | Yes             | No     |
| View Invoices       | Yes   | Yes   | No     | Yes             | Yes    |
| Invite New Users    | Yes   | Yes   | No     | No              | No     |
| Generate API Keys   | Yes   | Yes   | No     | No              | No     |
| Edit Webhooks       | Yes   | Yes   | No     | No              | No     |
| Edit Core Data      | Yes   | Yes   | Yes    | No              | No     |
| View Dashboard      | Yes   | Yes   | Yes    | Yes             | Yes    |

## Troubleshooting 'Permission Denied' Errors
If a user receives a "Permission Denied" pop-up or a `403 Forbidden` API response:
1. Verify the current active role under settings.
2. Ensure you are currently operating in the correct workspace.
3. If you need elevated access, contact the Owner or Admin of your workspace. They can change your role in Settings > Team Management by clicking the Edit icon next to your name.
"""
    }

    # Write other files
    for filename, content in documents.items():
        file_path = os.path.join(output_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\\n")
        print(f"Generated: {file_path}")

    print("Knowledge base documents generated successfully.")

if __name__ == "__main__":
    generate_documents()
