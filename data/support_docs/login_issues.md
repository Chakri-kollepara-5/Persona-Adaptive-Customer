# Troubleshooting Common Login and Access Issues

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
* Ensure third-party cookies are enabled in your browser settings, as they may be required for OAuth and authentication handshake protocols.\n