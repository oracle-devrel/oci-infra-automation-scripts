# Automatic IAM Credential Rotation

An OCI Function that processes supported OCI problem events and rotates the affected IAM credential. Where a replacement secret is created, the function stores its value in an existing OCI Vault secret and publishes the outcome to an OCI Notifications topic.

## Supported problem types

| Problem name | Automation action | Required value in problem comments |
| --- | --- | --- |
| `PASSWORD_TOO_OLD` | Resets the user's console password. | None |
| `AUTH_TOKEN_TOO_OLD` | Replaces an auth token and writes its value to Vault. | `auth_secret_ocid:<vault-secret-ocid>` |
| `SECRET_KEY_TOO_OLD` | Replaces a customer secret key and writes both parts to Vault. | `accesskey_secret_ocid:<vault-secret-ocid>,secretkey_secret_ocid:<vault-secret-ocid>` |
| `API_KEY_TOO_OLD` | Replaces an API key and writes the new private key to Vault. | `api_secret_ocid:<vault-secret-ocid>` |

> [!CAUTION]
> This function deletes the existing credential before creating its replacement. Test it with a non-production user and verify every downstream consumer can read the new Vault secret.

## Prerequisites

- OCI Functions application and Fn CLI.
- An OCI Notifications topic; its OCID is required as `ons_topic`.
- OCI Vault secrets for every generated credential value that must be retained.
- An OCI event rule that invokes the function with the expected problem-event payload.
- A dynamic group for the function with least-privilege permission to manage the relevant IAM credentials, update the designated Vault secrets, and publish to the configured Notifications topic.

## Configure and deploy

1. Create an OCI Function application and initialize or enter this directory.
2. Set the Notifications topic OCID as function configuration:

   ```bash
   fn config function <application-name> key-rotate ons_topic <notifications-topic-ocid>
   ```

3. Review `func.py` and replace the example function name in `func.yaml` if needed.
4. Deploy the function:

   ```bash
   fn -v deploy --app <application-name>
   ```

5. Configure an OCI Events rule to send the relevant problem events to the deployed function.

## Event payload expectations

The function expects an event payload with the problem name, affected user OCID, target resource name and ID, risk level, and comma-separated `comments` in `data.additionalDetails.problemAdditionalDetails`. The comments carry Vault secret OCIDs for rotations that produce secret values.

Malformed comments, unsupported problem names, and runtime errors result in a notification without a successful automation status. Monitor function logs and the Notifications subscription after deployment.

## Security notes

- Grant the function access only to the credential types it is intended to rotate.
- Restrict Vault permissions to the exact secret OCIDs where possible.
- Treat all new secret values as sensitive; do not place them in event payloads, logs, or source control.
- Verify that Notifications subscribers are authorized to receive resource and user identifiers.

## License

Licensed under the [Universal Permissive License 1.0](../LICENSE).
