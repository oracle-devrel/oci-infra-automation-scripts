# Publish Disk Utilization as an OCI Custom Metric

This Python example reads disk utilization from `/` and sends the value to OCI Monitoring as the `disk_usage` metric in the `custom_metrics` namespace.

It is a standalone script intended to run on an OCI Compute instance. It uses instance principal authentication; it is not implemented as an OCI Function handler.

## Prerequisites

- Python 3.9 or later.
- An OCI Compute instance configured for instance principals.
- IAM permission for the instance's dynamic group to publish metrics in the target compartment.
- Network access to the OCI Monitoring ingestion endpoint for the target region.

## Configure

Before running the script, edit `func.py` and replace these placeholders:

- `your_compartment_ocid` with the compartment OCID that will own the metric.
- `srv01` with an appropriate resource display name.
- `https://telemetry-ingestion.ap-mumbai-1.oraclecloud.com` with the Monitoring ingestion endpoint for the intended OCI region, if different.

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Run

```bash
python3 func.py
```

The script prints the disk-utilization percentage and the OCI Monitoring API response. You can schedule it with `cron`, a systemd timer, or another host scheduler.

## Metric details

| Field | Value |
| --- | --- |
| Namespace | `custom_metrics` |
| Metric name | `disk_usage` |
| Value | Percentage of disk space used on `/` |
| Dimension | `resourceDisplayName` |

## Security notes

Use instance principals instead of a local OCI API-key configuration. Keep the dynamic group's Monitoring policy scoped to the required compartment and namespace.

## License

Licensed under the [Universal Permissive License 1.0](../LICENSE).
