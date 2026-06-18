# Detailed Team Permissions and Role-Based Access Control (RBAC)

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
3. If you need elevated access, contact the Owner or Admin of your workspace. They can change your role in Settings > Team Management by clicking the Edit icon next to your name.\n