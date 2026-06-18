# User Management and Organization Configuration

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
Custom role mapping is exclusively available on the Enterprise plan. Enterprise admins can create granular permission policies (e.g., custom deployer role) under Settings > Roles > Create Custom Role.\n