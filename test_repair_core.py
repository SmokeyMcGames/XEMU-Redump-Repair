from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import xemu_redump_repair as app


class RepairCoreTests(unittest.TestCase):
    def _write_magic_at(self, path: Path, offset: int) -> None:
        with path.open("wb") as target:
            target.seek(offset)
            target.write(app.XDVDFS_MAGIC)
            target.write(b"data")

    def test_default_output_path_tracks_source_iso(self) -> None:
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "Halo.iso"

            self.assertEqual(
                app.default_output_path(source),
                Path(temp_dir) / "[Fixed]Halo.iso",
            )

    def test_find_iso_files_scans_folders_recursively(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "nested"
            nested.mkdir()
            first = root / "A.iso"
            second = nested / "B.ISO"
            ignored = nested / "notes.txt"

            first.write_bytes(b"one")
            second.write_bytes(b"two")
            ignored.write_text("nope")

            self.assertEqual(app.find_iso_files(root), [first, second])

    def test_output_path_for_batch_uses_fixed_name_in_output_folder(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "Halo.iso"
            output_folder = root / "fixed"

            self.assertEqual(
                app.output_path_for_job(source, output_folder, batch_mode=True),
                output_folder / "[Fixed]Halo.iso",
            )

    def test_default_batch_output_folder_uses_common_parent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "games"
            nested.mkdir()

            self.assertEqual(
                app.default_batch_output_folder(
                    [nested / "A.iso", nested / "B.iso"],
                ),
                nested,
            )

    def test_repair_skips_configured_bytes(self) -> None:
        old_skip_bytes = app.SKIP_BYTES
        old_chunk_size = app.CHUNK_SIZE

        try:
            app.SKIP_BYTES = 4
            app.CHUNK_SIZE = 3

            with TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / "input.iso"
                destination = Path(temp_dir) / "output.iso"

                source.write_bytes(b"skiprepaired-data")

                app.repair_iso(source, destination)

                self.assertEqual(destination.read_bytes(), b"repaired-data")
        finally:
            app.SKIP_BYTES = old_skip_bytes
            app.CHUNK_SIZE = old_chunk_size

    def test_inspect_iso_detects_already_repaired_xiso(self) -> None:
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "game.iso"
            self._write_magic_at(source, app.XDVDFS_DESCRIPTOR_OFFSET)

            inspection = app.inspect_iso(source)

            self.assertEqual(inspection.status, app.ISO_ALREADY_XISO)
            self.assertFalse(inspection.needs_repair)

    def test_inspect_iso_detects_redump_layout(self) -> None:
        old_skip_bytes = app.SKIP_BYTES

        try:
            app.SKIP_BYTES = 4

            with TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / "game.iso"
                self._write_magic_at(source, app.SKIP_BYTES + app.XDVDFS_DESCRIPTOR_OFFSET)

                inspection = app.inspect_iso(source)

                self.assertEqual(inspection.status, app.ISO_REDUMP)
                self.assertTrue(inspection.needs_repair)
        finally:
            app.SKIP_BYTES = old_skip_bytes

    def test_inspect_iso_reports_unknown_layout(self) -> None:
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "game.iso"
            source.write_bytes(b"not an xbox iso")

            inspection = app.inspect_iso(source)

            self.assertEqual(inspection.status, app.ISO_UNKNOWN)
            self.assertFalse(inspection.needs_repair)


if __name__ == "__main__":
    unittest.main()
