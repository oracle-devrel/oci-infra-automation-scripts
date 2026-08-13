# OCI Infrastructure Automation Scripts

[![License: UPL](https://img.shields.io/badge/license-UPL-green)](LICENSE)
[![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=oracle-devrel_oci-infra-automation-scripts)](https://sonarcloud.io/dashboard?id=oracle-devrel_oci-infra-automation-scripts)

Reusable [Oracle Cloud Infrastructure (OCI)](https://www.oracle.com/cloud/) automation examples created by Oracle Cloud Engineering Services. Most examples are Python-based OCI Functions; each solution is independently deployable and has its own configuration, IAM-policy, and trigger requirements.

> [!WARNING]
> These are reference implementations. Review, test, and adapt them for your tenancy, security requirements, and operational processes before production use.

## Solutions

| Solution                                           | What it does                                                                                                                               | Execution model                         | Documentation |
|----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------| --- |
| [Auto-rotation credentials](auto-rotation-credentials/) | Rotates selected IAM credentials from OCI problem events, stores replacement secrets in OCI Vault, and sends an OCI Notifications message. | OCI Function, event-driven              | [README](auto-rotation-credentials/README.md) |
| [Custom metrics](custom-metrics/)                  | Collects local disk usage and publishes it as an OCI Monitoring custom metric.                                                             | Python script using instance principals | [README](custom-metrics/README.md) |
| [Email-friendly notification](email-friendly-notification/) | Converts OCI event payloads into branded HTML emails using OCI Email Delivery and a Vault-held SMTP password.                              | OCI Function, event-driven              | [README](email-friendly-notification/README.md) |
| [Function CI/CD pipeline](fn-ci-cd-deployment-pipeline/) | GitHub Actions workflows that build and deploy an OCI Function with the Fn CLI.                                                            | GitHub Actions                          | [README](fn-ci-cd-deployment-pipeline/README.md) |
| [IAM credential-expiry notification](iam-credential-expiry-notification/) | Identifies aging or expired Identity Domain credentials, emails users, and produces optional reports.                                      | OCI Function, scheduled                 | [README](iam-credential-expiry-notification/README.md) |
| [IAM user capability management](iam-user-capability-management/) | Enables or disables Identity Domain user capabilities according to defined tags.                                                           | OCI Function, event-driven or scheduled | [README](iam-user-capability-management/README.md) |
| [Backup OCI Function](backup-oci-function/)| Backup/download existing OCI Function deployed | Python Script |[README](backup-oci-function/README.md) |

## Before you begin

Most function-based solutions require:

- An OCI tenancy, compartment, and OCI Functions application.
- The [Fn Project CLI](https://fnproject.io/) and OCI CLI configured for the target tenancy.
- A dynamic group for the deployed function and least-privilege IAM policies for the OCI services it uses.
- OCI Vault for credentials or secrets when the solution requires them.
- OCI Events or Resource Scheduler when the solution is intended to run automatically.
- Python dependencies defined in the solution's `requirements.txt`.

Function examples that call OCI APIs use OCI principals at runtime. Never commit API keys, SMTP passwords, private keys, or real tenant identifiers.

## Quick start

1. Select a solution in the table and read its folder-level README.
2. Clone this repository and enter the chosen directory.

   ```bash
   git clone https://github.com/oracle-devrel/oci-infra-automation-scripts.git
   cd oci-infra-automation-scripts/iam-credential-expiry-notification
   ```

3. Review `func.py`, `func.yaml`, and `requirements.txt`; replace every sample value.
4. Configure the required IAM policies, Vault secrets, email settings, and event or schedule trigger.
5. Deploy an OCI Function where applicable:

   ```bash
   fn -v deploy --app <function-application-name>
   ```

6. Test in a non-production compartment before enabling a schedule or event rule.

## Configuration and security

Configuration is solution-specific. Store only non-secret settings, such as OCIDs, names, thresholds, and feature flags, in `func.yaml`.

- Store secret values in OCI Vault.
- Grant the function's dynamic group access only to the secrets and OCI APIs it needs.
- Refer to a secret OCID in function configuration only when the solution supports it.
- Validate event payloads and test all credential-changing automations before enabling them.

Some solutions can modify or delete IAM credentials. In particular, review `enable_delete_on_expiry` in the credential-expiry solution before setting it to `true`.

## Repository layout

```text
.
├── auto-rotation-credentials/       # Event-driven IAM credential rotation
├── custom-metrics/                  # Disk-utilization metric example
├── email-friendly-notification/     # OCI event-to-email function
├── fn-ci-cd-deployment-pipeline/    # GitHub Actions build/deploy workflows
├── iam-credential-expiry-notification/
└── iam-user-capability-management/  # Tag-driven capability automation
```

## Contributing

Contributions should be reusable OCI infrastructure-automation code that has also been documented in a public Oracle blog or technical article. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

When adding a solution, include a folder-level README covering its purpose, prerequisites, IAM policies, configuration, deployment, trigger setup, testing, and cleanup. Include sanitized example values only.

## Security

Report potential vulnerabilities according to [SECURITY.md](SECURITY.md). Do not create public issues for security-sensitive findings.

## License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the [Universal Permissive License 1.0](LICENSE).
