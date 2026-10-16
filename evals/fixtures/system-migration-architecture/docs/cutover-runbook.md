# Cutover runbook: TrackerLegacy to the new tracking service

Window: Saturday 15 August 2026, 02:00 to 06:00. Incident lead: Sven Aalto.

## Steps
1. 02:00: stop scanner traffic at the handhelds' gateway; TrackerLegacy goes read-only.
2. 02:10: run the final Oracle to PostgreSQL copy of parcels and scans.
3. 02:50: verify row counts on both sides; they must match.
4. 03:10: switch the handhelds to the Scan Ingest Worker.
5. 03:20: switch the customer tracking pages to the Tracking API.
6. 03:30: enable the Notification Service and the Partner Export Job.
7. 04:00: smoke tests, then announce.

## Rollback
Roll back if the Tracking API error rate stays above 2% for 10 minutes, or if row counts do not match at step 3. Rollback means switching the handhelds and the tracking pages back to TrackerLegacy and re-enabling its writes. Decision owner: Hanna Berg.
