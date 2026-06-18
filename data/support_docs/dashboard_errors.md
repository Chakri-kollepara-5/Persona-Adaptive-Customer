# Dashboard Error Code Troubleshooting Guide

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
  3. Try accessing the dashboard using cellular data or a different network.\n