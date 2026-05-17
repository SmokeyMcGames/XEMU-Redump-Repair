# Changelog

## 2.0.0

- Rebuilt the app as a Python Edition.
- Removed the runtime dependency on DD for Windows.
- Added single ISO, multi-ISO, and folder-based repair flows.
- Added XISO/Redump layout detection before repair.
- Added progress reporting and cancellation cleanup.
- Added command-line repair support.
- Added automated tests and a Windows executable build workflow.

## 1.0.1

- Fixed the early `dd.exe` PID check that could show a failure message while `dd.exe` was still working.
