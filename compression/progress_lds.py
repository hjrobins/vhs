import sys
import os
import re
import time
import argparse
from tqdm import tqdm
from subprocess import Popen

def parse_sox_timecode(line):
    match = re.search(r'%\s+(\d{1,3}:\d{2}:\d{2}\.\d{2})\s+\[', line)
    return match.group(1) if match else None

def timecode_to_seconds(tc):
    try:
        h, m, s = tc.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return None

def format_hms(seconds):
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def extract_duration_from_stat(stat_path):
    try:
        with open(stat_path, "r") as f:
            for line in f:
                if "Length (seconds):" in line:
                    return float(line.strip().split(":")[1])
    except Exception as e:
        print(f"[ERROR] Failed to read stat file: {e}")
    return None

def monitor_sox_progress(expected_duration_sec, input_file, output_file, log_path="sox_output_log.txt"):
    import time
    import sys

    start_time = time.time()
    clipped_samples = None
    bar_width = 40
    full_output = []

    print(f"\nCapture length: {format_hms(expected_duration_sec)}")

    for line in sys.stdin:
        line = line.strip()
        full_output.append(line)

        tc = parse_sox_timecode(line)
        if tc:
            elapsed = timecode_to_seconds(tc)
            if elapsed is not None:
                corrected_elapsed = elapsed / 1000
                percent = min(corrected_elapsed / expected_duration_sec, 1.0)
                eta = (time.time() - start_time) / max(percent, 0.001) - (time.time() - start_time)
                wall = time.time() - start_time

                filled = int(percent * bar_width)
                empty = bar_width - filled
                percent_str = f"{int(percent * 100):3d}%"
                elapsed_str = format_hms(corrected_elapsed)

                bar = "[" + "#" * filled + f"{percent_str}" + " " * empty + f"]"

                print(
                    f"\rElapsed:{format_hms(wall)} | ETA:{format_hms(eta)} | {bar} {elapsed_str}/{format_hms(expected_duration_sec)}",
                    end=""
                )


        if "Clipped samples:" in line:
            clipped_samples = line

    wall = time.time() - start_time
    print(
        f"\r{format_hms(expected_duration_sec)} | ETA 00:00:00  |  [{'#' * bar_width}]  {format_hms(wall)}"
    )

    if clipped_samples:
        print(f"\n[INFO] {clipped_samples}")
    else:
        print("\n[INFO] No clipping detected.")

    print(f"\n[INFO] Saving full SoX output to: {log_path}")
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(full_output))
        print("[INFO] Log saved successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to save log: {e}")


def generate_stat(input_file, estimated_speed_MBps=258):
    stat_path = os.path.splitext(input_file)[0] + "_stat.txt"
    file_size_bytes = os.path.getsize(input_file)
    file_size_MB = file_size_bytes / (1024 * 1024)
    estimated_duration = file_size_MB / estimated_speed_MBps

    print(f"[INFO] Generating stat file: {stat_path}")
    print(f"[INFO] Estimated duration: {estimated_duration:.2f} sec ({estimated_duration/60:.2f} min)")

    with tqdm(total=estimated_duration, desc="Stat Progress", unit="sec", ncols=80) as pbar:
        start = time.time()
        proc = Popen(
            f'sox -r 40000 -b 16 -c 1 -e signed -t raw "{input_file}" -n stat > "{stat_path}" 2>&1',
            shell=True
        )
        while proc.poll() is None:
            elapsed = time.time() - start
            pbar.n = min(format_hms(elapsed), format_hms(estimated_duration))
            pbar.refresh()
            time.sleep(0.5)
        pbar.n = estimated_duration
        pbar.refresh()

    print(f"\n[DONE] Stat file created: {stat_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", nargs="?", help="Path to LDS file")
    parser.add_argument("--stat", action="store_true", help="Generate stat file with progress")
    parser.add_argument("--progress", action="store_true", help="Monitor sox progress from stdin")
    args = parser.parse_args()

    if args.stat:
        if not args.input_file:
            print("[ERROR] --stat mode requires an input file.")
            sys.exit(1)
        generate_stat(args.input_file)

    elif args.progress:
        if not args.input_file:
            print("[ERROR] --progress mode requires an input file.")
            sys.exit(1)

        stat_path = os.path.splitext(args.input_file)[0] + "_stat.txt"
        duration = extract_duration_from_stat(stat_path)

        if duration is None:
            print(f"[ERROR] Could not extract duration from stat file: {stat_path}")
            sys.exit(1)

        corrected_duration = (duration / 1000) * 1.6
        output_file = os.path.splitext(args.input_file)[0].replace("_10bit40msps", "_8bit24msps") + ".ldf"
        monitor_sox_progress(expected_duration_sec=corrected_duration, input_file=args.input_file, output_file=output_file)

    else:
        print("[ERROR] No mode selected. Use --stat or --progress.")
        sys.exit(1)

if __name__ == "__main__":
    main()
