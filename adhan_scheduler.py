#!/usr/bin/env python3
import time
import json
import shutil
import subprocess
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse

from praytimes import PrayTimes

# ===== CONFIG =====
LAT = 55.70941493357022
LON = 13.170082073009272

TZ_NAME = "Europe/Stockholm"   # DST handled automatically
ASR_METHOD = "Hanafi"
FAJR_ANGLE = 18.5
ISHA_ANGLE = 19

PRAYERS = ["fajr", "dhuhr", "asr", "maghrib", "isha"]

BASE_DIR = Path(__file__).resolve().parent
ADHAN_FILE = BASE_DIR / "adhan" / "mecca.mp3"

GRACE_SECONDS = 120                # only trigger within 2 minutes after adhan time
REPLAY_SUPPRESS_SECONDS = 15 * 60  # don't replay same prayer within 15 minutes (restart protection)

STATE_FILE = BASE_DIR / ".adhan_state.json"
# ==================


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


def _already_played(today_key: str, prayer: str) -> bool:
    state = _load_state()
    played = state.get("played", {})
    last = played.get(today_key, {}).get(prayer)
    if not last:
        return False
    try:
        last_ts = float(last)
    except Exception:
        return True
    return (time.time() - last_ts) < REPLAY_SUPPRESS_SECONDS


def _mark_played(today_key: str, prayer: str) -> None:
    state = _load_state()
    state.setdefault("played", {})
    state["played"].setdefault(today_key, {})
    state["played"][today_key][prayer] = time.time()
    _save_state(state)


def play_adhan(label: str) -> None:
    print(f"🔊 Playing Adzan for {label.upper()}")

    if shutil.which("mpg123") is None:
        print("❌ mpg123 not found. Install: sudo apt install mpg123")
        return

    if not ADHAN_FILE.exists():
        print(f"❌ Adhan file not found: {ADHAN_FILE}")
        return

    # IMPORTANT: "-o" (letter o), not "-0" (zero)
    subprocess.run(["mpg123", "-o", "alsa", "-q", str(ADHAN_FILE)], check=False)


def _tz_offset_hours_for_date(date: dt.date, tz: ZoneInfo) -> float:
    # PrayTimes expects numeric timezone hours. Use noon to avoid DST midnight edge.
    noon = dt.datetime.combine(date, dt.time(12, 0), tzinfo=tz)
    off = noon.utcoffset()
    return (off.total_seconds() / 3600.0) if off else 0.0


def _get_prayer_times(date: dt.date, tz: ZoneInfo) -> dict:
    pt = PrayTimes("custom")
    pt.adjust({"fajr": FAJR_ANGLE, "isha": ISHA_ANGLE, "asr": ASR_METHOD})
    tz_hours = _tz_offset_hours_for_date(date, tz)
    return pt.getTimes(date, (LAT, LON), tz_hours)


def _parse_hhmm(s: str):
    try:
        hh, mm = s.split(":")
        return int(hh), int(mm)
    except Exception:
        return None


def run_test(delay_seconds: int, test_all: bool) -> None:
    print(f"🧪 TEST MODE: will play in {delay_seconds} seconds")
    time.sleep(max(0, delay_seconds))

    if not test_all:
        play_adhan("test")
        return

    # Play each prayer one-by-one (2 seconds gap) for demo
    for p in PRAYERS:
        play_adhan(p)
        time.sleep(2)


def main() -> None:
    args = parse_args()

    # --- Test mode (for checking sound quickly) ---
    if args.test or args.test_all:
        run_test(args.test_delay, test_all=args.test_all)
        return

    tz = ZoneInfo(TZ_NAME)

    while True:
        now = dt.datetime.now(tz)
        today = now.date()
        today_key = today.isoformat()

        times = _get_prayer_times(today, tz)

        print("📅 Prayer times today:")
        for p in PRAYERS:
            print(f"{p.capitalize():8s}: {times.get(p, '??:??')}")

        schedule = []
        for p in PRAYERS:
            parsed = _parse_hhmm(times.get(p, ""))
            if not parsed:
                print(f"⚠️  Skipping {p}: invalid time '{times.get(p)}'")
                continue
            hh, mm = parsed
            target = dt.datetime.combine(today, dt.time(hh, mm), tzinfo=tz)
            schedule.append((p, target))
        schedule.sort(key=lambda x: x[1])

        for prayer, target in schedule:
            now = dt.datetime.now(tz)

            # If already played (restart protection), skip
            if _already_played(today_key, prayer):
                continue

            # If too late (service started after event), skip
            if now > target + dt.timedelta(seconds=GRACE_SECONDS):
                continue

            # Wait until adhan time
            while dt.datetime.now(tz) < target:
                time.sleep(0.5)

            # Final guard (avoid double-trigger on restart/race)
            if not _already_played(today_key, prayer):
                play_adhan(prayer)
                _mark_played(today_key, prayer)

        # Sleep until next day, then recompute
        tomorrow = today + dt.timedelta(days=1)
        next_run = dt.datetime.combine(tomorrow, dt.time(0, 1), tzinfo=tz)
        sleep_s = max(5.0, (next_run - dt.datetime.now(tz)).total_seconds())
        time.sleep(sleep_s)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="Play adhan once after --test-delay seconds, then exit")
    ap.add_argument("--test-all", action="store_true", help="Play adhan for all prayers sequentially (demo), then exit")
    ap.add_argument("--test-delay", type=int, default=3, help="Delay seconds for test mode (default: 3)")
    return ap.parse_args()


if __name__ == "__main__":
    main()

