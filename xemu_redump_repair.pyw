"""No-console Windows launcher for XEMU Redump Repair."""

from __future__ import annotations

import tkinter.messagebox as messagebox

from xemu_redump_repair import APP_NAME, RepairApp


def main() -> int:
    try:
        app = RepairApp()
        app.mainloop()
    except Exception as exc:
        messagebox.showerror(APP_NAME, f"Unable to start the app:\n{exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
