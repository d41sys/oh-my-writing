# Parcel tracking migration: target design

Author: Hanna Berg (engineering director). Version 3, 20 July 2026.

## Why
TrackerLegacy, a single Java application on two on-premises servers, serves parcel tracking pages and takes scans from handheld scanners. Its Oracle database is at the end of vendor support on 31 October 2026. We are moving the service to a set of smaller components.

## Components (target)
- **Scan Ingest Worker**: receives scan messages from the handheld scanners and puts them on the queue.
- **RabbitMQ**: the queue between ingest, the Tracking API and the Notification Service.
- **Tracking API**: validates scans, writes them to the database, and answers tracking lookups from customers.
- **PostgreSQL**: the system of record for scans and parcels (replaces Oracle).
- **Redis**: caches tracking lookups for 30 seconds.
- **Notification Service**: reads scan events from RabbitMQ and sends SMS updates to customers.
- **Partner Export Job**: writes the nightly parcel file for the warehouse partner and uploads it by SFTP (replaces the cron export of TrackerLegacy).

## Data flow
1. A handheld scanner sends a scan to the Scan Ingest Worker.
2. The worker publishes it to RabbitMQ.
3. The Tracking API consumes it and writes to PostgreSQL.
4. The Notification Service consumes the same event and sends an SMS when the parcel is out for delivery.
5. A customer lookup goes to the Tracking API, which answers from Redis when it can and from PostgreSQL otherwise.
6. Every night the Partner Export Job reads PostgreSQL and uploads the partner file by SFTP.

## Migration approach
Dual-write rehearsals first, then one cutover window. TrackerLegacy stays available for rollback for 14 days after cutover, then is shut down.
