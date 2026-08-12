# Email-Friendly OCI Event Notifications

An OCI Function that receives an OCI event payload and sends a branded HTML email through OCI Email Delivery. It includes selected event and resource details in the message body and attaches the full JSON event payload.

The recipient is read from the event tag `custom.recipient` when present; otherwise the function uses the configured default recipient.

## Prerequisites

- OCI Functions application and Fn CLI.
- OCI Email Delivery with an approved sender and SMTP credentials.
- An OCI Vault secret containing the SMTP password.
- An OCI event rule that invokes the function.
- A dynamic group for the function with permission to read the Vault secret.

## Function configuration

Set the following function configuration values. `smtppass` must be the OCID of a Vault secret, not the SMTP password itself.

| Name | Description |
| --- | --- |
| `smtpuser` | OCI Email Delivery SMTP username. |
| `smtppass` | OCID of the Vault secret that contains the SMTP password. |
| `host` | OCI Email Delivery SMTP endpoint. |
| `sender` | An approved sender address. |
| `defaultrecipient` | Recipient used when the event has no `custom.recipient` tag. |

Example:

```bash
fn config function <application-name> email-notification \
  smtpuser '<smtp-username>' \
  smtppass '<vault-secret-ocid>' \
  host 'smtp.email.<region>.oci.oraclecloud.com' \
  sender 'noreply@example.com' \
  defaultrecipient 'operations@example.com'
```

## Deploy and trigger

1. Replace `companylogo.png` with your organization’s approved logo if desired.
2. Review the email template in `func.py` and update its text to match your notification policy.
3. Deploy the function:

   ```bash
   fn -v deploy --app <application-name>
   ```

4. Create an OCI Events rule that targets the deployed function and test it with a non-sensitive event.

## Event requirements

The function expects an OCI event with `eventType`, `eventTime`, and resource details under `data`, including the resource name, ID, compartment ID, and compartment name. If the optional defined tag `custom.recipient` is present, its value becomes the email recipient.

## Security notes

- The attached JSON payload can contain sensitive resource metadata. Send to authorized recipients only.
- Use Vault for the SMTP password and restrict secret-read access to the function's dynamic group.
- Ensure the sender is configured as an approved sender in OCI Email Delivery.

## License

Licensed under the [Universal Permissive License 1.0](../LICENSE).
