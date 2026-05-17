# XEMU Redump Repair

A Windows tool for repairing Xbox Redump ISOs so they can be used with XEMU.

<p align="center">
  <img src="assets/app-icon.png" alt="XEMU Redump Repair icon" width="128">
</p>

## Version 2.0.1 - Python Edition

Download:
https://github.com/SmokeyMcGames/XEMU-Redump-Repair/releases/download/v2.0.1/XEMU.Redump.Repair.2.0.1.exe

This version replaces the original Windows Forms/DD for Windows workflow with a native Python repair engine. The repair operation removes the first `387 MiB` from a Redump ISO and writes the remaining data to a new repaired ISO.

## What's New

- Rebuilt as a Python app with no bundled `dd.exe` dependency.
- Added support for repairing one ISO, multiple selected ISOs, or every ISO in a folder.
- Added detection for ISOs that already look repaired/XISO.
- Added progress reporting during repair.
- Added cancel handling that removes unfinished `.part` files.
- Added command-line repair support for advanced users.

## How To Use

1. Download `XEMU.Redump.Repair.2.0.1.exe` from the release link above.
2. Open the app.
3. Click `Add ISO(s)` to choose one or more Redump ISOs, or click `Add Folder` to scan a folder.
4. Choose the save file or output folder.
5. Click `Repair`.
6. Wait for the progress bar to finish.
7. Use the repaired `[Fixed]` ISO with XEMU.

## Notes

Most Xbox Redump ISOs are around `7.6 GiB`.

If a game is below about `7.3 GiB`, it may not be a proper Xbox Redump image and may not work with XEMU or the repair tool. In that case, you may need a different dump of the game.

Some improperly dumped Xbox games may still boot in CXBX, but not in XEMU.

## Command Line

The executable is intended for the GUI, but the Python source also supports command-line repair:

```powershell
python .\xemu_redump_repair.py "input.iso" "output.iso"
```

Replace an existing output file:

```powershell
python .\xemu_redump_repair.py "input.iso" "output.iso" --force
```

## Build From Source

Requirements:

- Python 3.9 or newer
- Tkinter, included with the standard Windows Python installer

Run the app from source:

```powershell
pythonw .\xemu_redump_repair.pyw
```

Run tests:

```powershell
python -m unittest -v
```

Build the Windows executable:

```powershell
python -m pip install -r requirements-dev.txt
pyinstaller --noconfirm --onefile --windowed --name "XEMU.Redump.Repair.2.0.1" --icon assets\XemuRepair.ico xemu_redump_repair.pyw
```
