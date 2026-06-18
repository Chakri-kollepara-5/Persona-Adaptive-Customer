# Account Lockout Policy and Security Settings

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
* **Organization Owners**: If you are the primary owner and are unable to unlock your account, submit a ticket. For security compliance, support representatives will require multi-channel identity verification (e.g., verifying phone number and billing details) before manually unlocking an owner's account.\n