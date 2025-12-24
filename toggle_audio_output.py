"""
Toggle the default Windows audio output device between two named devices.

Targets (customize if needed):
  - Speakers (USB Audio Device)
  - Headphones (Arctis 7 Game)

This script does NOT click through Settings UI; it uses Windows Core Audio APIs
to set the default render endpoint for Console/Multimedia/Communications roles.
"""

from __future__ import annotations

import argparse
import platform
import sys
from dataclasses import dataclass


SPEAKERS_NAME = "Speakers (USB Audio Device)"
HEADPHONES_NAME = "Headphones (Arctis 7 Game)"


def _require_windows() -> None:
    if sys.platform != "win32":
        raise SystemExit(
            "This script only works on Windows (Core Audio APIs). "
            f"Detected: {platform.platform()} ({sys.platform})."
        )


@dataclass(frozen=True)
class AudioDevice:
    id: str
    name: str


def _iter_devices() -> list[AudioDevice]:
    # Lazy import so non-Windows users get a clean error message.
    from pycaw.pycaw import AudioUtilities

    devices = []
    for d in AudioUtilities.GetAllDevices():
        # pycaw returns an object with fields like .id and .FriendlyName
        dev_id = getattr(d, "id", None)
        dev_name = getattr(d, "FriendlyName", None)
        if dev_id and dev_name:
            devices.append(AudioDevice(id=str(dev_id), name=str(dev_name)))
    return devices


def _find_device_id_by_name(devices: list[AudioDevice], target_name: str) -> str | None:
    target = target_name.strip().casefold()

    # Prefer exact match.
    for d in devices:
        if d.name.strip().casefold() == target:
            return d.id

    # Fallback: substring match (helps if Windows prefixes/suffixes the name).
    for d in devices:
        if target in d.name.casefold():
            return d.id

    return None


def _get_default_render_device_id() -> str:
    from pycaw.pycaw import AudioUtilities

    dev = AudioUtilities.GetSpeakers()  # default render endpoint (IMMDevice)
    return str(dev.GetId())


def _set_default_device(device_id: str) -> None:
    # Core Audio "PolicyConfig" interface to set the default endpoint.
    # This is a well-known, undocumented interface used by many utilities.
    import comtypes
    from comtypes import CLSCTX_ALL, COMMETHOD, GUID, HRESULT, IUnknown
    from ctypes import POINTER, c_void_p
    from ctypes import wintypes

    class IPolicyConfig(IUnknown):
        _iid_ = GUID("{F8679F50-850A-41CF-9C72-430F290290C8}")
        _methods_ = [
            COMMETHOD(
                [],
                HRESULT,
                "GetMixFormat",
                (["in"], wintypes.LPCWSTR, "pwstrDeviceId"),
                (["out"], POINTER(c_void_p), "ppFormat"),
            ),
            COMMETHOD(
                [],
                HRESULT,
                "GetDeviceFormat",
                (["in"], wintypes.LPCWSTR, "pwstrDeviceId"),
                (["in"], wintypes.BOOL, "bDefault"),
                (["out"], POINTER(c_void_p), "ppFormat"),
            ),
            COMMETHOD([], HRESULT, "ResetDeviceFormat", (["in"], wintypes.LPCWSTR, "pwstrDeviceId")),
            COMMETHOD(
                [],
                HRESULT,
                "SetDeviceFormat",
                (["in"], wintypes.LPCWSTR, "pwstrDeviceId"),
                (["in"], c_void_p, "pEndpointFormat"),
                (["in"], c_void_p, "pMixFormat"),
            ),
            COMMETHOD(
                [],
                HRESULT,
                "GetProcessingPeriod",
                (["in"], wintypes.LPCWSTR, "pwstrDeviceId"),
                (["in"], wintypes.BOOL, "bDefault"),
                (["out"], POINTER(c_void_p), "ppDefaultPeriod"),
                (["out"], POINTER(c_void_p), "ppMinimumPeriod"),
            ),
            COMMETHOD(
                [],
                HRESULT,
                "SetProcessingPeriod",
                (["in"], wintypes.LPCWSTR, "pwstrDeviceId"),
                (["in"], c_void_p, "pDefaultPeriod"),
                (["in"], c_void_p, "pMinimumPeriod"),
            ),
            COMMETHOD(
                [],
                HRESULT,
                "GetShareMode",
                (["in"], wintypes.LPCWSTR, "pwstrDeviceId"),
                (["out"], POINTER(wintypes.DWORD), "pMode"),
            ),
            COMMETHOD(
                [],
                HRESULT,
                "SetShareMode",
                (["in"], wintypes.LPCWSTR, "pwstrDeviceId"),
                (["in"], wintypes.DWORD, "mode"),
            ),
            COMMETHOD(
                [],
                HRESULT,
                "GetPropertyValue",
                (["in"], wintypes.LPCWSTR, "pwstrDeviceId"),
                (["in"], c_void_p, "key"),
                (["out"], POINTER(c_void_p), "pv"),
            ),
            COMMETHOD(
                [],
                HRESULT,
                "SetPropertyValue",
                (["in"], wintypes.LPCWSTR, "pwstrDeviceId"),
                (["in"], c_void_p, "key"),
                (["in"], c_void_p, "pv"),
            ),
            COMMETHOD(
                [],
                HRESULT,
                "SetDefaultEndpoint",
                (["in"], wintypes.LPCWSTR, "pwstrDeviceId"),
                (["in"], wintypes.DWORD, "role"),
            ),
            COMMETHOD(
                [],
                HRESULT,
                "SetEndpointVisibility",
                (["in"], wintypes.LPCWSTR, "pwstrDeviceId"),
                (["in"], wintypes.BOOL, "bVisible"),
            ),
        ]

    CLSID_PolicyConfigClient = GUID("{870AF99C-171D-4F9E-AF0D-E63DF40C2BC9}")
    policy = comtypes.CoCreateInstance(
        CLSID_PolicyConfigClient, interface=IPolicyConfig, clsctx=CLSCTX_ALL
    )

    # 0=eConsole, 1=eMultimedia, 2=eCommunications
    for role in (0, 1, 2):
        policy.SetDefaultEndpoint(device_id, role)


def _cmd_list() -> int:
    devices = _iter_devices()
    default_id = _get_default_render_device_id()
    print("Audio devices (known to pycaw):")
    for d in devices:
        marker = " *" if d.id == default_id else "  "
        print(f"{marker} {d.name}\n     id={d.id}")
    return 0


def _cmd_set(target_name: str) -> int:
    devices = _iter_devices()
    target_id = _find_device_id_by_name(devices, target_name)
    if not target_id:
        print(f'Could not find a device matching "{target_name}".', file=sys.stderr)
        print("Run with --list to see exact device names.", file=sys.stderr)
        return 2
    _set_default_device(target_id)
    print(f'Set default output device to: "{target_name}"')
    return 0


def _cmd_toggle() -> int:
    devices = _iter_devices()
    speakers_id = _find_device_id_by_name(devices, SPEAKERS_NAME)
    headphones_id = _find_device_id_by_name(devices, HEADPHONES_NAME)

    missing = []
    if not speakers_id:
        missing.append(SPEAKERS_NAME)
    if not headphones_id:
        missing.append(HEADPHONES_NAME)
    if missing:
        print("Could not find one or more target devices:", file=sys.stderr)
        for m in missing:
            print(f' - "{m}"', file=sys.stderr)
        print("Run with --list to see exact device names.", file=sys.stderr)
        return 2

    current_id = _get_default_render_device_id()
    next_id = headphones_id if current_id == speakers_id else speakers_id
    next_name = HEADPHONES_NAME if next_id == headphones_id else SPEAKERS_NAME

    _set_default_device(next_id)
    print(f'Toggled default output device to: "{next_name}"')
    return 0


def main(argv: list[str] | None = None) -> int:
    _require_windows()

    p = argparse.ArgumentParser(
        description="Toggle/set the default Windows 11 audio output device."
    )
    g = p.add_mutually_exclusive_group()
    g.add_argument("--list", action="store_true", help="List audio devices and default")
    g.add_argument(
        "--toggle",
        action="store_true",
        help=f'Toggle between "{SPEAKERS_NAME}" and "{HEADPHONES_NAME}" (default)',
    )
    g.add_argument("--set", metavar="NAME", help="Set default output to matching NAME")
    g.add_argument(
        "--speakers",
        action="store_true",
        help=f'Set default output to "{SPEAKERS_NAME}"',
    )
    g.add_argument(
        "--headphones",
        action="store_true",
        help=f'Set default output to "{HEADPHONES_NAME}"',
    )

    args = p.parse_args(argv)

    if args.list:
        return _cmd_list()
    if args.set:
        return _cmd_set(args.set)
    if args.speakers:
        return _cmd_set(SPEAKERS_NAME)
    if args.headphones:
        return _cmd_set(HEADPHONES_NAME)

    # Default action
    return _cmd_toggle()


if __name__ == "__main__":
    raise SystemExit(main())
