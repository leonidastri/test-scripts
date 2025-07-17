import os
import argparse
import sys
import subprocess

# Dictionary of iput flags
IPUT_PARAMS = {
    "resource": {
        "flag": "-R",
        "help": "Specify the resource to store data."
    }
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Upload an existing folder to iRODS and optionally replicate it to another resource."
    )
    parser.add_argument("--folder", type=str, required=True,
                        help="Local folder containing files to upload.")
    parser.add_argument("--irods-path", type=str, required=True,
                        help="iRODS collection path to upload files to.")
    parser.add_argument("--resource", type=str,
                        help=IPUT_PARAMS["resource"]["help"])
    parser.add_argument("--replicate", type=str,
                        help="Replicate uploaded data to this second resource.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate actions without executing them.")
    return parser.parse_args()

def ensure_irods_collection(path: str, dry_run: bool):
    print(f"Ensuring iRODS collection '{path}' exists...")
    if dry_run:
        print(f"[DRY-RUN] Would run: imkdir -p {path}")
        print(f"[DRY-RUN] Collection '{path}' assumed to exist.")
        return
    try:
        subprocess.run(["imkdir", "-p", path], check=True, capture_output=True, text=True)
        print(f"Collection '{path}' exists or was created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create iRODS collection '{path}'!")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        sys.exit(1)

def upload_folder_to_irods(local_folder: str, irods_path: str, resource: str = None, dry_run: bool = False):
    if not os.path.isdir(local_folder):
        print(f"Error: Folder '{local_folder}' does not exist or is not a directory.", file=sys.stderr)
        sys.exit(1)

    ensure_irods_collection(irods_path, dry_run)

    print(f"Uploading '{local_folder}' to iRODS path '{irods_path}'...")
    cmd = ["iput", "-r"]
    if resource:
        cmd.extend([IPUT_PARAMS["resource"]["flag"], resource])
    cmd.extend([local_folder, irods_path])

    print(f"Running command: {' '.join(cmd)}")
    if dry_run:
        print(f"[DRY-RUN] Skipping actual upload.")
    else:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"Successfully uploaded folder '{local_folder}' to '{irods_path}'")
            if result.stdout:
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print("iRODS upload failed!")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            sys.exit(1)

    uploaded_folder_name = os.path.basename(os.path.normpath(local_folder))
    return os.path.join(irods_path, uploaded_folder_name)

def replicate_to_resource(uploaded_folder_path: str, second_resource: str, dry_run: bool):
    print(f"Replicating '{uploaded_folder_path}' to resource '{second_resource}'...")
    cmd = ["irepl", "-r", "-R", second_resource, uploaded_folder_path]
    print(f"Running command: {' '.join(cmd)}")
    if dry_run:
        print(f"[DRY-RUN] Skipping actual replication.")
    else:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"Successfully replicated '{uploaded_folder_path}' to resource '{second_resource}'")
            if result.stdout:
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print("Replication failed!")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            sys.exit(1)

def main():
    args = parse_args()
    try:
        uploaded_folder_path = upload_folder_to_irods(args.folder, args.irods_path, args.resource, args.dry_run)
        if args.replicate:
            replicate_to_resource(uploaded_folder_path, args.replicate, args.dry_run)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

