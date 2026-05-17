"""XEMU Redump Repair - Python edition.

This replaces the original dd.exe call with native Python file copying:

    dd if=input.iso of=output.iso skip=387 bs=1M --progress

The repair operation skips the first 387 MiB of the selected ISO and writes the
remaining bytes to a new ISO.
"""

from __future__ import annotations

import argparse
import os
import queue
import sys
import tempfile
import threading
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_NAME = "XEMU Redump Repair"
APP_VERSION = "2.0.0"
AUTHOR_URL = "https://www.youtube.com/smokeymcgames"
SKIP_MIB = 387
SKIP_BYTES = SKIP_MIB * 1024 * 1024
CHUNK_SIZE = 8 * 1024 * 1024
REDUMP_HINT_BYTES = int(7.3 * 1024 * 1024 * 1024)
XDVDFS_SECTOR_SIZE = 2048
XDVDFS_DESCRIPTOR_SECTOR = 32
XDVDFS_DESCRIPTOR_OFFSET = XDVDFS_SECTOR_SIZE * XDVDFS_DESCRIPTOR_SECTOR
XDVDFS_MAGIC = b"MICROSOFT*XBOX*MEDIA"
WINDOW_WIDTH = 860
WINDOW_HEIGHT = 640

COLOR_BG = "#111820"
COLOR_SURFACE = "#f7f9fb"
COLOR_SURFACE_ALT = "#eaf0f3"
COLOR_TEXT = "#18232b"
COLOR_MUTED = "#667782"
COLOR_ACCENT = "#1f8f7a"
COLOR_ACCENT_DARK = "#166b5b"
COLOR_DANGER = "#b94747"

ISO_ALREADY_XISO = "already_xiso"
ISO_REDUMP = "redump"
ISO_UNKNOWN = "unknown"


class RepairCancelled(Exception):
    """Raised when the user cancels an active repair."""


@dataclass(frozen=True)
class IsoInspection:
    status: str
    needs_repair: bool
    message: str


@dataclass(frozen=True)
class RepairJob:
    input_path: Path
    output_path: Path
    inspection: IsoInspection


def format_bytes(value: int) -> str:
    """Return a compact human-readable byte count."""
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{value} B"


def repaired_output_name(input_path: Path) -> str:
    if not input_path.name:
        return "[Fixed].iso"
    return f"[Fixed]{input_path.name}"


def default_output_path(input_path: Path) -> Path:
    return input_path.with_name(repaired_output_name(input_path))


def find_iso_files(folder_path: Path) -> list[Path]:
    if not folder_path.exists() or not folder_path.is_dir():
        return []

    return sorted(
        (path for path in folder_path.rglob("*.iso") if path.is_file()),
        key=lambda path: str(path).lower(),
    )


def unique_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()

    for path in paths:
        key = str(path.resolve()).lower()
        if key in seen:
            continue

        seen.add(key)
        unique.append(path)

    return unique


def default_batch_output_folder(input_paths: list[Path]) -> Optional[Path]:
    if not input_paths:
        return None

    parent_paths = [str(path.parent) for path in input_paths]
    try:
        common_path = Path(os.path.commonpath(parent_paths))
    except ValueError:
        return input_paths[0].parent

    return common_path if common_path.exists() else input_paths[0].parent


def output_path_for_job(input_path: Path, output_target: Path, batch_mode: bool) -> Path:
    if batch_mode:
        return output_target / repaired_output_name(input_path)
    return output_target


def validate_paths(input_path: Path, output_path: Path) -> None:
    if not input_path:
        raise ValueError("Choose an ISO/XISO file first.")

    if not output_path:
        raise ValueError("Choose a save location first.")

    if not input_path.exists():
        raise ValueError("The selected ISO does not exist.")

    if not input_path.is_file():
        raise ValueError("The selected ISO path is not a file.")

    if input_path.resolve() == output_path.resolve():
        raise ValueError("The output file must be different from the input file.")

    if input_path.stat().st_size <= SKIP_BYTES:
        raise ValueError(
            f"The selected file is too small to repair. It must be larger than "
            f"{format_bytes(SKIP_BYTES)}."
        )

    output_parent = output_path.parent
    if not output_parent.exists():
        raise ValueError("The save folder does not exist.")


def has_xdvdfs_magic(input_path: Path, offset: int) -> bool:
    if input_path.stat().st_size < offset + len(XDVDFS_MAGIC):
        return False

    with input_path.open("rb") as source:
        source.seek(offset)
        return source.read(len(XDVDFS_MAGIC)) == XDVDFS_MAGIC


def inspect_iso(input_path: Path) -> IsoInspection:
    """Identify whether an ISO looks like a repaired XISO or Redump image."""
    if not input_path.exists() or not input_path.is_file():
        return IsoInspection(ISO_UNKNOWN, False, "The selected ISO could not be read.")

    xiso_magic_found = has_xdvdfs_magic(input_path, XDVDFS_DESCRIPTOR_OFFSET)
    redump_magic_found = has_xdvdfs_magic(
        input_path,
        SKIP_BYTES + XDVDFS_DESCRIPTOR_OFFSET,
    )

    if xiso_magic_found:
        return IsoInspection(
            ISO_ALREADY_XISO,
            False,
            "This already looks like an XISO/repaired image. Repair is probably not needed.",
        )

    if redump_magic_found:
        return IsoInspection(
            ISO_REDUMP,
            True,
            f"This looks like a Redump image. Repair will remove the first {SKIP_MIB} MiB.",
        )

    return IsoInspection(
        ISO_UNKNOWN,
        False,
        "This does not match the expected XISO or Redump layout. Repair may not work.",
    )


def repair_iso(
    input_path: Path,
    output_path: Path,
    *,
    progress_queue: Optional[queue.Queue] = None,
    cancel_event: Optional[threading.Event] = None,
    progress_kind: str = "progress",
    done_kind: str = "done",
) -> None:
    """Repair an ISO by skipping the Redump header/padding and copying the rest."""
    validate_paths(input_path, output_path)

    total_size = input_path.stat().st_size
    bytes_to_copy = total_size - SKIP_BYTES
    copied = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".part",
        dir=str(output_path.parent),
    )
    os.close(fd)
    temp_path = Path(temp_name)

    def post(kind: str, payload: object = None) -> None:
        if progress_queue is not None:
            progress_queue.put((kind, payload))

    try:
        with input_path.open("rb") as source, temp_path.open("wb") as target:
            source.seek(SKIP_BYTES)

            while copied < bytes_to_copy:
                if cancel_event is not None and cancel_event.is_set():
                    raise RepairCancelled()

                chunk = source.read(min(CHUNK_SIZE, bytes_to_copy - copied))
                if not chunk:
                    break

                target.write(chunk)
                copied += len(chunk)
                post(progress_kind, (copied, bytes_to_copy))

        if copied != bytes_to_copy:
            raise IOError(
                f"Repair ended early. Copied {format_bytes(copied)} of "
                f"{format_bytes(bytes_to_copy)}."
            )

        os.replace(temp_path, output_path)
        post(done_kind, output_path)
    except BaseException:
        try:
            temp_path.unlink(missing_ok=True)
        finally:
            raise


class RepairApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)

        self.input_paths: list[Path] = []
        self.source_summary = tk.StringVar(value="No ISOs selected")
        self.output_path = tk.StringVar()
        self.output_label = tk.StringVar(value="Save repaired ISO as")
        self.status_text = tk.StringVar(value="Add one ISO, multiple ISOs, or a folder.")
        self.progress_text = tk.StringVar(value="")
        self.progress_value = tk.DoubleVar(value=0)

        self._queue: queue.Queue = queue.Queue()
        self._cancel_event = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._started_at: Optional[float] = None
        self._current_job_label = ""

        self._build_styles()
        self._build_ui()
        self._poll_queue()

    def _build_styles(self) -> None:
        self.configure(bg=COLOR_BG)
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("Root.TFrame", background=COLOR_BG)
        style.configure("Hero.TFrame", background=COLOR_BG)
        style.configure("Panel.TFrame", background=COLOR_SURFACE)
        style.configure("Path.TFrame", background=COLOR_SURFACE)
        style.configure("Actions.TFrame", background=COLOR_SURFACE)
        style.configure(
            "Title.TLabel",
            background=COLOR_BG,
            foreground="#f5f7f8",
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=COLOR_BG,
            foreground="#b7c5cd",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Badge.TLabel",
            background=COLOR_ACCENT,
            foreground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 5),
        )
        style.configure(
            "Panel.TLabel",
            background=COLOR_SURFACE,
            foreground=COLOR_TEXT,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Muted.TLabel",
            background=COLOR_SURFACE,
            foreground=COLOR_MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Loaded.TLabel",
            background=COLOR_SURFACE,
            foreground=COLOR_TEXT,
            font=("Segoe UI", 13, "bold"),
        )
        style.configure(
            "TEntry",
            fieldbackground="#ffffff",
            foreground=COLOR_TEXT,
            bordercolor="#c9d4d9",
            lightcolor="#c9d4d9",
            darkcolor="#c9d4d9",
            insertcolor=COLOR_TEXT,
            padding=(8, 7),
        )
        style.map(
            "TEntry",
            bordercolor=[("focus", COLOR_ACCENT)],
            lightcolor=[("focus", COLOR_ACCENT)],
            darkcolor=[("focus", COLOR_ACCENT)],
        )
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
        style.configure(
            "Accent.TButton",
            background=COLOR_ACCENT,
            foreground="#ffffff",
            bordercolor=COLOR_ACCENT,
            focusthickness=0,
            font=("Segoe UI", 11, "bold"),
            padding=(14, 9),
        )
        style.map(
            "Accent.TButton",
            background=[("active", COLOR_ACCENT_DARK), ("disabled", "#9dbdb5")],
            foreground=[("disabled", "#edf3f1")],
        )
        style.configure(
            "Danger.TButton",
            background="#f7eeee",
            foreground=COLOR_DANGER,
            bordercolor="#e0b7b7",
            padding=(14, 9),
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#f0dada"), ("disabled", "#f5f5f5")],
            foreground=[("disabled", "#b9b9b9")],
        )
        style.configure(
            "Horizontal.TProgressbar",
            background=COLOR_ACCENT,
            troughcolor=COLOR_SURFACE_ALT,
            bordercolor=COLOR_SURFACE_ALT,
            lightcolor=COLOR_ACCENT,
            darkcolor=COLOR_ACCENT,
            thickness=14,
        )
        style.configure("Status.TLabel", background=COLOR_BG, foreground="#d7e2e7")

    def _build_ui(self) -> None:
        root = ttk.Frame(self, style="Root.TFrame", padding=(24, 20))
        root.pack(fill=tk.BOTH, expand=True)

        hero = ttk.Frame(root, style="Hero.TFrame")
        hero.pack(fill=tk.X)
        hero.columnconfigure(0, weight=1)

        ttk.Label(hero, text=APP_NAME, style="Title.TLabel").grid(
            row=0, column=0, sticky=tk.W
        )
        ttk.Label(hero, text="PYTHON EDITION", style="Badge.TLabel").grid(
            row=0, column=1, sticky=tk.E, padx=(12, 0)
        )
        ttk.Label(
            hero,
            text=f"Repair Redump ISOs for XEMU by removing the first {SKIP_MIB} MiB.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(4, 0))

        panel = ttk.Frame(root, style="Panel.TFrame", padding=(22, 18))
        panel.pack(fill=tk.X, expand=False, pady=(18, 0))
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text="Source ISO/XISO queue", style="Muted.TLabel").grid(
            row=0, column=0, sticky=tk.W
        )

        source_actions = ttk.Frame(panel, style="Actions.TFrame")
        source_actions.grid(row=1, column=0, sticky=tk.EW, pady=(4, 8))
        source_actions.columnconfigure(0, weight=1)
        source_actions.columnconfigure(1, weight=1)
        source_actions.columnconfigure(2, weight=1)

        self.add_files_button = ttk.Button(
            source_actions,
            text="Add ISO(s)",
            command=self.choose_files,
        )
        self.add_files_button.grid(row=0, column=0, sticky=tk.EW, padx=(0, 8))

        self.add_folder_button = ttk.Button(
            source_actions,
            text="Add Folder",
            command=self.choose_folder,
        )
        self.add_folder_button.grid(row=0, column=1, sticky=tk.EW, padx=8)

        self.clear_button = ttk.Button(
            source_actions,
            text="Clear",
            command=self.clear_queue,
        )
        self.clear_button.grid(row=0, column=2, sticky=tk.EW, padx=(8, 0))

        ttk.Label(panel, textvariable=self.source_summary, style="Loaded.TLabel").grid(
            row=2, column=0, sticky=tk.W, pady=(0, 6)
        )

        queue_frame = tk.Frame(
            panel,
            bg="#ffffff",
            highlightbackground="#c9d4d9",
            highlightthickness=1,
        )
        queue_frame.grid(row=3, column=0, sticky=tk.EW, pady=(0, 12))
        queue_frame.columnconfigure(0, weight=1)

        self.queue_list = tk.Listbox(
            queue_frame,
            height=5,
            bd=0,
            highlightthickness=0,
            activestyle="none",
            bg="#ffffff",
            fg=COLOR_TEXT,
            selectbackground=COLOR_ACCENT,
            selectforeground="#ffffff",
            font=("Segoe UI", 9),
        )
        self.queue_list.grid(row=0, column=0, sticky=tk.EW)

        queue_scrollbar = ttk.Scrollbar(
            queue_frame,
            orient=tk.VERTICAL,
            command=self.queue_list.yview,
        )
        queue_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.queue_list.configure(yscrollcommand=queue_scrollbar.set)

        ttk.Label(panel, textvariable=self.output_label, style="Muted.TLabel").grid(
            row=4, column=0, sticky=tk.W
        )

        output_row = ttk.Frame(panel, style="Actions.TFrame")
        output_row.grid(row=5, column=0, sticky=tk.EW, pady=(4, 12))
        output_row.columnconfigure(0, weight=1)
        ttk.Entry(output_row, textvariable=self.output_path).grid(
            row=0, column=0, sticky=tk.EW
        )
        self.output_button = ttk.Button(
            output_row,
            text="Browse",
            command=self.choose_output,
        )
        self.output_button.grid(row=0, column=1, sticky=tk.EW, padx=(12, 0))

        progress_line = ttk.Frame(panel, style="Panel.TFrame")
        progress_line.grid(row=6, column=0, sticky=tk.EW, pady=(0, 6))
        progress_line.columnconfigure(0, weight=1)
        ttk.Label(progress_line, text="Progress", style="Muted.TLabel").grid(
            row=0, column=0, sticky=tk.W
        )
        ttk.Label(progress_line, textvariable=self.progress_text, style="Muted.TLabel").grid(
            row=0, column=1, sticky=tk.E
        )

        self.progress_bar = ttk.Progressbar(
            panel,
            variable=self.progress_value,
            maximum=100,
            mode="determinate",
        )
        self.progress_bar.grid(row=7, column=0, sticky=tk.EW, pady=(0, 14))

        actions = ttk.Frame(panel, style="Actions.TFrame")
        actions.grid(row=8, column=0, sticky=tk.EW)
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        actions.columnconfigure(2, weight=1)

        self.repair_button = ttk.Button(
            actions,
            text="Repair",
            style="Accent.TButton",
            command=self.start_repair,
        )
        self.repair_button.grid(row=0, column=0, sticky=tk.EW, padx=(0, 8))

        self.cancel_button = ttk.Button(
            actions,
            text="Cancel",
            style="Danger.TButton",
            command=self.cancel_repair,
            state=tk.DISABLED,
        )
        self.cancel_button.grid(row=0, column=1, sticky=tk.EW, padx=8)

        self.support_button = ttk.Button(
            actions,
            text="Support Me On YouTube",
            command=self.open_support,
        )
        self.support_button.grid(row=0, column=2, sticky=tk.EW, padx=(8, 0))

        ttk.Label(root, textvariable=self.status_text, style="Status.TLabel").pack(
            anchor=tk.W, pady=(12, 0)
        )

    def choose_input(self) -> None:
        self.choose_files()

    def choose_files(self) -> None:
        filenames = filedialog.askopenfilenames(
            title="Choose Redump ISO(s)",
            filetypes=(("ISO files", "*.iso"), ("All files", "*.*")),
        )
        if not filenames:
            return

        self._add_input_paths([Path(filename) for filename in filenames])

    def choose_folder(self) -> None:
        folder_name = filedialog.askdirectory(title="Choose Folder With ISO Files")
        if not folder_name:
            return

        folder_path = Path(folder_name)
        iso_paths = find_iso_files(folder_path)
        if not iso_paths:
            messagebox.showinfo(APP_NAME, "No .iso files were found in that folder.")
            return

        self._add_input_paths(iso_paths, preferred_output=folder_path)

    def clear_queue(self) -> None:
        self.input_paths = []
        self.output_path.set("")
        self.progress_value.set(0)
        self.progress_text.set("")
        self.status_text.set("Queue cleared.")
        self._refresh_queue_display()

    def _add_input_paths(
        self,
        paths: list[Path],
        *,
        preferred_output: Optional[Path] = None,
    ) -> None:
        iso_paths = [path for path in paths if path.suffix.lower() == ".iso"]
        if not iso_paths:
            messagebox.showinfo(APP_NAME, "No .iso files were selected.")
            return

        before_count = len(self.input_paths)
        self.input_paths = unique_paths([*self.input_paths, *iso_paths])
        added_count = len(self.input_paths) - before_count

        self._refresh_queue_display(preferred_output=preferred_output)
        if added_count == 0:
            self.status_text.set("Those ISO files are already in the queue.")
        elif len(self.input_paths) == 1:
            self._update_single_iso_status(self.input_paths[0])
        else:
            self.status_text.set(f"{len(self.input_paths)} ISO files queued.")

    def _refresh_queue_display(self, *, preferred_output: Optional[Path] = None) -> None:
        self.queue_list.delete(0, tk.END)
        for path in self.input_paths:
            self.queue_list.insert(tk.END, str(path))

        count = len(self.input_paths)
        if count == 0:
            self.source_summary.set("No ISOs selected")
            self.output_label.set("Save repaired ISO as")
            return

        if count == 1:
            source_path = self.input_paths[0]
            self.source_summary.set(source_path.name)
            self.output_label.set("Save repaired ISO as")
            self.output_path.set(str(default_output_path(source_path)))
            return

        output_folder = preferred_output or default_batch_output_folder(self.input_paths)
        self.source_summary.set(f"{count} ISOs queued")
        self.output_label.set("Save repaired ISOs to folder")
        if output_folder is not None:
            self.output_path.set(str(output_folder))

    def _update_single_iso_status(self, path: Path) -> None:
        size = path.stat().st_size
        inspection = inspect_iso(path)

        if inspection.status == ISO_ALREADY_XISO:
            self.status_text.set(inspection.message)
        elif inspection.status == ISO_REDUMP:
            self.status_text.set(f"Loaded {path.name}. {inspection.message}")
        elif size < REDUMP_HINT_BYTES:
            self.status_text.set(
                f"Loaded {path.name}. Warning: size is {format_bytes(size)}, "
                "which is smaller than a typical Xbox Redump."
            )
        else:
            self.status_text.set(
                f"Loaded {path.name} ({format_bytes(size)}). {inspection.message}"
            )

    def choose_output(self) -> None:
        batch_mode = len(self.input_paths) > 1
        output_value = self.output_path.get().strip()

        if batch_mode:
            initial_dir = output_value if output_value else None
            folder_name = filedialog.askdirectory(
                title="Choose Output Folder",
                initialdir=initial_dir,
            )
            if folder_name:
                self.output_path.set(folder_name)
                self.status_text.set("Output folder selected.")
            return

        initial_file = "[Fixed].iso"
        initial_dir = None

        if self.input_paths:
            input_path = self.input_paths[0]
            initial_file = repaired_output_name(input_path)
            initial_dir = str(input_path.parent)
        elif output_value:
            initial_dir = str(Path(output_value).parent)

        filename = filedialog.asksaveasfilename(
            title="Save Repaired ISO",
            defaultextension=".iso",
            initialdir=initial_dir,
            initialfile=initial_file,
            filetypes=(("ISO files", "*.iso"), ("All files", "*.*")),
        )
        if filename:
            self.output_path.set(filename)
            self.status_text.set("Save location selected.")

    def start_repair(self) -> None:
        try:
            jobs = self._build_jobs()
        except ValueError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return

        repairable_jobs = [job for job in jobs if job.inspection.status != ISO_ALREADY_XISO]
        skipped_count = len(jobs) - len(repairable_jobs)
        if not repairable_jobs:
            messagebox.showinfo(
                APP_NAME,
                f"No repairs needed. {skipped_count} ISO file(s) already look repaired/XISO.",
            )
            self.status_text.set("No repairs needed.")
            return

        unknown_jobs = [job for job in repairable_jobs if job.inspection.status == ISO_UNKNOWN]
        if unknown_jobs:
            if not messagebox.askyesno(
                APP_NAME,
                f"{len(unknown_jobs)} ISO file(s) do not match the expected XISO or "
                "Redump layout.\n\nTry repairing them anyway?",
            ):
                self.status_text.set("Repair canceled before starting.")
                return

        small_jobs = [
            job
            for job in repairable_jobs
            if job.input_path.stat().st_size < REDUMP_HINT_BYTES
        ]
        if small_jobs:
            if not messagebox.askyesno(
                APP_NAME,
                f"{len(small_jobs)} ISO file(s) are smaller than a typical Xbox Redump.\n\n"
                "Try repairing them anyway?",
            ):
                self.status_text.set("Repair canceled before starting.")
                return

        existing_outputs = [
            job.output_path
            for job in repairable_jobs
            if job.output_path.exists()
        ]
        if existing_outputs:
            if len(existing_outputs) == 1:
                prompt = f"{existing_outputs[0].name} already exists. Replace it?"
            else:
                prompt = f"{len(existing_outputs)} output files already exist. Replace them?"
            if not messagebox.askyesno(
                APP_NAME,
                prompt,
            ):
                self.status_text.set("Repair canceled before starting.")
                return

        self._cancel_event.clear()
        self.progress_value.set(0)
        self.progress_text.set("Starting repair...")
        self.status_text.set(f"Repairing {len(repairable_jobs)} ISO file(s).")
        self._started_at = time.monotonic()
        self._set_busy(True)

        self._worker = threading.Thread(
            target=self._repair_worker,
            args=(jobs,),
            daemon=True,
        )
        self._worker.start()

    def _build_jobs(self) -> list[RepairJob]:
        if not self.input_paths:
            raise ValueError("Add at least one ISO first.")

        output_value = self.output_path.get().strip()
        if not output_value:
            raise ValueError("Choose a save location first.")

        batch_mode = len(self.input_paths) > 1
        output_target = Path(output_value)

        if batch_mode:
            if not output_target.exists() or not output_target.is_dir():
                raise ValueError("Choose an existing output folder for batch repairs.")
        elif output_target.exists() and output_target.is_dir():
            raise ValueError("Choose a file path for a single ISO repair.")

        jobs: list[RepairJob] = []
        for input_path in self.input_paths:
            output_path = output_path_for_job(input_path, output_target, batch_mode)
            inspection = inspect_iso(input_path)
            if inspection.status != ISO_ALREADY_XISO:
                validate_paths(input_path, output_path)
            jobs.append(RepairJob(input_path, output_path, inspection))

        return jobs

    def _repair_worker(self, jobs: list[RepairJob]) -> None:
        results = {
            "total": len(jobs),
            "repaired": 0,
            "skipped": 0,
            "failed": [],
        }

        try:
            for index, job in enumerate(jobs, start=1):
                if self._cancel_event.is_set():
                    raise RepairCancelled()

                if job.inspection.status == ISO_ALREADY_XISO:
                    results["skipped"] += 1
                    self._queue.put(("job_skipped", (index, len(jobs), job.input_path.name)))
                    continue

                self._queue.put(("job_start", (index, len(jobs), job.input_path.name)))
                try:
                    repair_iso(
                        job.input_path,
                        job.output_path,
                        progress_queue=self._queue,
                        cancel_event=self._cancel_event,
                        progress_kind="job_progress",
                        done_kind="job_done",
                    )
                    results["repaired"] += 1
                except RepairCancelled:
                    raise
                except Exception as exc:
                    results["failed"].append((job.input_path.name, str(exc)))
                    self._queue.put(("job_error", (index, len(jobs), job.input_path.name, str(exc))))

            self._queue.put(("batch_done", results))
        except RepairCancelled:
            self._queue.put(("cancelled", None))
        except Exception as exc:
            self._queue.put(("error", str(exc)))

    def cancel_repair(self) -> None:
        self._cancel_event.set()
        self.status_text.set("Canceling after the current chunk finishes...")
        self.cancel_button.configure(state=tk.DISABLED)

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "job_start":
                    index, total, name = payload
                    self._current_job_label = f"{index}/{total} {name}"
                    self.progress_value.set(0)
                    self.progress_text.set(f"{self._current_job_label} - starting")
                    self.status_text.set(f"Repairing {name}")
                elif kind == "job_progress":
                    copied, total = payload
                    percent = (copied / total) * 100 if total else 0
                    elapsed = max(time.monotonic() - (self._started_at or time.monotonic()), 0.001)
                    rate = copied / elapsed
                    self.progress_value.set(percent)
                    self.progress_text.set(
                        f"{self._current_job_label} - {percent:5.1f}% - {format_bytes(copied)} of "
                        f"{format_bytes(total)} at {format_bytes(int(rate))}/s"
                    )
                elif kind == "job_done":
                    self.progress_value.set(100)
                    self.status_text.set(f"Saved repaired ISO to {payload}.")
                elif kind == "job_skipped":
                    index, total, name = payload
                    self.progress_text.set(f"{index}/{total} {name} - already repaired, skipped")
                    self.status_text.set(f"Skipped {name}; it already looks repaired/XISO.")
                elif kind == "job_error":
                    index, total, name, error = payload
                    self.progress_text.set(f"{index}/{total} {name} - failed")
                    self.status_text.set(f"Failed: {name} - {error}")
                elif kind == "batch_done":
                    self._set_busy(False)
                    self.progress_value.set(100)
                    repaired = payload["repaired"]
                    skipped = payload["skipped"]
                    failed = payload["failed"]
                    self.progress_text.set(
                        f"Done - repaired {repaired}, skipped {skipped}, failed {len(failed)}"
                    )
                    self.status_text.set("Repair queue complete.")
                    if failed:
                        messagebox.showwarning(
                            APP_NAME,
                            f"Repair complete with {len(failed)} failure(s). "
                            "Check the status line for the last failure.",
                        )
                    else:
                        messagebox.showinfo(
                            APP_NAME,
                            f"Repair complete. Repaired {repaired} ISO file(s); "
                            f"skipped {skipped}.",
                        )
                elif kind == "cancelled":
                    self.progress_text.set("Repair canceled. Partial file was removed.")
                    self.status_text.set("Repair canceled.")
                    self._set_busy(False)
                elif kind == "error":
                    self.progress_text.set("")
                    self.status_text.set("Repair failed.")
                    self._set_busy(False)
                    messagebox.showerror(APP_NAME, f"Repair failed:\n{payload}")
        except queue.Empty:
            pass

        self.after(100, self._poll_queue)

    def _set_busy(self, busy: bool) -> None:
        normal_state = tk.DISABLED if busy else tk.NORMAL
        for button in (
            self.add_files_button,
            self.add_folder_button,
            self.clear_button,
            self.output_button,
            self.support_button,
        ):
            button.configure(state=normal_state)

        self.repair_button.configure(state=tk.DISABLED if busy else tk.NORMAL)
        self.cancel_button.configure(state=tk.NORMAL if busy else tk.DISABLED)

    def open_support(self) -> None:
        webbrowser.open(AUTHOR_URL)


def run_cli(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)

    if output_path.exists() and not args.force:
        print(f"Output already exists: {output_path}", file=sys.stderr)
        print("Use --force to replace it.", file=sys.stderr)
        return 2

    last_percent = -1

    progress_queue: queue.Queue = queue.Queue()

    def progress_reader() -> None:
        nonlocal last_percent
        while True:
            kind, payload = progress_queue.get()
            if kind == "progress":
                copied, total = payload
                percent = int((copied / total) * 100) if total else 100
                if percent != last_percent:
                    last_percent = percent
                    print(
                        f"\rRepairing: {percent:3d}% "
                        f"({format_bytes(copied)} / {format_bytes(total)})",
                        end="",
                        flush=True,
                    )
            elif kind == "done":
                print(f"\rRepairing: 100% ({output_path})")
                return

    reader = threading.Thread(target=progress_reader, daemon=True)
    reader.start()

    try:
        repair_iso(input_path, output_path, progress_queue=progress_queue)
    except Exception as exc:
        print(f"\nRepair failed: {exc}", file=sys.stderr)
        return 1

    reader.join(timeout=1)
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} - Python edition")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {APP_VERSION}")
    parser.add_argument("input", nargs="?", help="Source Redump ISO/XISO")
    parser.add_argument("output", nargs="?", help="Destination repaired ISO")
    parser.add_argument("-f", "--force", action="store_true", help="Replace output if it exists")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.input or args.output:
        if not args.input or not args.output:
            print("Both input and output paths are required for command-line repair.", file=sys.stderr)
            return 2
        return run_cli(args)

    app = RepairApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
