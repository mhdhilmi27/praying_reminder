#!/usr/bin/env python3
import datetime
import math
import os
import shutil
import subprocess
import sys
import time
import tkinter as tk

import praytimes

# ===== CONFIG (FROM FIVEPRAYERS) =====
FONT_SCALE = 1.35
PRAYER_FONT_SCALE = 1.7
LAT = 55.70941493357022
LON = 13.170082073009272
TIMEZONE = 1        # Sweden (CET). DST handled by system
ASR_METHOD = "Standard"

FAJR_ANGLE = 15.0
ISHA_ANGLE = 15.1

ADHAN_FILE = "/adhan/mecca.mp3"
ADHAN_PRAYERS = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
DISPLAY_PRAYERS = ["fajr", "dhuhr", "asr", "maghrib", "isha", "sunrise"]
PRAYER_LABELS = {
    "fajr": "Fajr",
    "dhuhr": "Dhuhr",
    "asr": "Asr",
    "maghrib": "Maghrib",
    "isha": "Isha",
    "sunrise": "Sunrise",
}
MASJID_NAME = "Arkana's Family"
# ====================================

BG = "#0b0b0b"
PANEL = "#141414"
WHITE = "#f5f5f5"
MUTED = "#a0a0a0"
ACCENT = "#8bc34a"


def build_praytimes():
    pt = praytimes.PrayTimes("custom")
    pt.adjust(
        {
            "fajr": FAJR_ANGLE,
            "isha": ISHA_ANGLE,
            "asr": ASR_METHOD,
        }
    )
    return pt


def compute_schedule(pt, date_obj):
    times = pt.getTimes(date_obj, (LAT, LON), TIMEZONE)
    schedule = []
    for p in ADHAN_PRAYERS:
        hh, mm = map(int, times[p].split(":"))
        dt = datetime.datetime.combine(date_obj, datetime.time(hh, mm))
        schedule.append((p, dt))
    return times, schedule


def resolve_adhan_path(path):
    if os.path.isabs(path) and os.path.exists(path):
        return path
    # Handle leading "/" on Windows or relative paths in the repo.
    rel_path = path.lstrip("/\\")
    candidate = os.path.join(os.path.dirname(__file__), rel_path)
    return candidate


def play_adhan(prayer):
    adhan_path = resolve_adhan_path(ADHAN_FILE)
    print(f"Playing Adzan for {prayer.upper()}")
    if shutil.which("mpg123"):
        subprocess.run(["mpg123", "-q", adhan_path])
        return
    if sys.platform.startswith("win"):
        # Use Windows MediaPlayer via PowerShell for MP3 playback.
        ps = (
            "Add-Type -AssemblyName presentationCore; "
            "$p=New-Object System.Windows.Media.MediaPlayer; "
            f"$p.Open([Uri]'{adhan_path}'); "
            "$p.Play(); Start-Sleep -Seconds 20;"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps])
        return
    print("mpg123 not found; install it or adjust ADHAN_FILE/player.")


class AdhanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Adhan Visual")
        self.root.configure(bg=BG)
        self.root.attributes("-fullscreen", True)

        self.pt = build_praytimes()
        self.last_played = set()
        self.current_date = datetime.date.today()
        self.times, self.schedule = compute_schedule(self.pt, self.current_date)

        top = tk.Frame(root, bg=BG)
        top.pack(fill="x", padx=16, pady=(10, 6))

        title = tk.Label(
            top,
            text=MASJID_NAME,
            font=("Georgia", int(24 * FONT_SCALE), "bold"),
            fg=WHITE,
            bg=BG,
        )
        title.pack(anchor="w")

        main = tk.Frame(root, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=8)

        left = tk.Frame(main, bg=PANEL, padx=24, pady=24)
        right = tk.Frame(main, bg=PANEL, padx=24, pady=24)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        self.now_label = tk.Label(
            left,
            text="",
            font=("Helvetica", int(48 * FONT_SCALE), "bold"),
            fg=WHITE,
            bg=PANEL,
        )
        self.now_label.pack(anchor="w")

        self.clock_canvas = tk.Canvas(
            left,
            width=int(180 * FONT_SCALE),
            height=int(180 * FONT_SCALE),
            bg=PANEL,
            highlightthickness=0,
        )
        self.clock_canvas.pack(anchor="w", pady=(6, 10))

        self.date_label = tk.Label(
            left,
            text="",
            font=("Helvetica", int(16 * FONT_SCALE)),
            fg=MUTED,
            bg=PANEL,
        )
        self.date_label.pack(anchor="w", pady=(4, 14))

        self.next_label = tk.Label(
            left,
            text="",
            font=("Helvetica", int(20 * FONT_SCALE)),
            fg=ACCENT,
            bg=PANEL,
        )
        self.next_label.pack(anchor="w")

        self.countdown_label = tk.Label(
            left,
            text="",
            font=("Helvetica", int(36 * FONT_SCALE), "bold"),
            fg=WHITE,
            bg=PANEL,
        )
        self.countdown_label.pack(anchor="w", pady=(6, 16))

        self.upcoming_header = tk.Label(
            left,
            text="Upcoming",
            font=("Helvetica", int(14 * FONT_SCALE), "bold"),
            fg=WHITE,
            bg=PANEL,
        )
        self.upcoming_header.pack(anchor="w", pady=(6, 6))

        self.upcoming_labels = []
        for _ in range(3):
            lbl = tk.Label(
                left,
                text="",
                font=("Helvetica", int(14 * FONT_SCALE)),
                fg=MUTED,
                bg=PANEL,
            )
            lbl.pack(anchor="w")
            self.upcoming_labels.append(lbl)

        self.kids_canvas = tk.Canvas(
            left,
            width=int(320 * FONT_SCALE),
            height=int(90 * FONT_SCALE),
            bg=PANEL,
            highlightthickness=0,
        )
        self.kids_canvas.pack(anchor="w", pady=(16, 0))
        self.kids_phase = 0

        header = tk.Label(
            right,
            text="Prayer Times",
            font=("Helvetica", int(16 * PRAYER_FONT_SCALE), "bold"),
            fg=WHITE,
            bg=PANEL,
        )
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.rows = {}
        self.name_labels = {}
        row = 1
        for p in DISPLAY_PRAYERS:
            name = tk.Label(
                right,
                text=PRAYER_LABELS[p],
                font=("Helvetica", int(14 * PRAYER_FONT_SCALE)),
                fg=WHITE,
                bg=PANEL,
            )
            time_lbl = tk.Label(
                right,
                text=self.times[p],
                font=("Helvetica", int(14 * PRAYER_FONT_SCALE)),
                fg=WHITE,
                bg=PANEL,
            )
            if p == "sunrise":
                divider = tk.Frame(right, bg=MUTED, height=1)
                divider.grid(row=row, column=0, columnspan=2, sticky="we", pady=(8, 6))
                row += 1
            name.grid(row=row, column=0, sticky="w", pady=4)
            time_lbl.grid(row=row, column=1, sticky="e", pady=4, padx=(20, 0))
            row += 1
            self.rows[p] = time_lbl
            self.name_labels[p] = name

        self.tick()

    def refresh_day(self):
        self.current_date = datetime.date.today()
        self.times, self.schedule = compute_schedule(self.pt, self.current_date)
        self.last_played.clear()
        for p in DISPLAY_PRAYERS:
            self.rows[p].configure(text=self.times[p])

    def find_next_prayer(self, now):
        for prayer, dt in self.schedule:
            if dt > now:
                return prayer, dt
        # Next prayer is tomorrow's Fajr
        tomorrow = self.current_date + datetime.timedelta(days=1)
        times, schedule = compute_schedule(self.pt, tomorrow)
        return schedule[0][0], schedule[0][1]

    def tick(self):
        now = datetime.datetime.now()
        if now.date() != self.current_date:
            self.refresh_day()

        self.now_label.configure(text=now.strftime("%H:%M:%S"))
        self.date_label.configure(text=now.strftime("%A, %d %B %Y"))
        self.draw_analog_clock(now)

        next_prayer, next_dt = self.find_next_prayer(now)
        next_time = next_dt.strftime("%H:%M")
        remaining = next_dt - now
        total_sec = int(remaining.total_seconds())
        if total_sec < 0:
            total_sec = 0
        hrs = total_sec // 3600
        mins = (total_sec % 3600) // 60
        secs = total_sec % 60
        self.next_label.configure(text=f"Next: {next_prayer.capitalize()} at {next_time}")
        self.countdown_label.configure(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")

        upcoming = []
        for prayer, dt in self.schedule:
            if dt > now:
                upcoming.append((prayer, dt))
        if len(upcoming) < 3:
            tomorrow = self.current_date + datetime.timedelta(days=1)
            _, schedule = compute_schedule(self.pt, tomorrow)
            upcoming.extend(schedule)
        for i, lbl in enumerate(self.upcoming_labels):
            p, dt = upcoming[i]
            lbl.configure(text=f"{p.capitalize():8s}  {dt.strftime('%H:%M')}")

        for prayer in DISPLAY_PRAYERS:
            color = ACCENT if prayer == next_prayer else WHITE
            self.name_labels[prayer].configure(fg=color)
            self.rows[prayer].configure(fg=color)

        # Play adhan when a prayer time hits (once per day)
        for prayer, dt in self.schedule:
            if prayer not in self.last_played and now >= dt:
                if (now - dt).total_seconds() > 60:
                    continue
                play_adhan(prayer)
                self.last_played.add(prayer)

        self.root.after(200, self.tick)

    def draw_analog_clock(self, now):
        c = self.clock_canvas
        c.delete("all")
        w = int(c["width"])
        h = int(c["height"])
        cx = w // 2
        cy = h // 2
        r = min(w, h) // 2 - 6
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=MUTED, width=2)
        # hour marks
        for i in range(12):
            angle = (i / 12.0) * 2 * 3.14159265
            x1 = cx + (r - 6) * math.sin(angle)
            y1 = cy - (r - 6) * math.cos(angle)
            x2 = cx + r * math.sin(angle)
            y2 = cy - r * math.cos(angle)
            c.create_line(x1, y1, x2, y2, fill=MUTED, width=2)

        hour = (now.hour % 12) + now.minute / 60.0
        minute = now.minute + now.second / 60.0
        second = now.second
        # hour hand
        angle = (hour / 12.0) * 2 * 3.14159265
        c.create_line(
            cx,
            cy,
            cx + (r * 0.5) * math.sin(angle),
            cy - (r * 0.5) * math.cos(angle),
            fill=WHITE,
            width=4,
        )
        # minute hand
        angle = (minute / 60.0) * 2 * 3.14159265
        c.create_line(
            cx,
            cy,
            cx + (r * 0.75) * math.sin(angle),
            cy - (r * 0.75) * math.cos(angle),
            fill=WHITE,
            width=3,
        )
        # second hand
        angle = (second / 60.0) * 2 * 3.14159265
        c.create_line(
            cx,
            cy,
            cx + (r * 0.85) * math.sin(angle),
            cy - (r * 0.85) * math.cos(angle),
            fill=ACCENT,
            width=2,
        )
        c.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=ACCENT, outline=ACCENT)

        self.draw_kids_animation()

    def draw_kids_animation(self):
        c = self.kids_canvas
        c.delete("all")
        w = int(c["width"])
        h = int(c["height"])
        baseline = h - 18
        # Subtle motion phase
        self.kids_phase = (self.kids_phase + 2) % (w + 120)

        # Train (green line + cars)
        train_x = w - (self.kids_phase % (w + 120))
        c.create_line(0, baseline + 8, w, baseline + 8, fill=MUTED, width=2)
        for i in range(3):
            x = train_x + i * 28
            c.create_rectangle(x, baseline - 18, x + 22, baseline - 4, fill=ACCENT, outline=ACCENT)
            c.create_oval(x + 3, baseline - 2, x + 9, baseline + 4, fill=WHITE, outline=WHITE)
            c.create_oval(x + 13, baseline - 2, x + 19, baseline + 4, fill=WHITE, outline=WHITE)

        # Car (white) moving opposite
        car_x = (self.kids_phase * 2) % (w + 80) - 60
        c.create_rectangle(car_x, baseline - 36, car_x + 36, baseline - 22, fill=WHITE, outline=WHITE)
        c.create_rectangle(car_x + 8, baseline - 46, car_x + 26, baseline - 36, fill=WHITE, outline=WHITE)
        c.create_oval(car_x + 6, baseline - 20, car_x + 12, baseline - 14, fill=ACCENT, outline=ACCENT)
        c.create_oval(car_x + 24, baseline - 20, car_x + 30, baseline - 14, fill=ACCENT, outline=ACCENT)

        # Plane (white) gliding
        plane_x = (self.kids_phase * 3) % (w + 100) - 80
        plane_y = 18 + int(6 * math.sin(self.kids_phase / 15.0))
        c.create_polygon(
            plane_x,
            plane_y,
            plane_x + 24,
            plane_y + 6,
            plane_x,
            plane_y + 12,
            plane_x + 6,
            plane_y + 6,
            fill=WHITE,
            outline=WHITE,
        )
        c.create_line(plane_x + 6, plane_y + 6, plane_x + 18, plane_y + 2, fill=ACCENT, width=2)



def main():
    root = tk.Tk()
    root.bind("<Escape>", lambda e: root.destroy())
    app = AdhanApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
FONT_SCALE = 1.35
