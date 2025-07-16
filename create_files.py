import os
import argparse
from datetime import datetime
import sys
import subprocess

# Dictionary of iput flags
IPUT_PARAMS = {
    "resource": {
        "flag": "-R",
        "help": "Specify the resource to store data."
    }
}

def parse_size(size_str):
    size_str = size_str.strip().upper()
    units = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}
    for unit in units:
        if size_str.endswith(unit):
            try:
                number = float(size_str[:-len(unit)])
                return int(number * units[unit])
            except ValueError:
                raise argparse.ArgumentTypeError(f"Invalid size value: {size_str}")
    try:
        return int(size_str)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid size value: {size_str}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Create or append files in a folder. Then optionally upload to iRODS."
    )
    parser.add_argument("--total-size", type=parse_size, required=True,
                        help="Total size of all NEW files combined (e.g. 10MB, 500KB, 1000)")
    parser.add_argument("--num-files", type=int, required=True,
                        help="Number of new files to create (must be > 0)")
    parser.add_argument("--folder", type=str, default=None,
                        help="Optional folder name. If not provided, a folder named 'data_<timestamp>' will be created.")
    parser.add_argument("--irods-path", type=str, default=None,
                        help="Optional iRODS collection path to upload files to after creation.")
    parser.add_argument("--resource", type=str, help=IPUT_PARAMS["resource"]["help"])
    return parser.parse_args()

def create_data_folder_with_files(total_size_bytes, num_files, folder_name=None):
    if total_size_bytes <= 0:
        raise ValueError("Total size must be greater than 0.")
    if num_files <= 0:
        raise ValueError("Number of files must be greater than 0.")
    if num_files > total_size_bytes:
        raise ValueError("Number of files cannot exceed total size in bytes (each file must be at least 1 byte).")

    if not folder_name:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        folder_name = f"data_{timestamp}"

    os.makedirs(folder_name, exist_ok=True)

    # count existing files
    existing_files = [
        f for f in os.listdir(folder_name)
        if f.startswith("file_") and f.endswith(".txt")
    ]
    next_index = len(existing_files) + 1

    size_per_file = total_size_bytes // num_files
    remainder = total_size_bytes % num_files

    for i in range(num_files):
        file_size = size_per_file + (1 if i < remainder else 0)
        file_path = os.path.join(folder_name, f"file_{next_index + i}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('0' * file_size)

    print(f"Created {num_files} .txt files in '{folder_name}' totaling {total_size_bytes} bytes.")
    return folder_name

def ensure_irods_collection(path):
    print(f"Ensuring iRODS collection '{path}' exists...")
    try:
        subprocess.run(["imkdir", "-p", path], check=True, capture_output=True, text=True)
        print(f"Collection '{path}' exists or created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create iRODS collection '{path}'!")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        sys.exit(1)

def upload_to_irods(local_folder, irods_path, args):
    ensure_irods_collection(irods_path)

    print(f"Uploading '{local_folder}' to iRODS path '{irods_path}'...")

    cmd = ["iput", "-r"]
    if args.resource:
        cmd.extend([IPUT_PARAMS["resource"]["flag"], args.resource])

    cmd.extend([local_folder, irods_path])

    print(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Successfully uploaded to {irods_path}")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("iRODS upload failed!")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        sys.exit(1)

def main():
    args = parse_args()
    try:
        folder = create_data_folder_with_files(args.total_size, args.num_files, args.folder)
        if args.irods_path:
            upload_to_irods(folder, args.irods_path, args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()


