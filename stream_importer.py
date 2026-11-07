import os
import sys
import time
import glob
import gzip
import subprocess

CSV_DIR = r"d:\Loay_Mohamed_Files\db\old_Users_Egypt_csv\csv"
VM_HOST = "192.168.1.201"
VM_USER = "root"
CONTAINER = "postgres-egypt"
DB_NAME = "egypt_users"
DB_USER = "loay"

COLUMNS = (
    "fbid,unknown_1,unknown_2,phone,unknown_3,unknown_4,fname,sname,gender,fbaccount,"
    "unknown_5,unknown_6,unknown_7,unknown_8,unknown_9,unknown_10,unknown_11,unknown_12,unknown_13,"
    "email,unknown_14,unknown_15,unknown_16,unknown_17,unknown_18,unknown_19,unknown_20,"
    "unknown_21,unknown_22,unknown_23,unknown_24,unknown_25,unknown_26,unknown_27,unknown_28,unknown_29,unknown_30"
)

def import_file(filepath):
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    filesize_mb = filesize / (1024 * 1024)
    print(f"\n=======================================================", flush=True)
    print(f"Starting import: {filename} ({filesize_mb:.2f} MB)", flush=True)
    print(f"=======================================================", flush=True)

    copy_sql = f"COPY users({COLUMNS}) FROM STDIN WITH (FORMAT csv, HEADER true);"
    ssh_cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no", f"{VM_USER}@{VM_HOST}",
        f'gzip -dc | docker exec -i {CONTAINER} psql -U {DB_USER} -d {DB_NAME} -c "{copy_sql}"'
    ]

    t0 = time.time()
    proc = subprocess.Popen(ssh_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    bytes_read = 0
    last_log_time = t0
    chunk_size = 1024 * 1024  # 1 MB chunk

    try:
        with gzip.open(proc.stdin, "wb", compresslevel=1) as gz_out:
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    # sanitize any rogue null bytes that would crash postgres text COPY
                    if b"\x00" in chunk:
                        chunk = chunk.replace(b"\x00", b"")
                    gz_out.write(chunk)
                    bytes_read += len(chunk)

                    now = time.time()
                    if now - last_log_time >= 5.0:  # log every 5 seconds
                        pct = (bytes_read / filesize) * 100.0
                        mb_done = bytes_read / (1024 * 1024)
                        speed = mb_done / (now - t0)
                        eta_sec = (filesize_mb - mb_done) / speed if speed > 0 else 0
                        print(
                            f"[{filename}] {mb_done:.1f}/{filesize_mb:.1f} MB ({pct:.1f}%) "
                            f"@ {speed:.2f} MB/s | ETA: {eta_sec:.0f}s",
                            flush=True
                        )
                        last_log_time = now
    except Exception as e:
        print(f"Error streaming {filename}: {e}", file=sys.stderr, flush=True)

    out, err = proc.communicate()
    t1 = time.time()
    duration = t1 - t0

    out_str = out.decode("utf-8", errors="replace").strip()
    err_str = err.decode("utf-8", errors="replace").strip()

    if proc.returncode != 0:
        print(f"FAILED {filename}: exit code {proc.returncode}", flush=True)
        print(f"STDERR: {err_str}", flush=True)
        return False, 0
    else:
        print(f"SUCCESS {filename} in {duration:.1f}s ({filesize_mb/duration:.2f} MB/s) -> {out_str}", flush=True)
        return True, duration

def main():
    files = sorted(glob.glob(os.path.join(CSV_DIR, "eg-*.csv")))
    if not files:
        print(f"No CSV files found in {CSV_DIR}!")
        sys.exit(1)

    print(f"Found {len(files)} CSV files to import:")
    total_bytes = sum(os.path.getsize(f) for f in files)
    for f in files:
        print(f"  - {os.path.basename(f)}: {os.path.getsize(f)/(1024*1024):.2f} MB")
    print(f"Total uncompressed size: {total_bytes/(1024*1024*1024):.2f} GB\n")

    overall_t0 = time.time()
    for f in files:
        success, duration = import_file(f)
        if not success:
            print(f"Aborting due to error in {os.path.basename(f)}!")
            sys.exit(1)

    overall_duration = time.time() - overall_t0
    print(f"\n=======================================================", flush=True)
    print(f"All {len(files)} files imported successfully in {overall_duration/60:.2f} minutes!", flush=True)
    print(f"=======================================================", flush=True)

if __name__ == "__main__":
    main()
