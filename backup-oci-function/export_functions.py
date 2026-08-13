#!/usr/bin/env python3

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import getpass
import shutil
import tarfile,tempfile


SEARCH_QUERY = "query functionsapplication resources"
docker_username = ""
docker_password = ""
auth = ""


def log(message):
    print(message, flush=True)


def error(message):
    print(f"ERROR: {message}", file=sys.stderr, flush=True)


def sanitize_name(name):
    name = re.sub(r"[\\/]", "_", name)
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = re.sub(r"_+", "_", name)

    return name or "unnamed"


def run_command(cmd, capture_output=True, check=True):
    try:
        result = subprocess.run(
            cmd,
            text=True,
            capture_output=capture_output,
            check=check,
        )

        if capture_output:
            return result.stdout.strip()

        return ""

    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            error(exc.stderr.strip())

        raise


def run_oci(args, profile, region=None):

    if auth == "DEFAULT":
        cmd = ["oci"]
    elif auth in ["instance_principal","resoruce_principal"]:
        cmd = ["oci","--auth",auth]
    else:
        cmd = ["oci", "--config-file", auth,"--profile", profile]

    if region:
        cmd.extend(["--region", region])

    cmd.extend(args)
    cmd.extend(["--output", "json"])

    output = run_command(cmd)

    return json.loads(output)


def check_dependencies():
    dependencies = ["oci", "docker"]

    for command in dependencies:
        try:
            subprocess.run(
                [command, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except Exception:
            error(f"{command} is not installed or not available in PATH")
            sys.exit(1)


def check_docker():
    try:
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError:
        error("Docker daemon is not available")
        sys.exit(1)


def docker_login_if_needed(image, logged_in_registries):
    registry = image.split("/", 1)[0]

    if registry in logged_in_registries:
        return

    if not docker_username or not docker_password:
        log(f"Using existing Docker credentials for {registry}")
        logged_in_registries.add(registry)
        return

    log(f"Logging into {registry}")

    proc = subprocess.run(
        [
            "docker",
            "login",
            registry,
            "--username",
            docker_username,
            "--password-stdin",
        ],
        input=docker_password,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"Docker login failed for {registry}: {proc.stderr.strip()}"
        )

    logged_in_registries.add(registry)


def pull_image(image):
    log(f"  Pulling image: {image}")

    subprocess.run(
        ["docker", "pull", image],
        check=True,
    )


def export_function_directory(image,function_name, output_tar):
    container_id = None
    temp_dir = None

    try:
        result = subprocess.run(
            ["docker", "create", image],
            text=True,
            capture_output=True,
            check=True,
        )

        container_id = result.stdout.strip()

        temp_dir = tempfile.mkdtemp(prefix="oci-function-")

        function_dir = os.path.join(temp_dir, "functions")

        # First try /function
        copy_result = subprocess.run(
            [
                "docker",
                "cp",
                f"{container_id}:/function/.",
                function_dir,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # If /function does not exist, try /functions
        if copy_result.returncode != 0:
            copy_result = subprocess.run(
                [
                    "docker",
                    "cp",
                    f"{container_id}:/functions/.",
                    function_dir,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        if copy_result.returncode != 0:
            raise RuntimeError(
                "Neither /function nor /functions directory "
                "was found inside the container"
            )

        log(f"  Creating tar: {output_tar}")

        # with tarfile.open(output_tar, "w") as tar:
        #     tar.add(
        #         function_dir,
        #         arcname=function_name,
        #     )
        with tarfile.open(output_tar, "w:gz") as tar:
            tar.add(function_dir, arcname=function_name)

    finally:
        if container_id:
            subprocess.run(
                ["docker", "rm", container_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)



        if image:
            subprocess.run(
                ["docker", "rmi", image],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )



def get_function_image(function_id, profile, region):
    data = run_oci(
        [
            "fn",
            "function",
            "get",
            "--function-id",
            function_id,
        ],
        profile,
        region,
    )

    return data.get("data", {}).get("image")


def process_function(
    function,
    app_name,
    output_dir,
    profile,
    region,
    logged_in_registries,
    overwrite=False,
):
    function_id = function.get("id")
    function_name = function.get("display-name") or function_id

    if not function_id:
        error(f"Function without ID found in {app_name}")
        return False

    safe_app_name = sanitize_name(app_name)
    safe_function_name = sanitize_name(function_name)

    app_dir = Path(output_dir) / safe_app_name
    app_dir.mkdir(parents=True, exist_ok=True)

    output_tar = app_dir / f"{safe_function_name}.tar.gz"

    log("")
    log(f"Function: {function_name}")

    if output_tar.exists() and not overwrite:
        log(f"  Already exists, skipping: {output_tar}")
        return True

    try:
        image = get_function_image(
            function_id,
            profile,
            region,
        )

        if not image:
            error(f"No image configured for function {function_name}")
            return False

        log(f"  Image: {image}")

        docker_login_if_needed(
            image,
            logged_in_registries,
        )

        pull_image(image)

        export_function_directory(
            image,function_name,
            output_tar,
        )

        log(f"  Saved: {output_tar}")

        return True

    except Exception as exc:
        error(f"Failed processing function {function_name}: {exc}")

        if output_tar.exists():
            output_tar.unlink()

        return False


def process_application(
    application,
    reg_dir,
    profile,
    region,
    logged_in_registries,
    overwrite,
):
    app_id = application.get("identifier")

    app_name = (
        application.get("display-name")
        or application.get("displayName")
        or app_id
    )

    if not app_id:
        error("Application returned without an OCID")
        return 0, 1

    log("")
    log("=" * 80)
    log(f"Application: {app_name}")
    log(f"Application OCID: {app_id}")

    if region:
        log(f"Region: {region}")

    log("=" * 80)

    try:
        result = run_oci(
            [
                "fn",
                "function",
                "list",
                "--application-id",
                app_id,
                "--all",
            ],
            profile,
            region,
        )

    except Exception as exc:
        error(
            f"Unable to list functions for application "
            f"{app_name}: {exc}"
        )
        return 0, 1

    functions = result.get("data", [])

    log(f"Functions found: {len(functions)}")

    success = 0
    failed = 0

    for function in functions:
        if process_function(
            function,
            app_name,
            reg_dir,
            profile,
            region,
            logged_in_registries,
            overwrite,
        ):
            success += 1
        else:
            failed += 1

    return success, failed


def search_applications(profile, region):
    log("")
    log(f"Searching applications using: {SEARCH_QUERY}")

    result = run_oci(
        [
            "search",
            "resource",
            "structured-search",
            "--query-text",
            SEARCH_QUERY,
            "--limit",
            "1000",
        ],
        profile,
        region,
    )

    return result.get("data", {}).get("items", [])


def process_region(
    region,
    output_dir,
    profile,
    logged_in_registries,
    overwrite,
):
    if region:
        log("")
        log("#" * 80)
        log(f"Processing region: {region}")
        log("#" * 80)

    try:
        applications = search_applications(
            profile,
            region,
        )

    except Exception as exc:
        error(f"Resource Search failed: {exc}")
        return 0, 1

    log(f"Applications found: {len(applications)}")

    success = 0
    failed = 0
    reg_dir = f'{output_dir}/{region.replace("-", "_").strip()}'

    for application in applications:
        app_success, app_failed = process_application(
            application,
            reg_dir,
            profile,
            region,
            logged_in_registries,
            overwrite,
        )

        success += app_success
        failed += app_failed

    return success, failed


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download OCI Function container filesystems"
    )

    parser.add_argument(
        "--output-dir",
        default="./oci-functions",
        help="Output directory",
    )

    parser.add_argument("--auth", default="DEFAULT", help= "instance_principal/resource_principal or provide the config file path. Default is system default authentication")

    parser.add_argument(
        "--profile",
        default="DEFAULT",
        help="OCI CLI profile",
    )

    parser.add_argument(
        "--regions",
        nargs="+",
        required=True,
        help="OCI regions, e.g. us-ashburn-1 us-phoenix-1",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing tar files",
    )

    return parser.parse_args()


def main():
    global docker_username,docker_password,auth
    args = parse_args()
    docker_username = input("OCIR Username: ").strip()
    docker_password = getpass.getpass("OCIR Password/Auth Token: ")
    auth = args.auth
    check_dependencies()
    check_docker()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logged_in_registries = set()

    regions = args.regions

    total_success = 0
    total_failed = 0

    for region in regions:
        success, failed = process_region(
            region,
            output_dir,
            args.profile,
            logged_in_registries,
            args.overwrite,
        )

        total_success += success
        total_failed += failed

    log("")
    log("=" * 80)
    log("Completed")
    log(f"Successful functions: {total_success}")
    log(f"Failed functions:     {total_failed}")
    log(f"Output directory:     {output_dir}")
    log("=" * 80)

    if total_failed:
        sys.exit(2)


if __name__ == "__main__":
    main()