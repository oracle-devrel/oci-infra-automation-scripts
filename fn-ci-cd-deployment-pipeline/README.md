# CI/CD pipeline for OCI function deployment using Fn CLI

## Introduction
This is a reference yaml as an action workflow to build and deploy the OCI function using FN CLI.

### Pipeline Definition
- [oci-fn-build.yml](./oci-fn-build.yml)
- [oci-fn-deploy.yml](./oci-fn-deploy.yml)

### Build and Deploy Pipeline

Deploy a function using the Fn Project CLI, the function is built as a Docker image and pushed to a specified Docker registry. 

- Provide value for non senstive information as an workflow input and update during runtime.

    ```
      OCI_FN_NAME
      OCI_FN_APP
      OCI_FN_COMPARTMENT
      OCI_FN_IMAGE
    ````

- Create environment/git variables for other non senstive information.
  
  ```
  OCI_TENANCY_NAME
  OCI_FN_REGISTRY
  OCI_FN_API_URL
  OCI_FN_USER_NAME
  OCI_FN_OCIR
  ```

- Create secrets for all senstive information to use in the pipeline.
    ```
    OCI_CLI_USER
    OCI_CLI_FINGERPRINT
    OCI_CLI_TENANCY
    OCI_CLI_REGION         
    OCI_CLI_KEY_CONTENT    
    ```

OCI Functions pulls the function's Docker image from the specified Docker registry, runs it as a Docker container, and executes the function.

## License
Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.  FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK. 
