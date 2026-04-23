import os
import csv
import datetime

# Output directory setup
DATA_DIR = os.path.expanduser("~/data")
os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------------
# Path timestamp format
# ----------------------------
def current_file_base():
    return datetime.datetime.now().strftime("%Y-%m-%d-%H")

# ----------------------------
# Create new CSV + LOG file
# ----------------------------
def open_new_files():
    ts = current_file_base()

    csv_path = f"{DATA_DIR}/NetRadar-{ts}.csv"
    log_path = f"{DATA_DIR}/NetRadar-{ts}.log"

    csv_file = open(csv_path, "w", newline="")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow([
        "date", "time", "service",
        "latency", "packet_loss",
        "dns", "tcp", "status"
    ])

    log_file = open(log_path, "a")

    return csv_path, log_path, csv_file, csv_writer, log_file

# ----------------------------
# Logging with timestamp
# ----------------------------
def log(msg, plain_text, log_file):
    now = datetime.datetime.now()
    ts_date = now.strftime("%Y-%m-%d")
    ts_time = now.strftime("%H:%M:%S")
    prefix = f"{ts_date} {ts_time} "

    print(prefix + msg)
    log_file.write(prefix + plain_text + "\n")
    log_file.flush()
