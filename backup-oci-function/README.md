### README for `export_functions.py`

#### Overview

The `export_functions.py` script is designed to download OCI (Oracle Cloud Infrastructure) Function container filesystems. It utilizes the OCI CLI to interact with OCI services and Docker to handle container images.

#### Prerequisites

1. **OCI CLI**: Ensure that the OCI CLI is installed and configured on your system.
2. **Docker**: Docker must be installed and running on your system.
3. **Python**: The script is written in Python 3, so you need to have Python 3 installed.
4. **Policies**: There are effectively two authentication paths in your solution.
    
   The OCI CLI identity used for Resource Search and Functions API calls needs to ***read functions-family in tenancy***

   The OCIR Docker login identity used to pull the deployed container images needs to ***read repos in tenancy***

#### Usage

To use the script, follow these steps:

1. **Clone or Download the Script**: Obtain the `export_functions.py` script.
2. **Run the Script**: Execute the script using Python 3.

   ```bash
   python3 export_functions.py --help
   ```

   This will display the help message and usage instructions.

#### Command-Line Arguments

The script accepts the following command-line arguments:

* `--output-dir`: Specify the output directory where the downloaded function filesystems will be saved. Default is `./oci-functions`.
* `--auth`: Specify the authentication method. Can be `instance_principal`, `resource_principal`, or the path to a config file. Default is `DEFAULT`, which uses the system's default authentication.
* `--profile`: ***OPTIONAL*** Specify the OCI CLI profile to use. Default is `DEFAULT`.
* `--regions`: Specify one or more OCI regions to process. This argument is required.
* `--overwrite`: If specified, the script will overwrite existing tar files. Default is to overwrite.

#### Example Usage

To download OCI Function container filesystems from the `us-ashburn-1` and `us-phoenix-1` regions, using the default OCI CLI profile and authentication, run:

```bash
python3 export_functions.py --regions us-ashburn-1 us-phoenix-1
```

You will be prompted to enter your OCIR username and password/auth token.

#### Script Behavior

1. The script checks for the presence of OCI CLI and Docker, exiting if either is not found or not properly configured.
2. It logs into the specified OCI regions and searches for applications using a predefined query.
3. For each application found, it lists the functions and downloads their container images using Docker.
4. The function filesystems are then exported to tar.gz files in the specified output directory, organized by region and application.

#### Output

The script logs its progress and any errors encountered during execution. The final output includes a summary of successful and failed function downloads, along with the output directory path.

#### Troubleshooting

* Ensure that your OCI CLI is properly configured and that you have the necessary permissions to access the OCI resources.
* Verify that Docker is running and that you have the necessary credentials to access the OCIR.
* Check the script's log output for any error messages that may indicate issues during execution.

#### Security Considerations

* Be cautious when handling your OCIR credentials. Avoid hardcoding them or storing them insecurely.
* Ensure that the output directory is secure and access-controlled to prevent unauthorized access to the downloaded function filesystems.