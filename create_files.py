import os
import argparse
import sys
import random
import string

MAX_TXT_GB = 1024 ** 3  # 1 GB in bytes


def parse_size(size_str: str) -> int:
    size_str = size_str.strip().upper()
    units = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}
    for unit, factor in units.items():
        if size_str.endswith(unit):
            return int(float(size_str[:-len(unit)]) * factor)
    return int(size_str)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create txt and bin files of varied sizes, matching total-size."
    )
    parser.add_argument("--total-size", type=parse_size, required=True, help="Total size of all files combined.")
    parser.add_argument("--num-files", type=int, required=True, help="Total number of files (>20).")
    parser.add_argument("--path", type=str, required=True, help="Base path.")
    parser.add_argument("--folder", type=str, required=True, help="Folder name to create.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions without actually creating files.")
    return parser.parse_args()


def write_file_in_chunks(file_path: str, size: int, is_text: bool = True):
    chunk_size = 1024 * 1024  # 1 MB
    remaining = size

    if is_text:
        letters = string.ascii_letters
        with open(file_path, "w", encoding="utf-8") as f:
            while remaining > 0:
                to_write = min(remaining, chunk_size)
                chunk = ''.join(random.choices(letters, k=to_write))
                f.write(chunk)
                remaining -= to_write
    else:
        with open(file_path, "wb") as f:
            chunk = b"\x00" * chunk_size
            while remaining > 0:
                to_write = min(remaining, chunk_size)
                f.write(chunk[:to_write])
                remaining -= to_write


def create_data_folder_with_files(total_size_bytes: int, num_files: int, base_path: str, folder_name: str, dry_run: bool):
    if num_files <= 20:
        raise ValueError("Number of files must be greater than 20 (20 are reserved for BIN).")

    folder_path = os.path.join(os.path.abspath(base_path), folder_name)
    if dry_run:
        print(f"[DRY-RUN] Would create folder: {folder_path}")
    else:
        os.makedirs(folder_path, exist_ok=True)

    num_bin = 20
    num_txt = num_files - num_bin

    # Allocate budgets
    txt_budget = int(total_size_bytes * 0.8)
    bin_budget = total_size_bytes - txt_budget

    # Generate random txt sizes
    txt_sizes = []
    for _ in range(num_txt):
        choice = random.random()
        if choice < 0.3:
            size = random.randint(1 * 1024**2, 50 * 1024**2)
        elif choice < 0.6:
            size = random.randint(50 * 1024**2, 200 * 1024**2)
        elif choice < 0.85:
            size = random.randint(200 * 1024**2, 800 * 1024**2)
        else:
            size = random.randint(800 * 1024**2, MAX_TXT_GB)
        txt_sizes.append(size)

    # Scale txt sizes to match txt_budget
    total_txt = sum(txt_sizes)
    if total_txt == 0:
        raise ValueError("Random generation failed to produce nonzero txt sizes.")
    scale = txt_budget / total_txt
    txt_sizes = [max(1, int(s * scale)) for s in txt_sizes]
    diff = txt_budget - sum(txt_sizes)
    if diff != 0:
        txt_sizes[-1] += diff

    # Divide bin budget evenly
    per_bin = bin_budget // num_bin
    bin_sizes = [per_bin] * num_bin
    diff = bin_budget - (per_bin * num_bin)
    if diff > 0:
        bin_sizes[-1] += diff

    # Write TXT files
    for i, size in enumerate(txt_sizes, start=1):
        file_path = os.path.join(folder_path, f"irelocatetest_{i}.txt")
        if dry_run:
            print(f"[DRY-RUN] Would create TXT: {file_path} ({size} bytes)")
        else:
            write_file_in_chunks(file_path, size, is_text=True)

    # Write BIN files
    for i, size in enumerate(bin_sizes, start=1):
        file_path = os.path.join(folder_path, f"irelocatetest_{i}.bin")
        if dry_run:
            print(f"[DRY-RUN] Would create BIN: {file_path} ({size} bytes)")
        else:
            write_file_in_chunks(file_path, size, is_text=False)

    total_created = sum(txt_sizes) + sum(bin_sizes)
    
    print(f"{'[DRY-RUN]' if dry_run else ''} Total size planned: {total_created} bytes ({total_created / 1024**2:.2f} MB).")


def main():
    args = parse_args()
    try:
        create_data_folder_with_files(args.total_size, args.num_files, args.path, args.folder, args.dry_run)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

