# Changelog

All notable changes to **LoginVRCast** will be documented in this file.

## [0.1.0] - 2025-08-20
### Added
- Hebrew (RTL) UI with buttons: **שידור**, **חיבור אלחוטי** / **נתק אלחוטי**, **עצור**.
- One‑click Wi‑Fi connect: switches to `tcpip 5555`, auto‑detects headset IP, and runs `adb connect`.
- Auto‑prefer Wi‑Fi when available; falls back to USB.
- Renderer selector (OpenGL / Direct3D).
- Exact 1600×904 client crop with borderless window and no scaling.
- Status indicator with clear messages (device/unauthorized/offline).

### Fixed
- Robust Wi‑Fi IP detection across multiple wlan interfaces and route fallback.

