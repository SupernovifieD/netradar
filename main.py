#!/usr/bin/env python3

import time
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.colors import YELLOW, RED, GREEN, BLUE, RESET
from src.services import load_services
from src.checks import check_service
from src.output import open_new_files, log

# -----------------------------------
# INITIAL FILES + CURRENT HOUR
# -----------------------------------
CSV_PATH, LOG_PATH, csv_file, writer, log_file = open_new_files()
current_hour = datetime.datetime.now().hour

print(f"Logging to {CSV_PATH}")
print(f"Terminal log will also be saved to {LOG_PATH}\n")

# -----------------------------------
# MAIN LOOP
# -----------------------------------
while True:
    now = datetime.datetime.now()

    # HOURLY ROTATION
    if now.hour != current_hour:
        log_file.close()
        csv_file.close()
        CSV_PATH, LOG_PATH, csv_file, writer, log_file = open_new_files()
        current_hour = now.hour

        print(f"{BLUE}--- Hour changed: new CSV and LOG created ---{RESET}")
        print(f"Logging to {CSV_PATH}\n")

    services = load_services()

    # THREADING
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_service, svc): svc for svc in services}

        for future in as_completed(futures):
            service = futures[future]
            try:
                svc, dns, tcp, latency, packet_loss, status = future.result()

                color_service = f"{YELLOW}{svc}{RESET}"
                color_status = (
                    f"{GREEN}{status}{RESET}"
                    if status == "UP"
                    else f"{RED}{status}{RESET}"
                )

                term_msg = (
                    f"[{color_service}] DNS:{dns} TCP:{tcp} "
                    f"PING:{latency} STATUS:{color_status}"
                )

                log_msg = (
                    f"[{svc}] DNS:{dns} TCP:{tcp} "
                    f"PING:{latency} STATUS:{status}"
                )

                log(term_msg, log_msg, log_file)

                row_now = datetime.datetime.now()
                writer.writerow([
                    row_now.strftime("%Y-%m-%d"),
                    row_now.strftime("%H:%M:%S"),
                    svc,
                    latency,
                    packet_loss,
                    dns,
                    tcp,
                    status
                ])
                csv_file.flush()

            except Exception as e:
                err_term = f"{RED}Error checking {service}: {e}{RESET}"
                err_log = f"Error checking {service}: {e}"
                log(err_term, err_log, log_file)

    log(f"{BLUE}Cycle completed{RESET}\n", "Cycle completed\n", log_file)
    time.sleep(15)
