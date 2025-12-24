# Windows 11 audio output toggle (Python)

This repo contains a small Python script to **toggle your default Windows output device** between:

- `Speakers (USB Audio Device)`
- `Headphones (Arctis 7 Game)`

It uses Windows Core Audio APIs (it does **not** click through Settings UI).

## Requirements

- Windows 11
- Python 3.10+ recommended

## Install

```bash
python -m pip install -r requirements.txt
```

## Usage

List devices (and see the current default):

```bash
python toggle_audio_output.py --list
```

Toggle between the two configured device names:

```bash
python toggle_audio_output.py
```

Force a specific device:

```bash
python toggle_audio_output.py --speakers
python toggle_audio_output.py --headphones
```

Or set by any matching name:

```bash
python toggle_audio_output.py --set "Speakers (USB Audio Device)"
```

## Customize the device names

Edit the constants at the top of `toggle_audio_output.py`:

- `SPEAKERS_NAME`
- `HEADPHONES_NAME`

If the script says it can’t find a device, run `--list` and copy/paste the exact name shown.
