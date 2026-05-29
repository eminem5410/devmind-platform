"""Platform detection utility for cross-platform support."""

import platform
import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformInfo:
    """Detected platform information."""
    system: str          # "Linux", "Windows", "Darwin"
    os_name: str         # "Ubuntu", "Windows 10", "macOS"
    os_version: str
    arch: str            # "x86_64", "AMD64", "arm64"
    is_linux: bool
    is_windows: bool
    is_macos: bool
    is_wsl: bool         # Windows Subsystem for Linux
    package_manager: str # "apt", "dnf", "pacman", "choco", "winget", "brew", ""
    shell: str           # "bash", "zsh", "powershell", "cmd"

    @property
    def display(self) -> str:
        wsl_tag = " (WSL)" if self.is_wsl else ""
        return f"{self.os_name}{wsl_tag} {self.arch}"


def detect_platform() -> PlatformInfo:
    """Detect current platform information."""
    system = platform.system()
    release = platform.release()
    machine = platform.machine().replace("AMD64", "x86_64")
    is_linux = system == "Linux"
    is_windows = system == "Windows"
    is_macos = system == "Darwin"

    os_name = system
    os_version = release
    pkg_mgr = ""
    shell = ""

    if is_linux:
        # Detect distro
        os_name, os_version = _detect_linux_distro()
        pkg_mgr = _detect_package_manager()
        shell = _detect_shell()
        # Detect WSL
        is_wsl = _detect_wsl()
    elif is_windows:
        os_name = "Windows"
        os_version = platform.version()
        pkg_mgr = _detect_windows_pkg_manager()
        shell = "powershell" if shutil.which("pwsh") or shutil.which("powershell") else "cmd"
    elif is_macos:
        os_name = "macOS"
        os_version = platform.mac_ver()[0]
        pkg_mgr = "brew" if shutil.which("brew") else ""

    return PlatformInfo(
        system=system,
        os_name=os_name,
        os_version=os_version,
        arch=machine,
        is_linux=is_linux,
        is_windows=is_windows,
        is_macos=is_macos,
        is_wsl=is_wsl if is_linux else False,
        package_manager=pkg_mgr,
        shell=shell,
    )


def _detect_linux_distro() -> tuple[str, str]:
    """Detect Linux distribution name and version."""
    import subprocess
    try:
        result = subprocess.run(
            ["lsb_release", "-si"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            name = result.stdout.strip()
            ver_result = subprocess.run(
                ["lsb_release", "-sr"], capture_output=True, text=True, timeout=5
            )
            version = ver_result.stdout.strip() if ver_result.returncode == 0 else ""
            return name, version
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Fallback: /etc/os-release
    try:
        with open("/etc/os-release") as f:
            info = {}
            for line in f:
                if "=" in line:
                    key, val = line.split("=", 1)
                    info[key.strip()] = val.strip().strip('"')
            return info.get("NAME", "Linux"), info.get("VERSION", "")
    except (FileNotFoundError, PermissionError):
        pass
    return "Linux", ""


def _detect_package_manager() -> str:
    """Detect Linux package manager."""
    managers = [
        ("apt", "apt-get"),
        ("dnf", "dnf"),
        ("pacman", "pacman"),
        ("zypper", "zypper"),
    ]
    for name, cmd in managers:
        if shutil.which(cmd):
            return name
    return ""


def _detect_shell() -> str:
    """Detect current shell on Linux."""
    import os
    shell_path = os.environ.get("SHELL", "")
    if "zsh" in shell_path:
        return "zsh"
    if "bash" in shell_path:
        return "bash"
    if "fish" in shell_path:
        return "fish"
    return shell_path.split("/")[-1] if shell_path else ""


def _detect_wsl() -> bool:
    """Detect if running under Windows Subsystem for Linux."""
    import os
    wsl_markers = ["microsoft", "microsoft-standard"]
    try:
        with open("/proc/version") as f:
            content = f.read().lower()
            return any(marker in content for marker in wsl_markers)
    except (FileNotFoundError, PermissionError):
        # Check env vars
        wsl_env = os.environ.get("WSL_DISTRO_NAME", "")
        return bool(wsl_env)


def _detect_windows_pkg_manager() -> str:
    """Detect Windows package manager."""
    if shutil.which("winget"):
        return "winget"
    if shutil.which("choco"):
        return "choco"
    if shutil.which("scoop"):
        return "scoop"
    return ""
