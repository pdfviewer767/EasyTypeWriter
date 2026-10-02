# EasyTypeWriter

EasyTypeWriter is a desktop touch-typing trainer with Arabic and English lessons, practice exercises, speed tests, and progress tracking.

## Requirements

- Python 3.9 or newer
- Windows for the packaged build

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Build

```powershell
python build.py
```

The single-file executable is written to `dist/EasyTypeWriter.exe`.

User accounts, settings, progress, profile images, and encryption keys are stored in the current user's application-data directory and are intentionally excluded from this repository.