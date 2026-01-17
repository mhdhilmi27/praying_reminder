# Adhan Visual

Full-screen prayer time display with adhan playback. Designed for TV display (Tkinter UI) and works on Windows or Raspberry Pi.

## Requirements

- Python 3.10+
- `praytimes` package
- Audio player:
  - Linux/Raspberry Pi: `mpg123`
  - Windows: uses a PowerShell MediaPlayer fallback (no extra install)

## Quick start (Windows)

```bash
python -m pip install praytimes
python adhan_visual.py
```

## Quick start (Raspberry Pi / Debian)

```bash
sudo apt update
sudo apt install -y python3-venv python3-full mpg123
python3 -m venv .venv
source .venv/bin/activate
pip install praytimes
python adhan_visual.py
```

## How to exit full-screen

Press `Esc` to close the app.

## Configuration

Edit these values in `adhan_visual.py`:

- `MASJID_NAME` (display name)
- `LAT`, `LON`, `TIMEZONE`
- `FAJR_ANGLE`, `ISHA_ANGLE`, `ASR_METHOD`
- `ADHAN_FILE` (MP3 path)
- `FONT_SCALE`, `PRAYER_FONT_SCALE`

## Notes

- The app recalculates prayer times daily at midnight while running.
- Adhan plays at each prayer time (Fajr, Dhuhr, Asr, Maghrib, Isha).
- If you run over SSH, you need a GUI display (VNC or X11 forwarding).
