# Security Compliance and Data Protection Policy

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
Security is our top priority. If you identify a potential security vulnerability in our platform, please do not exploit it. Report it immediately by emailing security@saasplatform.com. Include a detailed proof of concept. We do not offer public bug bounties but will provide official recognition and support for responsible disclosure.\n