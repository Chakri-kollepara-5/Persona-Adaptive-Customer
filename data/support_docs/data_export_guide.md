# Workspace Data Export and Backup Procedures

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
* **Canceled Accounts**: We retain account data for 90 days after subscription cancellation. Owners can download their final exports during this window. On day 91, all data is permanently purged from active systems and backups.\n