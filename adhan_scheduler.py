#!/usr/bin/env python3
import time
import datetime
import subprocess
from praytimes import PrayTimes

# ===== CONFIG (FROM FIVEPRAYERS) =====
LAT = 55.70941493357022
LON = 13.170082073009272
TIMEZONE = 1        # Sweden (CET). DST handled by system
ASR_METHOD = 'Hanafi'

FAJR_ANGLE = 18.5
ISHA_ANGLE = 19

ADHAN_FILE = "/adhan/mecca.mp3"
PRAYERS = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
# ====================================

def play_adhan(prayer):
    print(f"🔊 Playing Adzan for {prayer.upper()}")
    subprocess.run(["mpg123", "-q", ADHAN_FILE])


def main():
    pt = PrayTimes('custom')
    pt.adjust({
        'fajr': FAJR_ANGLE,
        'isha': ISHA_ANGLE,
        'asr': ASR_METHOD
    })

    today = datetime.date.today()
    times = pt.getTimes(today, (LAT, LON), TIMEZONE)

    print("📅 Prayer times today:")
    for p in PRAYERS:
        print(f"{p.capitalize():8s}: {times[p]}")

    # Convert to timestamps
    schedule = []
    for p in PRAYERS:
        hh, mm = map(int, times[p].split(':'))
        t = datetime.datetime.combine(
            today, datetime.time(hh, mm)
        ).timestamp()
        schedule.append((p, t))
        #schedule.append((p, time.time() + 3))

    schedule.sort()

    for prayer, ts in schedule:
        while time.time() < ts:
            time.sleep(1)
        play_adhan(prayer)

if __name__ == "__main__":
    main()
