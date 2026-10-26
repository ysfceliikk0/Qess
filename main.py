import gc
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from watchdog.events import FileMovedEvent, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from PyQt6.QtCore import (
    QEasingCurve,
    QMimeData,
    QObject,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTimer,
    QUrl,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAction,
    QBrush,
    QCloseEvent,
    QColor,
    QCursor,
    QDrag,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QFont,
    QFontMetrics,
    QIcon,
    QImageReader,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QResizeEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

CONFIG_PATH = Path(__file__).parent / "config.json"
APP_REGISTRY_NAME = "UniversalFileDropCatcher"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}

DIRECTION_ITEMS = [
    ("Üst Kenar (Sıfır Boşluk / Ortalanmış)", "top"),
    ("Sağ Kenar (Ortalanmış)", "right"),
    ("Sol Kenar (Ortalanmış)", "left"),
    ("Alt Kenar (Ortalanmış)", "bottom"),
]

# ---------------------------------------------------------------------------
# 1. Dinamik Tema ve Gradient Tanımları (Gradient & Solid)
# ---------------------------------------------------------------------------
THEME_ITEMS = [
    ("🌊 Okyanus (Su Yeşili & Mavi Gradient - Varsayılan)", "ocean"),
    ("🌅 Gün Batımı (Turuncu, Pembe & Kırmızı Gradient)", "sunset"),
    ("🌌 Gece Yarısı (Koyu Mavi & Mor Gradient)", "midnight"),
    ("🌑 Koyu Mod (Tek Renk - Yarı Saydam Koyu Gri)", "dark_solid"),
    ("🏳️ Sade Beyaz (Tek Renk - Yarı Saydam Beyaz)", "light_solid"),
]

THEMES: Dict[str, Dict[str, Any]] = {
    "ocean": {
        "label": "Okyanus",
        "is_gradient": True,
        "bg_colors": [(8, 22, 31, 246), (11, 35, 46, 245), (13, 48, 54, 246)],
        "border_colors": ["#2DD4BF", "#38BDF8", "#34D399"],
        "bar_colors": [(45, 212, 191, 242), (14, 165, 233, 242)],
        "track_color": (45, 212, 191, 45),
        "accent_primary": "#2DD4BF",
        "accent_secondary": "#38BDF8",
        "text_primary": "#F8FAFC",
        "text_secondary": "#99F6E4",
        "card_bg": "rgba(16, 40, 54, 238)",
        "card_hover_bg": "rgba(21, 56, 74, 250)",
        "card_border": "rgba(45, 212, 191, 110)",
        "btn_base_bg": (16, 42, 56, 225),
        "btn_hover_bg": (24, 72, 92, 250),
        "btn_text": "#F8FAFC",
    },
    "sunset": {
        "label": "Gün Batımı",
        "is_gradient": True,
        "bg_colors": [(38, 12, 24, 246), (58, 16, 32, 245), (72, 24, 18, 246)],
        "border_colors": ["#FB923C", "#F43F5E", "#EC4899"],
        "bar_colors": [(251, 146, 60, 242), (244, 63, 94, 242)],
        "track_color": (251, 146, 60, 48),
        "accent_primary": "#FB923C",
        "accent_secondary": "#F43F5E",
        "text_primary": "#FFF1F2",
        "text_secondary": "#FDBA74",
        "card_bg": "rgba(62, 18, 34, 238)",
        "card_hover_bg": "rgba(84, 24, 46, 250)",
        "card_border": "rgba(251, 146, 60, 115)",
        "btn_base_bg": (62, 18, 34, 225),
        "btn_hover_bg": (92, 28, 50, 250),
        "btn_text": "#FFF1F2",
    },
    "midnight": {
        "label": "Gece Yarısı",
        "is_gradient": True,
        "bg_colors": [(12, 14, 36, 246), (22, 18, 52, 245), (38, 16, 62, 246)],
        "border_colors": ["#6366F1", "#A855F7", "#EC4899"],
        "bar_colors": [(99, 102, 241, 242), (168, 85, 247, 242)],
        "track_color": (168, 85, 247, 48),
        "accent_primary": "#A855F7",
        "accent_secondary": "#818CF8",
        "text_primary": "#F5F3FF",
        "text_secondary": "#C4B5FD",
        "card_bg": "rgba(26, 20, 58, 238)",
        "card_hover_bg": "rgba(38, 28, 82, 250)",
        "card_border": "rgba(168, 85, 247, 115)",
        "btn_base_bg": (28, 22, 62, 225),
        "btn_hover_bg": (46, 34, 96, 250),
        "btn_text": "#F5F3FF",
    },
    "dark_solid": {
        "label": "Koyu Mod",
        "is_gradient": False,
        "bg_solid": (24, 26, 32, 242),
        "border_solid": "#94A3B8",
        "bar_solid": (100, 116, 139, 240),
        "track_color": (148, 163, 184, 45),
        "accent_primary": "#94A3B8",
        "accent_secondary": "#E2E8F0",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "card_bg": "rgba(38, 41, 50, 238)",
        "card_hover_bg": "rgba(52, 56, 68, 250)",
        "card_border": "rgba(148, 163, 184, 105)",
        "btn_base_bg": (38, 42, 52, 225),
        "btn_hover_bg": (58, 64, 78, 250),
        "btn_text": "#F8FAFC",
    },
    "light_solid": {
        "label": "Sade Beyaz",
        "is_gradient": False,
        "bg_solid": (248, 250, 252, 244),
        "border_solid": "#0284C7",
        "bar_solid": (2, 132, 199, 238),
        "track_color": (2, 132, 199, 45),
        "accent_primary": "#0284C7",
        "accent_secondary": "#0369A1",
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "card_bg": "rgba(255, 255, 255, 238)",
        "card_hover_bg": "rgba(226, 232, 240, 252)",
        "card_border": "rgba(2, 132, 199, 110)",
        "btn_base_bg": (226, 232, 240, 238),
        "btn_hover_bg": (203, 213, 225, 252),
        "btn_text": "#0F172A",
    },
}


def get_theme_spec(theme_key: str) -> Dict[str, Any]:
    return THEMES.get(theme_key, THEMES["ocean"])


def build_theme_bg_brush(rect: QRectF, theme_key: str) -> QBrush:
    spec = get_theme_spec(theme_key)
    if spec["is_gradient"]:
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        c0, c1, c2 = spec["bg_colors"]
        grad.setColorAt(0.0, QColor(*c0))
        grad.setColorAt(0.55, QColor(*c1))
        grad.setColorAt(1.0, QColor(*c2))
        return QBrush(grad)
    return QBrush(QColor(*spec["bg_solid"]))


def build_theme_border_brush(rect: QRectF, theme_key: str) -> QBrush:
    spec = get_theme_spec(theme_key)
    if spec["is_gradient"]:
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        b0, b1, b2 = spec["border_colors"]
        grad.setColorAt(0.0, QColor(b0))
        grad.setColorAt(0.5, QColor(b1))
        grad.setColorAt(1.0, QColor(b2))
        return QBrush(grad)
    return QBrush(QColor(spec["border_solid"]))


def build_theme_bar_brush(rect: QRectF, theme_key: str) -> QBrush:
    spec = get_theme_spec(theme_key)
    if spec["is_gradient"]:
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        c0, c1 = spec["bar_colors"]
        grad.setColorAt(0.0, QColor(*c0))
        grad.setColorAt(1.0, QColor(*c1))
        return QBrush(grad)
    return QBrush(QColor(*spec["bar_solid"]))


# ---------------------------------------------------------------------------
# 2. Yapılandırma (config.json - Varsayılan Üst Yön) & Auto-Start Yönetimi
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "popup_duration_seconds": 10,
    "popup_direction": "top",
    "tray_direction": "top",
    "theme": "ocean",
    "run_on_startup": False,
    "ignore_extensions": [
        ".crdownload",
        ".part",
        ".tmp",
        ".partial",
        ".opdownload",
        ".download",
    ],
    "watch_paths": [
        "~/Downloads",
        "~/İndirilenler",
        "~/Quick Share",
        "~/Phone Link",
        "~/Windows Bağlantısı",
        "~/CrossDevice",
    ],
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        for k, v in DEFAULT_CONFIG.items():
            data.setdefault(k, v)
        return data
    except Exception as exc:
        print(f"[Config] Okuma hatası, varsayılan ayarlar yüklendi: {exc}")
        return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        print(f"[Config] Kaydetme hatası: {exc}")


def _build_startup_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    exe_path = Path(sys.executable)
    pythonw = exe_path.with_name("pythonw.exe")
    runner = str(pythonw if pythonw.exists() else exe_path)
    script_path = os.path.abspath(__file__)
    return f'"{runner}" "{script_path}"'


def set_autostart_enabled(enabled: bool) -> bool:
    """
    İşletim sistemine göre başlangıçta otomatik çalışmayı ayarlar:
    - Windows: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run (winreg)
    - Linux: ~/.config/autostart/filecatcher.desktop
    """
    os_name = platform.system()
    cmd_str = _build_startup_command()

    if os_name == "Windows":
        try:
            import winreg

            run_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                run_key_path,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                if enabled:
                    winreg.SetValueEx(
                        key, APP_REGISTRY_NAME, 0, winreg.REG_SZ, cmd_str
                    )
                else:
                    try:
                        winreg.DeleteValue(key, APP_REGISTRY_NAME)
                    except FileNotFoundError:
                        pass
            return True
        except Exception as exc:
            print(f"[AutoStart] Windows kayıt defteri hatası: {exc}")
            return False

    if os_name == "Linux":
        try:
            autostart_dir = Path.home() / ".config" / "autostart"
            desktop_file = autostart_dir / "filecatcher.desktop"
            if enabled:
                autostart_dir.mkdir(parents=True, exist_ok=True)
                content = (
                    "[Desktop Entry]\n"
                    "Type=Application\n"
                    "Name=Universal File Drop Catcher\n"
                    "Comment=Universal File Drop Catcher Background Service\n"
                    f"Exec={cmd_str}\n"
                    "Terminal=false\n"
                    "X-GNOME-Autostart-enabled=true\n"
                )
                desktop_file.write_text(content, encoding="utf-8")
            else:
                if desktop_file.exists():
                    desktop_file.unlink()
            return True
        except Exception as exc:
            print(f"[AutoStart] Linux autostart hatası: {exc}")
            return False

    return False


# ---------------------------------------------------------------------------
# 3. Kaynak Tespiti, Panoya Kopyalama ve Yerel Paylaşım Menüsü (Native Share API)
# ---------------------------------------------------------------------------
def detect_source_from_path(file_path: str) -> Tuple[str, str, str]:
    normalized = file_path.replace("\\", "/").lower()
    if "quick share" in normalized or "quickshare" in normalized:
        return ("Quick Share", "⚡", "#38BDF8")
    if (
        "phone link" in normalized
        or "windows bağlantısı" in normalized
        or "windows baglantisi" in normalized
        or "crossdevice" in normalized
    ):
        return ("Phone Link", "📱", "#2DD4BF")
    return ("Chrome / İndirilenler", "🌐", "#34D399")


def open_with_default_app(file_path: str):
    try:
        os_name = platform.system()
        if os_name == "Windows":
            os.startfile(file_path)  # type: ignore[attr-defined]
        elif os_name == "Darwin":
            subprocess.Popen(["open", file_path])
        else:
            subprocess.Popen(
                ["xdg-open", file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception as exc:
        print(f"[OS] Dosya açılamadı: {exc}")


def copy_file_to_clipboard(file_path: str):
    abs_path = os.path.abspath(file_path)
    clipboard = QApplication.clipboard()
    if clipboard is None:
        return
    mime = QMimeData()
    file_url = QUrl.fromLocalFile(abs_path)
    mime.setUrls([file_url])
    mime.setText(abs_path)
    if platform.system() == "Linux":
        encoded_uri = file_url.toEncoded().data().decode("utf-8")
        mime.setData(
            "x-special/gnome-copied-files", f"copy\n{encoded_uri}".encode("utf-8")
        )
    clipboard.setMimeData(mime)


def _trigger_windows_native_share(abs_path: str, hwnd: int) -> bool:
    try:
        import winsdk.windows.applicationmodel.datatransfer as w_dt  # type: ignore
        import winsdk.windows.storage as w_storage  # type: ignore

        dtm = w_dt.DataTransferManager.get_for_current_view()

        def _on_data_requested(sender, args):
            req = args.request
            deferral = req.get_deferral()
            req.data.properties.title = os.path.basename(abs_path)
            req.data.properties.description = abs_path
            op = w_storage.StorageFile.get_file_from_path_async(abs_path)

            def _on_file_ready(async_info, status):
                try:
                    storage_file = async_info.get_results()
                    req.data.set_storage_items([storage_file])
                except Exception:
                    req.data.set_text(abs_path)
                finally:
                    deferral.complete()

            op.completed = _on_file_ready

        dtm.add_data_requested(_on_data_requested)
        w_dt.DataTransferManager.show_share_ui()
        return True
    except Exception:
        pass

    escaped_path = abs_path.replace("'", "''")
    file_uri = QUrl.fromLocalFile(abs_path).toString().replace("'", "''")

    ps_script = f"""
$ErrorActionPreference = 'Stop'
$filePath = '{escaped_path}'
$fileUri = '{file_uri}'

try {{
    [Windows.ApplicationModel.DataTransfer.DataTransferManager, Windows.ApplicationModel.DataTransfer, ContentType = WindowsRuntime] | Out-Null
    [Windows.ApplicationModel.DataTransfer.DataRequestedEventArgs, Windows.ApplicationModel.DataTransfer, ContentType = WindowsRuntime] | Out-Null
    [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
    [Windows.Storage.IStorageItem, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
    [Windows.Foundation.TypedEventHandler`2, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null

    $runtimeDir = [System.Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()
    $winrtDll = Join-Path $runtimeDir 'System.Runtime.WindowsRuntime.dll'
    if (Test-Path $winrtDll) {{
        [System.Reflection.Assembly]::LoadFrom($winrtDll) | Out-Null
    }}

    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

[ComImport, Guid("3A3DCD6C-3EAB-43DC-BCDE-45671CE800C8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IDataTransferManagerInterop {{
    IntPtr GetForWindow(IntPtr appWindow, [In] ref Guid riid);
    void ShowShareUIForWindow(IntPtr appWindow);
}}

public static class ShareInterop {{
    [DllImport("combase.dll", PreserveSig = false)]
    private static extern void RoGetActivationFactory(
        [MarshalAs(UnmanagedType.HString)] string activatableClassId,
        [In] ref Guid iid,
        [Out, MarshalAs(UnmanagedType.Interface)] out IDataTransferManagerInterop factory
    );

    public static IDataTransferManagerInterop GetFactory() {{
        Guid iid = new Guid("3A3DCD6C-3EAB-43DC-BCDE-45671CE800C8");
        IDataTransferManagerInterop factory;
        RoGetActivationFactory("Windows.ApplicationModel.DataTransfer.DataTransferManager", ref iid, out factory);
        return factory;
    }}

    public static object GetManagerForWindow(IntPtr hwnd) {{
        var factory = GetFactory();
        Guid dtmIid = new Guid("A5CAEE9B-8708-49D1-8D36-67D25A8DA00C");
        IntPtr pUnk = factory.GetForWindow(hwnd, ref dtmIid);
        try {{
            return Marshal.GetObjectForIUnknown(pUnk);
        }} finally {{
            Marshal.Release(pUnk);
        }}
    }}

    public static void ShowForWindow(IntPtr hwnd) {{
        GetFactory().ShowShareUIForWindow(hwnd);
    }}
}}
"@

    $storageFile = $null
    try {{
        $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{
            $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
            $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
        }})[0]
        $asTask = $asTaskGeneric.MakeGenericMethod([Windows.Storage.StorageFile])
        $fileTask = $asTask.Invoke($null, @([Windows.Storage.StorageFile]::GetFileFromPathAsync($filePath)))
        $fileTask.Wait(1500) | Out-Null
        if ($fileTask.IsCompleted -and -not $fileTask.IsFaulted) {{
            $storageFile = $fileTask.Result
        }}
    }} catch {{
        $storageFile = $null
    }}

    Add-Type -AssemblyName System.Windows.Forms
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Paylaş"
    $form.Width = 1
    $form.Height = 1
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
    $form.ShowInTaskbar = $false
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $form.Opacity = 0.01
    $form.TopMost = $true

    $form.Add_Shown({{
        try {{
            $form.Activate()
            $dtm = [ShareInterop]::GetManagerForWindow($form.Handle)
            $handlerType = [Windows.Foundation.TypedEventHandler`2].MakeGenericType(
                [Windows.ApplicationModel.DataTransfer.DataTransferManager],
                [Windows.ApplicationModel.DataTransfer.DataRequestedEventArgs]
            )
            $del = ({{
                param($s, $e)
                $req = $e.Request
                $req.Data.Properties.Title = [System.IO.Path]::GetFileName($filePath)
                $req.Data.Properties.Description = $filePath
                if ($storageFile -ne $null) {{
                    $list = New-Object 'System.Collections.Generic.List[Windows.Storage.IStorageItem]'
                    $list.Add($storageFile)
                    $req.Data.SetStorageItems($list)
                }} else {{
                    $req.Data.SetText($filePath)
                    try {{ $req.Data.SetWebLink([Uri]::new($fileUri)) }} catch {{}}
                }}
            }}) -as $handlerType

            $addMethod = [Windows.ApplicationModel.DataTransfer.DataTransferManager].GetMethod("add_DataRequested")
            $addMethod.Invoke($dtm, @($del)) | Out-Null

            [ShareInterop]::ShowForWindow($form.Handle)
        }} catch {{
            Start-Process explorer.exe -ArgumentList "/select,`"$filePath`""
            $form.Close()
        }}
    }})

    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = 14000
    $timer.Add_Tick({{ $form.Close(); $timer.Stop() }})
    $timer.Start()
    [System.Windows.Forms.Application]::Run($form)
}} catch {{
    Start-Process explorer.exe -ArgumentList "/select,`"$filePath`""
}}
"""
    try:
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-STA",
                "-WindowStyle",
                "Hidden",
                "-Command",
                ps_script,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        return True
    except Exception as exc:
        print(f"[Share] PowerShell Native Share hatası: {exc}")
        return False


def _trigger_linux_native_share(abs_path: str) -> bool:
    file_uri = QUrl.fromLocalFile(abs_path).toString()

    for share_cmd in (
        ["nautilus-sendto", abs_path],
        ["kdeconnect-handler", file_uri],
        ["bluetooth-sendto", abs_path],
    ):
        if shutil.which(share_cmd[0]):
            try:
                subprocess.Popen(
                    share_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except Exception:
                pass

    if shutil.which("gdbus"):
        try:
            py_portal = (
                "import os, subprocess; "
                f"fd = os.open({abs_path!r}, os.O_RDONLY); "
                "subprocess.Popen(["
                "'gdbus', 'call', '--session', "
                "'--dest', 'org.freedesktop.portal.Desktop', "
                "'--object-path', '/org/freedesktop/portal/desktop', "
                "'--method', 'org.freedesktop.portal.OpenURI.OpenFile', "
                "'', '0', \"{'ask': <true>}\""
                "], pass_fds=(fd,))"
            )
            subprocess.Popen(
                [sys.executable, "-c", py_portal],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            pass

    if shutil.which("dbus-send"):
        try:
            subprocess.Popen(
                [
                    "dbus-send",
                    "--session",
                    "--print-reply",
                    "--dest=org.freedesktop.FileManager1",
                    "/org/freedesktop/FileManager1",
                    "org.freedesktop.FileManager1.ShowItems",
                    f"array:string:{file_uri}",
                    "string:",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            pass

    return False


def open_native_share_ui(file_path: str, parent_widget: Optional[QWidget] = None):
    abs_path = os.path.abspath(file_path)
    copy_file_to_clipboard(abs_path)

    os_name = platform.system()
    hwnd = int(parent_widget.winId()) if parent_widget is not None else 0

    if os_name == "Windows":
        if _trigger_windows_native_share(abs_path, hwnd):
            return
        try:
            subprocess.Popen(["explorer.exe", f'/select,"{abs_path}"'])
        except Exception as exc:
            print(f"[OS] Windows yedek paylaşım hatası: {exc}")

    elif os_name == "Linux":
        if _trigger_linux_native_share(abs_path):
            return
        try:
            subprocess.Popen(
                ["xdg-open", str(Path(abs_path).parent)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            print(f"[OS] Linux yedek paylaşım hatası: {exc}")

    elif os_name == "Darwin":
        try:
            subprocess.Popen(["open", "-R", abs_path])
        except Exception as exc:
            print(f"[OS] macOS paylaşım hatası: {exc}")


# ---------------------------------------------------------------------------
# 4. Yardımcı Görsel & Sürükle-Bırak Fonksiyonları
# ---------------------------------------------------------------------------
def create_low_ram_thumbnail(
    file_path: str, size: int, radius: int = 20, theme_key: str = "ocean"
) -> QPixmap:
    spec = get_theme_spec(theme_key)
    ext = Path(file_path).suffix.lower()
    canvas = QPixmap(size, size)
    canvas.fill(Qt.GlobalColor.transparent)

    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if ext in IMAGE_EXTENSIONS and os.path.exists(file_path):
        reader = QImageReader(file_path)
        reader.setAutoTransform(True)
        orig_size = reader.size()
        if orig_size.isValid():
            target_size = orig_size.scaled(
                QSize(size, size),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            )
            reader.setScaledSize(target_size)
        img = reader.read()
        if not img.isNull():
            cx = max(0, (img.width() - size) // 2)
            cy = max(0, (img.height() - size) // 2)
            cropped = img.copy(cx, cy, size, size)

            clip = QPainterPath()
            clip.addRoundedRect(2, 2, size - 4, size - 4, radius, radius)
            painter.setClipPath(clip)
            painter.drawImage(0, 0, cropped)
            painter.setClipping(False)

            border_c = QColor(spec["accent_primary"])
            border_c.setAlpha(175)
            painter.setPen(QPen(border_c, 1.5, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(2, 2, size - 4, size - 4, radius, radius)
            painter.end()
            return canvas

    rect_f = QRectF(3.0, 3.0, size - 6.0, size - 6.0)
    painter.setBrush(build_theme_bar_brush(rect_f, theme_key))
    painter.setPen(QPen(QColor(spec["accent_primary"]), 1.5, Qt.PenStyle.SolidLine))
    painter.drawRoundedRect(rect_f, radius, radius)

    painter.setPen(QPen(QColor("#FFFFFF")))
    font_pt = max(8, size // 7)
    painter.setFont(QFont("Sans Serif", font_pt, QFont.Weight.Bold))
    badge_txt = (ext[1:].upper() if ext else "FILE")[:5]
    painter.drawText(canvas.rect(), Qt.AlignmentFlag.AlignCenter, badge_txt)
    painter.end()
    return canvas


def execute_os_file_drag(
    source_widget: QWidget, file_path: str, pixmap: QPixmap
) -> Qt.DropAction:
    drag = QDrag(source_widget)
    mime = QMimeData()

    file_url = QUrl.fromLocalFile(file_path)
    mime.setUrls([file_url])

    if platform.system() == "Linux":
        encoded_uri = file_url.toEncoded().data().decode("utf-8")
        gnome_payload = f"copy\n{encoded_uri}".encode("utf-8")
        mime.setData("x-special/gnome-copied-files", gnome_payload)

    drag.setMimeData(mime)

    drag_icon = pixmap.scaled(
        56,
        56,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    drag.setPixmap(drag_icon)
    drag.setHotSpot(QPoint(drag_icon.width() // 2, drag_icon.height() // 2))

    return drag.exec(
        Qt.DropAction.CopyAction | Qt.DropAction.MoveAction,
        Qt.DropAction.CopyAction,
    )


def build_clockwise_perimeter_path(rect: QRectF, radius: float) -> QPainterPath:
    r_clamped = min(radius, rect.width() / 2.0, rect.height() / 2.0)
    l, t, r, b = rect.left(), rect.top(), rect.right(), rect.bottom()
    cx = rect.center().x()
    d = r_clamped * 2.0

    path = QPainterPath()
    path.moveTo(cx, t)
    path.lineTo(r - r_clamped, t)
    path.arcTo(QRectF(r - d, t, d, d), 90.0, -90.0)
    path.lineTo(r, b - r_clamped)
    path.arcTo(QRectF(r - d, b - d, d, d), 0.0, -90.0)
    path.lineTo(l + r_clamped, b)
    path.arcTo(QRectF(l, b - d, d, d), -90.0, -90.0)
    path.lineTo(l, t + r_clamped)
    path.arcTo(QRectF(l, t, d, d), 180.0, -90.0)
    path.lineTo(cx, t)
    return path


# ---------------------------------------------------------------------------
# 5. Dinamik Hover (Morfing) Aksiyon Butonu (minimumWidth & maximumWidth + OutBack)
# ---------------------------------------------------------------------------
class MorphingActionButton(QPushButton):
    expansion_changed = pyqtSignal(int)

    COLLAPSED_WIDTH = 42
    FIXED_HEIGHT = 36

    def __init__(
        self,
        icon_text: str,
        label_text: str,
        accent_hex: str = "#2DD4BF",
        theme_key: str = "ocean",
        expand_on_hover: bool = True,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(icon_text, parent)
        self._icon_text = icon_text
        self._label_text = label_text
        self._expand_on_hover = expand_on_hover
        self._expand_progress: float = 0.0
        self._scale_factor: float = 1.0

        self._accent_color = QColor(accent_hex)
        self._base_bg = QColor(16, 42, 56, 225)
        self._hover_bg = QColor(24, 72, 92, 250)
        self._text_color = QColor("#F8FAFC")

        self._icon_font = QFont("Segoe UI Emoji", 11)
        self._label_font = QFont("Segoe UI", 9, QFont.Weight.Bold)

        fm = QFontMetrics(self._label_font)
        text_px = fm.horizontalAdvance(self._label_text) if self._label_text else 0
        self._expanded_width = (
            self.COLLAPSED_WIDTH + text_px + 20
            if (self._expand_on_hover and self._label_text)
            else self.COLLAPSED_WIDTH
        )

        self.setToolTip(label_text)
        self.setFixedHeight(self.FIXED_HEIGHT)
        self.setMinimumWidth(self.COLLAPSED_WIDTH)
        self.setMaximumWidth(self.COLLAPSED_WIDTH)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._morph_group = QParallelAnimationGroup(self)

        self._min_w_anim = QPropertyAnimation(self, b"minimumWidth", self)
        self._min_w_anim.setDuration(340)
        out_back_1 = QEasingCurve(QEasingCurve.Type.OutBack)
        out_back_1.setOvershoot(1.12)
        self._min_w_anim.setEasingCurve(out_back_1)

        self._max_w_anim = QPropertyAnimation(self, b"maximumWidth", self)
        self._max_w_anim.setDuration(340)
        out_back_2 = QEasingCurve(QEasingCurve.Type.OutBack)
        out_back_2.setOvershoot(1.12)
        self._max_w_anim.setEasingCurve(out_back_2)

        self._prog_anim = QPropertyAnimation(self, b"expandProgress", self)
        self._prog_anim.setDuration(240)
        self._prog_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._morph_group.addAnimation(self._min_w_anim)
        self._morph_group.addAnimation(self._max_w_anim)
        self._morph_group.addAnimation(self._prog_anim)

        self._scale_anim = QPropertyAnimation(self, b"scaleFactor", self)
        self._scale_anim.setDuration(220)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        self.apply_theme(theme_key)

    def apply_theme(self, theme_key: str):
        spec = get_theme_spec(theme_key)
        self._base_bg = QColor(*spec["btn_base_bg"])
        self._hover_bg = QColor(*spec["btn_hover_bg"])
        self._text_color = QColor(spec["btn_text"])
        self.update()

    @pyqtProperty(float)
    def expandProgress(self) -> float:
        return self._expand_progress

    @expandProgress.setter
    def expandProgress(self, val: float):
        self._expand_progress = max(0.0, min(1.0, val))
        self.update()

    @pyqtProperty(float)
    def scaleFactor(self) -> float:
        return self._scale_factor

    @scaleFactor.setter
    def scaleFactor(self, val: float):
        self._scale_factor = val
        self.update()

    def enterEvent(self, event):
        self._morph_group.stop()
        self._min_w_anim.setStartValue(self.width())
        self._min_w_anim.setEndValue(self._expanded_width)
        self._max_w_anim.setStartValue(self.width())
        self._max_w_anim.setEndValue(self._expanded_width)
        self._prog_anim.setStartValue(self._expand_progress)
        self._prog_anim.setEndValue(1.0)
        self._morph_group.start()

        if self._expand_on_hover and self._expanded_width > self.COLLAPSED_WIDTH:
            self.expansion_changed.emit(self._expanded_width - self.COLLAPSED_WIDTH)

        super().enterEvent(event)

    def leaveEvent(self, event):
        self._morph_group.stop()
        self._min_w_anim.setStartValue(self.width())
        self._min_w_anim.setEndValue(self.COLLAPSED_WIDTH)
        self._max_w_anim.setStartValue(self.width())
        self._max_w_anim.setEndValue(self.COLLAPSED_WIDTH)
        self._prog_anim.setStartValue(self._expand_progress)
        self._prog_anim.setEndValue(0.0)
        self._morph_group.start()

        if self._expand_on_hover and self._expanded_width > self.COLLAPSED_WIDTH:
            self.expansion_changed.emit(0)

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._scale_anim.stop()
            self._scale_anim.setDuration(100)
            self._scale_anim.setStartValue(self._scale_factor)
            self._scale_anim.setEndValue(0.92)
            self._scale_anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._scale_anim.stop()
            self._scale_anim.setDuration(240)
            self._scale_anim.setStartValue(self._scale_factor)
            self._scale_anim.setEndValue(1.0)
            self._scale_anim.start()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() / 2.0, self.height() / 2.0
        painter.translate(cx, cy)
        painter.scale(self._scale_factor, self._scale_factor)
        painter.translate(-cx, -cy)

        rect = QRectF(2.0, 2.0, self.width() - 4.0, self.height() - 4.0)
        t = self._expand_progress

        r = int(self._base_bg.red() + (self._hover_bg.red() - self._base_bg.red()) * t)
        g = int(
            self._base_bg.green() + (self._hover_bg.green() - self._base_bg.green()) * t
        )
        b = int(
            self._base_bg.blue() + (self._hover_bg.blue() - self._base_bg.blue()) * t
        )
        a = int(
            self._base_bg.alpha() + (self._hover_bg.alpha() - self._base_bg.alpha()) * t
        )
        bg_col = QColor(r, g, b, a)

        border_col = QColor(self._accent_color)
        border_col.setAlpha(int(100 + 155 * t))

        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, 1.3 + 0.6 * t, Qt.PenStyle.SolidLine))
        painter.drawRoundedRect(rect, 11.0, 11.0)

        if not self._expand_on_hover or t <= 0.05:
            painter.setPen(QPen(self._text_color))
            painter.setFont(self._icon_font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._icon_text)
        else:
            icon_box_w = 28.0
            start_x = (self.width() - icon_box_w) / 2.0
            target_x = 8.0
            cur_icon_x = start_x + (target_x - start_x) * t

            icon_rect = QRectF(cur_icon_x, 2.0, icon_box_w, self.height() - 4.0)
            painter.setPen(QPen(self._text_color))
            painter.setFont(self._icon_font)
            painter.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, self._icon_text)

            text_col = QColor(self._text_color)
            text_col.setAlpha(int(255 * min(1.0, max(0.0, (t - 0.12) / 0.88))))
            painter.setPen(QPen(text_col))
            painter.setFont(self._label_font)

            slide_offset = (1.0 - t) * 8.0
            text_rect = QRectF(
                cur_icon_x + icon_box_w + 2.0 + slide_offset,
                2.0,
                max(0.0, self.width() - (cur_icon_x + icon_box_w + 10.0)),
                self.height() - 4.0,
            )
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                self._label_text,
            )

        painter.end()


# ---------------------------------------------------------------------------
# 6. Thread-Safe Sinyal Köprüsü ve Watchdog Klasör Dinleyici
# ---------------------------------------------------------------------------
class FileCatcherBridge(QObject):
    file_caught = pyqtSignal(str, str, str, str)


class UnifiedDropHandler(FileSystemEventHandler):
    def __init__(self, ignore_exts: List[str], bridge: FileCatcherBridge):
        super().__init__()
        self.ignore_exts = {ext.lower() for ext in ignore_exts}
        self.bridge = bridge
        self._recent_emits: Dict[str, float] = {}

    def _is_ignored(self, file_path: str) -> bool:
        name_lower = os.path.basename(file_path).lower()
        if name_lower.startswith(".") or name_lower in {"desktop.ini", "thumbs.db"}:
            return True
        return any(name_lower.endswith(ext) for ext in self.ignore_exts)

    def _handle_file(self, raw_path: str):
        abs_path = os.path.abspath(raw_path)
        if os.path.isdir(abs_path) or self._is_ignored(abs_path):
            return

        now = time.time()
        if len(self._recent_emits) > 64:
            self._recent_emits = {
                k: t for k, t in self._recent_emits.items() if now - t < 10.0
            }

        if now - self._recent_emits.get(abs_path, 0.0) < 2.0:
            return
        self._recent_emits[abs_path] = now

        for _ in range(10):
            if os.path.exists(abs_path) and os.path.getsize(abs_path) > 0:
                break
            time.sleep(0.08)

        if not os.path.exists(abs_path):
            return

        source_name, source_icon, accent_color = detect_source_from_path(abs_path)
        print(f"[{source_icon} {source_name}] Yakalandı: {abs_path}")
        self.bridge.file_caught.emit(abs_path, source_name, source_icon, accent_color)

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle_file(os.fsdecode(event.src_path))

    def on_moved(self, event: FileMovedEvent):
        if not event.is_directory:
            self._handle_file(os.fsdecode(event.dest_path))


# ---------------------------------------------------------------------------
# 7. Bağımsız Dinamik Popup UI (Buton Hover Morf + OutBack Genişleme + Tema)
# ---------------------------------------------------------------------------
class UniversalDropPopup(QWidget):
    BASE_WIDTH = 290
    POPUP_HEIGHT = 282
    CORNER_RADIUS = 30.0
    BORDER_WIDTH = 3.5
    MARGIN = 6.0

    def __init__(
        self,
        file_path: str,
        source_name: str,
        source_icon: str,
        accent_color: str,
        duration_sec: int,
        direction: str = "top",
        theme_key: str = "ocean",
        on_add_to_tray: Optional[Callable[[str], None]] = None,
        stack_index: int = 0,
    ):
        super().__init__()
        self.file_path = os.path.abspath(file_path)
        self.source_name = source_name
        self.source_icon = source_icon
        self.accent_color = accent_color
        self.duration_ms = max(2000, int(duration_sec * 1000))
        self.direction = direction
        self.theme_key = theme_key
        self.on_add_to_tray = on_add_to_tray
        self.stack_index = stack_index

        self._border_progress: float = 1.0
        self.drag_start_pos: Optional[QPoint] = None
        self.is_dragging = False
        self._is_closing = False

        self._card_rect = QRectF()
        self._bg_path = QPainterPath()
        self._perimeter_path = QPainterPath()
        self._perimeter_length: float = 1.0
        self._bg_brush = QBrush()
        self._border_brush = QBrush()
        self._track_pen = QPen()

        self._configure_window()
        self._build_centered_ui()
        self._rebuild_paint_cache()
        self.apply_theme(self.theme_key)
        self._setup_animations()

    @pyqtProperty(float)
    def borderProgress(self) -> float:
        return self._border_progress

    @borderProgress.setter
    def borderProgress(self, value: float):
        self._border_progress = max(0.0, min(1.0, value))
        self.update()

    def _configure_window(self):
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.resize(self.BASE_WIDTH, self.POPUP_HEIGHT)
        self.setMinimumSize(self.BASE_WIDTH, self.POPUP_HEIGHT)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def _rebuild_paint_cache(self):
        self._card_rect = QRectF(
            self.MARGIN,
            self.MARGIN,
            max(20.0, self.width() - 2 * self.MARGIN),
            max(20.0, self.height() - 2 * self.MARGIN),
        )
        self._bg_path = QPainterPath()
        self._bg_path.addRoundedRect(
            self._card_rect, self.CORNER_RADIUS, self.CORNER_RADIUS
        )
        self._perimeter_path = build_clockwise_perimeter_path(
            self._card_rect, self.CORNER_RADIUS
        )
        self._perimeter_length = max(1.0, self._perimeter_path.length())
        self._bg_brush = build_theme_bg_brush(self._card_rect, self.theme_key)
        self._border_brush = build_theme_border_brush(self._card_rect, self.theme_key)

    def resizeEvent(self, event: QResizeEvent):
        self._rebuild_paint_cache()
        super().resizeEvent(event)

    def _build_centered_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_pixmap = create_low_ram_thumbnail(
            self.file_path, 82, radius=22, theme_key=self.theme_key
        )
        self.thumb_label = QLabel(self)
        self.thumb_label.setFixedSize(82, 82)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setPixmap(self.preview_pixmap)
        layout.addWidget(self.thumb_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(2)

        self.source_label = QLabel(f"{self.source_icon}  {self.source_name}", self)
        self.source_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.source_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        filename = os.path.basename(self.file_path)
        self.name_label = QLabel(self)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        elided = self.name_label.fontMetrics().elidedText(
            filename, Qt.TextElideMode.ElideMiddle, 240
        )
        self.name_label.setText(elided)
        self.name_label.setToolTip(filename)
        layout.addWidget(self.name_label)

        size_bytes = (
            os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0
        )
        size_kb = size_bytes / 1024.0
        size_str = (
            f"{size_kb / 1024:.1f} MB"
            if size_kb >= 1024
            else f"{max(0.1, size_kb):.1f} KB"
        )
        self.meta_label = QLabel(f"{size_str}  •  Sürükle veya Tıkla", self)
        self.meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.meta_label)

        layout.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(7)
        btn_row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self.btn_close = MorphingActionButton(
            "✕", "Kapat", "#F87171", self.theme_key, True, self
        )
        self.btn_tray = MorphingActionButton(
            "📥", "Tepsiye Ekle", "#2DD4BF", self.theme_key, True, self
        )
        self.btn_copy = MorphingActionButton(
            "📋", "Kopyala", "#38BDF8", self.theme_key, True, self
        )
        self.btn_share = MorphingActionButton(
            "🔗", "Paylaş", "#34D399", self.theme_key, True, self
        )

        self.btn_close.clicked.connect(self._start_exit_animation)
        self.btn_tray.clicked.connect(self._action_add_to_tray)
        self.btn_copy.clicked.connect(self._action_copy)
        self.btn_share.clicked.connect(self._action_share)

        for btn in (self.btn_close, self.btn_tray, self.btn_copy, self.btn_share):
            btn.expansion_changed.connect(self._on_button_expansion_changed)
            btn_row.addWidget(btn)

        btn_row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        layout.addLayout(btn_row)

    def _on_button_expansion_changed(self, extra_btn_width: int):
        if self._is_closing:
            return
        new_w = self.BASE_WIDTH + extra_btn_width
        target_rect = self._calculate_rect_for_width(new_w)

        self._resize_anim.stop()
        self._resize_anim.setStartValue(self.geometry())
        self._resize_anim.setEndValue(target_rect)
        self._resize_anim.start()

    def apply_theme(self, theme_key: str):
        self.theme_key = theme_key
        spec = get_theme_spec(theme_key)
        self._rebuild_paint_cache()

        self._track_pen = QPen(
            QColor(*spec["track_color"]),
            self.BORDER_WIDTH,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )

        self.source_label.setStyleSheet(
            f"""
            color: {spec['accent_primary']};
            background-color: {spec['card_bg']};
            border: 1px solid {spec['card_border']};
            border-radius: 10px;
            padding: 3px 10px;
            font-size: 11px;
            font-weight: bold;
            """
        )
        self.name_label.setStyleSheet(
            f"color: {spec['text_primary']}; font-size: 13px; font-weight: bold;"
        )
        self.meta_label.setStyleSheet(
            f"color: {spec['text_secondary']}; font-size: 11px;"
        )

        for btn in (self.btn_close, self.btn_tray, self.btn_copy, self.btn_share):
            btn.apply_theme(theme_key)

        self.update()

    def _action_add_to_tray(self):
        if self.on_add_to_tray is not None:
            self.on_add_to_tray(self.file_path)
        self.meta_label.setText("✓ Tepsiye eklendi!")
        QTimer.singleShot(220, self._start_exit_animation)

    def _action_copy(self):
        copy_file_to_clipboard(self.file_path)
        self.meta_label.setText("✓ Panoya kopyalandı!")

    def _action_share(self):
        open_native_share_ui(self.file_path, self)
        self.meta_label.setText("✓ Paylaşım penceresi açıldı!")

    def _calculate_rect_for_width(self, width: int) -> QRect:
        screen = QApplication.primaryScreen()
        screen_geo = screen.geometry() if screen else QRect(0, 0, 1920, 1080)
        avail = screen.availableGeometry() if screen else screen_geo
        cx, cy = avail.center().x(), avail.center().y()
        margin = 14

        if self.direction == "left":
            offset_y = self.stack_index * 24
            target_x = avail.left() + margin
            target_y = cy - (self.POPUP_HEIGHT // 2) + offset_y
        elif self.direction == "top":
            offset_x = self.stack_index * 24
            target_x = cx - (width // 2) + offset_x
            target_y = 0
        elif self.direction == "bottom":
            offset_x = self.stack_index * 24
            target_x = cx - (width // 2) + offset_x
            target_y = avail.bottom() - self.POPUP_HEIGHT - margin
        else:
            offset_y = self.stack_index * 24
            target_x = avail.right() - width - margin
            target_y = cy - (self.POPUP_HEIGHT // 2) + offset_y

        return QRect(target_x, target_y, width, self.POPUP_HEIGHT)

    def _calculate_centered_edge_positions(self) -> Tuple[QPoint, QPoint]:
        target_rect = self._calculate_rect_for_width(self.BASE_WIDTH)
        target_pos = target_rect.topLeft()
        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

        if self.direction == "left":
            start_pos = QPoint(avail.left() - self.BASE_WIDTH - 24, target_pos.y())
        elif self.direction == "top":
            start_pos = QPoint(target_pos.x(), -self.POPUP_HEIGHT - 24)
        elif self.direction == "bottom":
            start_pos = QPoint(target_pos.x(), avail.bottom() + 24)
        else:
            start_pos = QPoint(avail.right() + 24, target_pos.y())

        return start_pos, target_pos

    def _setup_animations(self):
        self._start_pos, self._target_pos = self._calculate_centered_edge_positions()
        self.move(self._start_pos)
        self.setWindowOpacity(0.0)

        self._resize_anim = QPropertyAnimation(self, b"geometry", self)
        self._resize_anim.setDuration(340)
        resize_curve = QEasingCurve(QEasingCurve.Type.OutBack)
        resize_curve.setOvershoot(1.10)
        self._resize_anim.setEasingCurve(resize_curve)

        self.enter_group = QParallelAnimationGroup(self)

        pos_in = QPropertyAnimation(self, b"pos", self)
        pos_in.setDuration(520)
        pos_in.setStartValue(self._start_pos)
        pos_in.setEndValue(self._target_pos)
        back_in_curve = QEasingCurve(QEasingCurve.Type.OutBack)
        back_in_curve.setOvershoot(1.15)
        pos_in.setEasingCurve(back_in_curve)

        fade_in = QPropertyAnimation(self, b"windowOpacity", self)
        fade_in.setDuration(340)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.enter_group.addAnimation(pos_in)
        self.enter_group.addAnimation(fade_in)

        self.border_anim = QPropertyAnimation(self, b"borderProgress", self)
        self.border_anim.setDuration(self.duration_ms)
        self.border_anim.setStartValue(1.0)
        self.border_anim.setEndValue(0.0)
        self.border_anim.setEasingCurve(QEasingCurve.Type.Linear)
        self.border_anim.finished.connect(self._start_exit_animation)

        self.exit_group = QParallelAnimationGroup(self)

        self._pos_out = QPropertyAnimation(self, b"pos", self)
        self._pos_out.setDuration(400)
        back_out_curve = QEasingCurve(QEasingCurve.Type.InBack)
        back_out_curve.setOvershoot(1.05)
        self._pos_out.setEasingCurve(back_out_curve)

        fade_out = QPropertyAnimation(self, b"windowOpacity", self)
        fade_out.setDuration(360)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InExpo)

        self.exit_group.addAnimation(self._pos_out)
        self.exit_group.addAnimation(fade_out)
        self.exit_group.finished.connect(self.close)

    def showEvent(self, event):
        super().showEvent(event)
        self.enter_group.start()
        self.border_anim.start()

    def _start_exit_animation(self):
        if not self.is_dragging and not self._is_closing:
            self._is_closing = True
            self._resize_anim.stop()
            self._pos_out.setStartValue(self.pos())
            self._pos_out.setEndValue(self._start_pos)
            self.exit_group.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillPath(self._bg_path, self._bg_brush)
        painter.setPen(self._track_pen)
        painter.drawPath(self._perimeter_path)

        if self._border_progress > 0.002:
            pen = QPen(
                self._border_brush,
                self.BORDER_WIDTH,
                Qt.PenStyle.CustomDashLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
            total_units = self._perimeter_length / self.BORDER_WIDTH
            active_units = max(0.01, total_units * self._border_progress)
            pen.setDashPattern([active_units, total_units])
            painter.setPen(pen)
            painter.drawPath(self._perimeter_path)

        painter.end()

    def enterEvent(self, event):
        if self._is_closing:
            self.exit_group.stop()
            self._is_closing = False
            self.move(self._target_pos)
            self.setWindowOpacity(1.0)

        if self.border_anim.state() == QPropertyAnimation.State.Running:
            self.border_anim.pause()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_dragging and not self._is_closing:
            if self.border_anim.state() == QPropertyAnimation.State.Paused:
                self.border_anim.resume()
            else:
                self.border_anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.RightButton:
            self._start_exit_animation()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self.drag_start_pos is None:
            return

        dist = (event.position().toPoint() - self.drag_start_pos).manhattanLength()
        if dist >= QApplication.startDragDistance():
            self._start_os_drag()

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.drag_start_pos is not None
            and not self.is_dragging
        ):
            open_with_default_app(self.file_path)
            self.close()
        self.drag_start_pos = None

    def _start_os_drag(self):
        if not os.path.exists(self.file_path):
            self.close()
            return

        self.is_dragging = True
        self.border_anim.pause()
        self.drag_start_pos = None
        self.setWindowOpacity(0.35)

        result_action = execute_os_file_drag(self, self.file_path, self.preview_pixmap)

        self.is_dragging = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        if result_action != Qt.DropAction.IgnoreAction:
            self.close()
        else:
            self.setWindowOpacity(1.0)
            self.border_anim.resume()

    def closeEvent(self, event: QCloseEvent):
        self.preview_pixmap = QPixmap()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# 8. İki Aşamalı Morf Edilen, Sıfır Boşluklu, Solid Çizgili & Entegre Tepsi
# ---------------------------------------------------------------------------
class ShelfItemWidget(QFrame):
    removed = pyqtSignal(str)
    drag_started = pyqtSignal()
    drag_finished = pyqtSignal(bool)

    def __init__(
        self,
        file_path: str,
        drawer: "EdgeDrawer",
        theme_key: str = "ocean",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.file_path = os.path.abspath(file_path)
        self.drawer = drawer
        self.theme_key = theme_key
        self.drag_start_pos: Optional[QPoint] = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setFixedHeight(64)
        self.setObjectName("shelfItem")

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(10)

        self.thumb_pix = create_low_ram_thumbnail(
            self.file_path, 46, radius=12, theme_key=self.theme_key
        )
        self.icon_lbl = QLabel(self)
        self.icon_lbl.setFixedSize(46, 46)
        self.icon_lbl.setPixmap(self.thumb_pix)
        row.addWidget(self.icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        fname = os.path.basename(self.file_path)
        self.name_lbl = QLabel(fname, self)
        self.name_lbl.setToolTip(fname)

        size_b = (
            os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0
        )
        size_kb = size_b / 1024.0
        size_str = (
            f"{size_kb / 1024:.1f} MB"
            if size_kb >= 1024
            else f"{max(0.1, size_kb):.1f} KB"
        )
        self.sub_lbl = QLabel(f"{size_str} • Dışarı sürükle veya tıkla", self)

        text_col.addWidget(self.name_lbl)
        text_col.addWidget(self.sub_lbl)
        row.addLayout(text_col, stretch=1)

        self.del_btn = MorphingActionButton(
            "✕", "Raftan Kaldır", "#EF4444", self.theme_key, False, self
        )
        self.del_btn.setFixedSize(28, 28)
        self.del_btn.clicked.connect(lambda: self.removed.emit(self.file_path))
        row.addWidget(self.del_btn)

        self.apply_theme(self.theme_key)

    def apply_theme(self, theme_key: str):
        self.theme_key = theme_key
        spec = get_theme_spec(theme_key)
        self.setStyleSheet(
            f"""
            QFrame#shelfItem {{
                background-color: {spec['card_bg']};
                border: 1px solid {spec['card_border']};
                border-radius: 14px;
            }}
            QFrame#shelfItem:hover {{
                background-color: {spec['card_hover_bg']};
                border: 1.5px solid {spec['accent_primary']};
            }}
            """
        )
        self.name_lbl.setStyleSheet(
            f"color: {spec['text_primary']}; font-size: 12px; font-weight: bold; border: none; background: transparent;"
        )
        self.sub_lbl.setStyleSheet(
            f"color: {spec['text_secondary']}; font-size: 10px; border: none; background: transparent;"
        )
        self.del_btn.apply_theme(theme_key)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            not (event.buttons() & Qt.MouseButton.LeftButton)
            or self.drag_start_pos is None
        ):
            return
        dist = (event.position().toPoint() - self.drag_start_pos).manhattanLength()
        if dist < QApplication.startDragDistance():
            return

        self.drag_start_pos = None
        if not os.path.exists(self.file_path):
            self.removed.emit(self.file_path)
            return

        self.drag_started.emit()
        action = execute_os_file_drag(self, self.file_path, self.thumb_pix)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        cursor_now = QCursor.pos()
        dropped_on_self = (
            self.drawer.geometry().adjusted(-12, -12, 12, 12).contains(cursor_now)
        )
        dropped_externally = (action != Qt.DropAction.IgnoreAction) and (
            not dropped_on_self
        )

        self.drag_finished.emit(dropped_externally)
        if dropped_externally:
            self.removed.emit(self.file_path)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.drag_start_pos is not None
        ):
            open_with_default_app(self.file_path)
        self.drag_start_pos = None
        super().mouseReleaseEvent(event)


class EdgeDrawer(QWidget):
    STATE_HIDDEN = 0
    STATE_BAR = 1
    STATE_TRAY = 2

    PROXIMITY_THICKNESS = 14
    CORNER_SAFE_MARGIN = 64

    BAR_THICKNESS = 10
    BAR_LENGTH = 136

    TRAY_BASE_MIN_WIDTH = 340
    TRAY_MAX_WIDTH = 680
    TRAY_EMPTY_HEIGHT = 185
    TRAY_HEADER_BASE_H = 100
    TRAY_ITEM_STEP_H = 72
    TRAY_INCOMING_CARD_H = 215
    TRAY_MAX_HEIGHT = 600
    BORDER_WIDTH = 3.5

    def __init__(self, direction: str = "top", theme_key: str = "ocean"):
        super().__init__()
        self.direction = direction
        self.theme_key = theme_key
        self.state = self.STATE_HIDDEN
        self.is_dragging_out = False
        self.is_drag_hovering = False
        self.shelf_files: Dict[str, ShelfItemWidget] = {}

        self._incoming_file_path: Optional[str] = None
        self._incoming_pixmap: QPixmap = QPixmap()
        self._incoming_drag_pos: Optional[QPoint] = None
        self._border_progress: float = 0.0
        self._hovered_btn_extra_w: int = 0

        self.proximity_strip = _ProximityStrip(self)

        self._configure_morph_window()
        self._build_tray_ui()
        self.apply_theme(self.theme_key)
        self._setup_morph_animations()

        self.state_timer = QTimer(self)
        self.state_timer.setSingleShot(True)
        self.state_timer.setInterval(240)
        self.state_timer.timeout.connect(self._evaluate_hover_state)

        self.reposition_for_direction(self.direction)
        self.proximity_strip.show()

    @pyqtProperty(float)
    def borderProgress(self) -> float:
        return self._border_progress

    @borderProgress.setter
    def borderProgress(self, value: float):
        self._border_progress = max(0.0, min(1.0, value))
        self.update()

    def _configure_morph_window(self):
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAcceptDrops(True)
        self.setMinimumSize(6, 6)
        self.setMaximumSize(16777215, 16777215)

    def _build_tray_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        self.content_frame = QWidget(self)
        root = QVBoxLayout(self.content_frame)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(10)

        self.incoming_card = QFrame(self.content_frame)
        self.incoming_card.setObjectName("incomingCard")
        inc_layout = QVBoxLayout(self.incoming_card)
        inc_layout.setContentsMargins(14, 12, 14, 12)
        inc_layout.setSpacing(6)
        inc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_inc_row = QHBoxLayout()
        top_inc_row.setSpacing(12)

        self.inc_thumb_lbl = QLabel(self.incoming_card)
        self.inc_thumb_lbl.setFixedSize(64, 64)
        self.inc_thumb_lbl.setCursor(Qt.CursorShape.OpenHandCursor)
        top_inc_row.addWidget(self.inc_thumb_lbl)

        inc_info_col = QVBoxLayout()
        inc_info_col.setSpacing(3)
        self.inc_source_lbl = QLabel(self.incoming_card)
        self.inc_name_lbl = QLabel(self.incoming_card)
        self.inc_meta_lbl = QLabel(self.incoming_card)

        inc_info_col.addWidget(self.inc_source_lbl)
        inc_info_col.addWidget(self.inc_name_lbl)
        inc_info_col.addWidget(self.inc_meta_lbl)
        top_inc_row.addLayout(inc_info_col, stretch=1)
        inc_layout.addLayout(top_inc_row)

        inc_btn_row = QHBoxLayout()
        inc_btn_row.setSpacing(7)
        inc_btn_row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self.inc_btn_close = MorphingActionButton(
            "✕", "Kapat", "#F87171", self.theme_key, True, self.incoming_card
        )
        self.inc_btn_tray = MorphingActionButton(
            "📥", "Tepsiye Ekle", "#2DD4BF", self.theme_key, True, self.incoming_card
        )
        self.inc_btn_copy = MorphingActionButton(
            "📋", "Kopyala", "#38BDF8", self.theme_key, True, self.incoming_card
        )
        self.inc_btn_share = MorphingActionButton(
            "🔗", "Paylaş", "#34D399", self.theme_key, True, self.incoming_card
        )

        self.inc_btn_close.clicked.connect(self._dismiss_incoming_card)
        self.inc_btn_tray.clicked.connect(self._move_incoming_to_shelf)
        self.inc_btn_copy.clicked.connect(self._copy_incoming_file)
        self.inc_btn_share.clicked.connect(self._share_incoming_file)

        for btn in (
            self.inc_btn_close,
            self.inc_btn_tray,
            self.inc_btn_copy,
            self.inc_btn_share,
        ):
            btn.expansion_changed.connect(self._on_inc_button_expansion_changed)
            inc_btn_row.addWidget(btn)

        inc_btn_row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        inc_layout.addLayout(inc_btn_row)

        self.incoming_card.hide()
        root.addWidget(self.incoming_card)

        header_row = QHBoxLayout()
        self.title_lbl = QLabel("🗄️  Dosya Rafı (Dropzone)", self.content_frame)
        self.count_badge = QLabel("0 Dosya", self.content_frame)
        header_row.addWidget(self.title_lbl)
        header_row.addStretch()
        header_row.addWidget(self.count_badge)
        root.addLayout(header_row)

        self.sub_lbl = QLabel(
            "Dosyaları buraya bırakın, istediğiniz zaman dışarı sürükleyin.",
            self.content_frame,
        )
        self.sub_lbl.setWordWrap(True)
        root.addWidget(self.sub_lbl)

        self.scroll = QScrollArea(self.content_frame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 2, 4, 2)
        self.list_layout.setSpacing(8)

        self.empty_label = QLabel(
            "📥  Raf şu an boş.\nDosyaları buraya sürükleyip bırakabilirsiniz.",
            self.list_container,
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_layout.addWidget(self.empty_label)
        self.list_layout.addStretch()

        self.scroll.setWidget(self.list_container)
        root.addWidget(self.scroll, stretch=1)
        outer.addWidget(self.content_frame)

        self.content_frame.hide()

    def _on_inc_button_expansion_changed(self, extra_w: int):
        self._hovered_btn_extra_w = extra_w
        if self.state == self.STATE_TRAY and self.isVisible():
            self._animate_dynamic_resize()

    def apply_theme(self, theme_key: str):
        self.theme_key = theme_key
        spec = get_theme_spec(theme_key)

        self.incoming_card.setStyleSheet(
            f"""
            QFrame#incomingCard {{
                background-color: {spec['card_bg']};
                border: 1.5px solid {spec['accent_primary']};
                border-radius: 18px;
            }}
            """
        )
        self.inc_source_lbl.setStyleSheet(
            f"color: {spec['accent_primary']}; font-size: 11px; font-weight: bold;"
        )
        self.inc_name_lbl.setStyleSheet(
            f"color: {spec['text_primary']}; font-size: 13px; font-weight: bold;"
        )
        self.inc_meta_lbl.setStyleSheet(
            f"color: {spec['text_secondary']}; font-size: 11px;"
        )

        for btn in (
            self.inc_btn_close,
            self.inc_btn_tray,
            self.inc_btn_copy,
            self.inc_btn_share,
        ):
            btn.apply_theme(theme_key)

        self.title_lbl.setStyleSheet(
            f"color: {spec['text_primary']}; font-size: 13px; font-weight: bold;"
        )
        self.count_badge.setStyleSheet(
            f"""
            color: {spec['accent_primary']};
            background-color: {spec['card_bg']};
            border: 1px solid {spec['card_border']};
            border-radius: 9px;
            padding: 2px 9px;
            font-size: 11px;
            font-weight: bold;
            """
        )
        self.sub_lbl.setStyleSheet(
            f"color: {spec['text_secondary']}; font-size: 11px;"
        )
        self.scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {spec['accent_primary']};
                border-radius: 3px;
            }}
            """
        )
        # KESİK ÇİZGİ DÜZELTMESİ: dashed yerine pürüzsüz düz çizgi (solid)
        self.empty_label.setStyleSheet(
            f"""
            color: {spec['text_secondary']};
            background-color: {spec['card_bg']};
            border: 1.5px solid {spec['card_border']};
            border-radius: 14px;
            padding: 16px 12px;
            font-size: 11px;
            """
        )

        for item_widget in self.shelf_files.values():
            item_widget.apply_theme(theme_key)

        self.update()

    def _setup_morph_animations(self):
        self.morph_group = QParallelAnimationGroup(self)

        self.geom_anim = QPropertyAnimation(self, b"geometry", self)
        self.geom_anim.setDuration(420)

        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self.opacity_anim.setDuration(300)

        self.morph_group.addAnimation(self.geom_anim)
        self.morph_group.addAnimation(self.opacity_anim)
        self.morph_group.finished.connect(self._on_morph_finished)

        self.border_anim = QPropertyAnimation(self, b"borderProgress", self)
        self.border_anim.setEasingCurve(QEasingCurve.Type.Linear)
        self.border_anim.finished.connect(self._on_integrated_timer_finished)

    def present_incoming_file(
        self,
        file_path: str,
        source_name: str,
        source_icon: str,
        accent_color: str,
        duration_sec: int,
    ):
        self._incoming_file_path = os.path.abspath(file_path)
        self._incoming_pixmap = create_low_ram_thumbnail(
            self._incoming_file_path, 64, radius=16, theme_key=self.theme_key
        )
        self.inc_thumb_lbl.setPixmap(self._incoming_pixmap)
        self.inc_source_lbl.setText(f"{source_icon}  {source_name} (Yeni Dosya)")

        fname = os.path.basename(self._incoming_file_path)
        self.inc_name_lbl.setText(fname)
        self.inc_name_lbl.setToolTip(fname)

        size_b = (
            os.path.getsize(self._incoming_file_path)
            if os.path.exists(self._incoming_file_path)
            else 0
        )
        size_kb = size_b / 1024.0
        size_str = (
            f"{size_kb / 1024:.1f} MB"
            if size_kb >= 1024
            else f"{max(0.1, size_kb):.1f} KB"
        )
        self.inc_meta_lbl.setText(f"{size_str} • Sürükle, Tıkla veya Aksiyon Seç")

        self.incoming_card.show()

        self.border_anim.stop()
        self._border_progress = 1.0
        self.border_anim.setDuration(max(2000, int(duration_sec * 1000)))
        self.border_anim.setStartValue(1.0)
        self.border_anim.setEndValue(0.0)

        if self.state != self.STATE_TRAY or not self.isVisible():
            self.expand_drawer()
        else:
            self._animate_dynamic_resize()

        self.border_anim.start()

    def _dismiss_incoming_card(self):
        self.border_anim.stop()
        self._border_progress = 0.0
        self._incoming_file_path = None
        self._hovered_btn_extra_w = 0
        self.incoming_card.hide()
        self.update()
        cursor_pos = QCursor.pos()
        if not self.geometry().contains(cursor_pos):
            self.transition_to_bar()
        else:
            self._animate_dynamic_resize()

    def _move_incoming_to_shelf(self):
        if self._incoming_file_path:
            path_to_add = self._incoming_file_path
            self.border_anim.stop()
            self._border_progress = 0.0
            self._incoming_file_path = None
            self._hovered_btn_extra_w = 0
            self.incoming_card.hide()
            self.add_files_to_shelf([path_to_add])
            self.update()

    def _copy_incoming_file(self):
        if self._incoming_file_path:
            copy_file_to_clipboard(self._incoming_file_path)
            self.inc_meta_lbl.setText("✓ Panoya kopyalandı!")

    def _share_incoming_file(self):
        if self._incoming_file_path:
            open_native_share_ui(self._incoming_file_path, self)
            self.inc_meta_lbl.setText("✓ Paylaşım penceresi açıldı!")

    def _on_integrated_timer_finished(self):
        self._border_progress = 0.0
        self._incoming_file_path = None
        self._hovered_btn_extra_w = 0
        self.incoming_card.hide()
        self.update()
        cursor_pos = QCursor.pos()
        if not self.geometry().contains(cursor_pos):
            self.transition_to_bar()
        else:
            self._animate_dynamic_resize()

    def _calculate_dynamic_tray_size(self) -> QSize:
        fm = QFontMetrics(QFont("Segoe UI", 10, QFont.Weight.Bold))
        longest_px = 190

        for path_str in self.shelf_files.keys():
            name_w = fm.horizontalAdvance(os.path.basename(path_str))
            if name_w > longest_px:
                longest_px = name_w

        if self._incoming_file_path:
            inc_w = (
                fm.horizontalAdvance(os.path.basename(self._incoming_file_path)) + 30
            )
            if inc_w > longest_px:
                longest_px = inc_w

        base_w = max(
            self.TRAY_BASE_MIN_WIDTH,
            min(self.TRAY_MAX_WIDTH, longest_px + 170),
        )
        computed_w = min(self.TRAY_MAX_WIDTH, base_w + self._hovered_btn_extra_w)

        count = len(self.shelf_files)
        if count == 0:
            base_h = self.TRAY_EMPTY_HEIGHT
        else:
            base_h = self.TRAY_HEADER_BASE_H + (count * self.TRAY_ITEM_STEP_H)

        if self._incoming_file_path:
            base_h += self.TRAY_INCOMING_CARD_H

        clamped_h = min(self.TRAY_MAX_HEIGHT, max(self.TRAY_EMPTY_HEIGHT, base_h))
        return QSize(computed_w, clamped_h)

    def _compute_stage_geometries(self) -> Tuple[QRect, QRect, QRect]:
        screen = QApplication.primaryScreen()
        screen_geo = screen.geometry() if screen else QRect(0, 0, 1920, 1080)
        avail = screen.availableGeometry() if screen else screen_geo
        cx, cy = avail.center().x(), avail.center().y()

        p_thick = self.PROXIMITY_THICKNESS
        c_margin = self.CORNER_SAFE_MARGIN
        b_thick = self.BAR_THICKNESS
        b_len = self.BAR_LENGTH

        tray_size = self._calculate_dynamic_tray_size()
        tw, th = tray_size.width(), tray_size.height()

        if self.direction == "left":
            prox_rect = QRect(
                0,
                avail.top() + c_margin,
                p_thick,
                max(200, avail.height() - 2 * c_margin),
            )
            bar_rect = QRect(0, cy - b_len // 2, b_thick, b_len)
            tray_rect = QRect(0, cy - th // 2, tw, th)

        elif self.direction == "top":
            prox_rect = QRect(
                avail.left() + c_margin,
                0,
                max(200, avail.width() - 2 * c_margin),
                p_thick,
            )
            bar_rect = QRect(cx - b_len // 2, 0, b_len, b_thick)
            tray_rect = QRect(cx - tw // 2, 0, tw, th)

        elif self.direction == "bottom":
            bottom_y = screen_geo.bottom()
            prox_rect = QRect(
                avail.left() + c_margin,
                bottom_y - p_thick + 1,
                max(200, avail.width() - 2 * c_margin),
                p_thick,
            )
            bar_rect = QRect(
                cx - b_len // 2, avail.bottom() - b_thick + 1, b_len, b_thick
            )
            tray_rect = QRect(cx - tw // 2, avail.bottom() - th + 1, tw, th)

        else:
            right_x = screen_geo.right()
            prox_rect = QRect(
                right_x - p_thick + 1,
                avail.top() + c_margin,
                p_thick,
                max(200, avail.height() - 2 * c_margin),
            )
            bar_rect = QRect(
                avail.right() - b_thick + 1, cy - b_len // 2, b_thick, b_len
            )
            tray_rect = QRect(avail.right() - tw + 1, cy - th // 2, tw, th)

        return prox_rect, bar_rect, tray_rect

    def reposition_for_direction(self, direction: str):
        self.direction = direction
        prox_rect, bar_rect, tray_rect = self._compute_stage_geometries()
        self.proximity_strip.setGeometry(prox_rect)

        if self.state == self.STATE_TRAY:
            self.setGeometry(tray_rect)
        else:
            self.setGeometry(bar_rect)

    def transition_to_bar(self):
        self.state_timer.stop()
        if self.state == self.STATE_BAR and self.isVisible():
            return

        _, bar_rect, _ = self._compute_stage_geometries()
        previous_state = self.state
        self.state = self.STATE_BAR
        self.content_frame.hide()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.morph_group.stop()

        if previous_state == self.STATE_HIDDEN or not self.isVisible():
            self.setGeometry(bar_rect)
            self.setWindowOpacity(0.0)
            self.show()
            self.raise_()

            self.geom_anim.setDuration(240)
            self.geom_anim.setStartValue(bar_rect)
            self.geom_anim.setEndValue(bar_rect)
            self.geom_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            self.opacity_anim.setDuration(240)
            self.opacity_anim.setStartValue(0.0)
            self.opacity_anim.setEndValue(0.95)
            self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.morph_group.start()
        else:
            self.geom_anim.setDuration(360)
            self.geom_anim.setStartValue(self.geometry())
            self.geom_anim.setEndValue(bar_rect)
            self.geom_anim.setEasingCurve(QEasingCurve.Type.OutExpo)

            self.opacity_anim.setDuration(320)
            self.opacity_anim.setStartValue(self.windowOpacity())
            self.opacity_anim.setEndValue(0.92)
            self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.morph_group.start()

    def expand_drawer(self):
        self.state_timer.stop()
        _, bar_rect, tray_rect = self._compute_stage_geometries()

        if self.state == self.STATE_TRAY and self.isVisible():
            self._animate_dynamic_resize()
            return

        start_rect = self.geometry() if self.isVisible() else bar_rect
        start_opacity = self.windowOpacity() if self.isVisible() else 0.25

        self.state = self.STATE_TRAY
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.proximity_strip.hide()

        self.morph_group.stop()
        self.setGeometry(start_rect)
        self.setWindowOpacity(start_opacity)
        self.show()
        self.raise_()

        self.geom_anim.setDuration(440)
        self.geom_anim.setStartValue(start_rect)
        self.geom_anim.setEndValue(tray_rect)
        morph_curve = QEasingCurve(QEasingCurve.Type.OutBack)
        morph_curve.setOvershoot(1.08)
        self.geom_anim.setEasingCurve(morph_curve)

        self.opacity_anim.setDuration(260)
        self.opacity_anim.setStartValue(start_opacity)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.morph_group.start()

    def _animate_dynamic_resize(self):
        if self.state != self.STATE_TRAY or not self.isVisible():
            return

        _, _, new_tray_rect = self._compute_stage_geometries()
        if self.geometry() == new_tray_rect:
            return

        self.morph_group.stop()
        self.geom_anim.setDuration(320)
        self.geom_anim.setStartValue(self.geometry())
        self.geom_anim.setEndValue(new_tray_rect)
        self.geom_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        self.opacity_anim.setDuration(200)
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(1.0)
        self.morph_group.start()

    def transition_to_hidden(self):
        if self.state == self.STATE_HIDDEN:
            return

        self.state = self.STATE_HIDDEN
        self.content_frame.hide()
        _, bar_rect, _ = self._compute_stage_geometries()

        self.morph_group.stop()
        self.geom_anim.setDuration(260)
        self.geom_anim.setStartValue(self.geometry())
        self.geom_anim.setEndValue(bar_rect)
        self.geom_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        self.opacity_anim.setDuration(240)
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InExpo)
        self.morph_group.start()

    def _on_morph_finished(self):
        if self.state == self.STATE_TRAY:
            self.content_frame.show()
            self.update()
        elif self.state == self.STATE_BAR:
            self.content_frame.hide()
            self.proximity_strip.show()
            self.raise_()
            self.update()
            self.state_timer.start()
        elif self.state == self.STATE_HIDDEN:
            self.content_frame.hide()
            self.hide()
            self.proximity_strip.show()

    def schedule_state_check(self):
        if not self.is_dragging_out and not self.is_drag_hovering:
            if self.border_anim.state() == QPropertyAnimation.State.Running:
                return
            self.state_timer.start()

    def _evaluate_hover_state(self):
        if self.is_dragging_out or self.is_drag_hovering:
            return
        if self.border_anim.state() == QPropertyAnimation.State.Running:
            return

        cursor_pos = QCursor.pos()
        prox_rect, bar_rect, _ = self._compute_stage_geometries()

        if self.state == self.STATE_TRAY:
            if self.geometry().adjusted(-8, -8, 8, 8).contains(cursor_pos):
                return
            self.transition_to_bar()
            return

        if self.state == self.STATE_BAR:
            if bar_rect.adjusted(-6, -6, 6, 6).contains(
                cursor_pos
            ) or prox_rect.adjusted(-4, -4, 4, 4).contains(cursor_pos):
                return
            self.transition_to_hidden()

    def add_files_to_shelf(self, file_paths: List[str]):
        added_any = False
        for raw_p in file_paths:
            if not raw_p:
                continue
            abs_p = os.path.abspath(raw_p)
            if not os.path.exists(abs_p) or os.path.isdir(abs_p):
                continue
            if abs_p in self.shelf_files:
                continue

            item_widget = ShelfItemWidget(
                abs_p, self, self.theme_key, self.list_container
            )
            item_widget.removed.connect(self.remove_file_from_shelf)
            item_widget.drag_started.connect(self._on_item_drag_started)
            item_widget.drag_finished.connect(self._on_item_drag_finished)

            self.shelf_files[abs_p] = item_widget
            self.list_layout.insertWidget(self.list_layout.count() - 1, item_widget)
            added_any = True

        self._refresh_shelf_state()
        if added_any:
            self._animate_dynamic_resize()

    def remove_file_from_shelf(self, file_path: str):
        abs_p = os.path.abspath(file_path)
        widget = self.shelf_files.pop(abs_p, None)
        if widget is not None:
            self.list_layout.removeWidget(widget)
            widget.deleteLater()
        self._refresh_shelf_state()
        self._animate_dynamic_resize()
        gc.collect()

    def _refresh_shelf_state(self):
        count = len(self.shelf_files)
        self.count_badge.setText(f"{count} Dosya")
        self.empty_label.setVisible(count == 0)

    def _on_item_drag_started(self):
        self.is_dragging_out = True
        self.state_timer.stop()
        self.setWindowOpacity(0.45)

    def _on_item_drag_finished(self, dropped: bool):
        self.is_dragging_out = False
        self.setWindowOpacity(1.0)
        self.schedule_state_check()

    def enterEvent(self, event):
        self.state_timer.stop()
        if self.border_anim.state() == QPropertyAnimation.State.Running:
            self.border_anim.pause()
        if self.state != self.STATE_TRAY:
            self.expand_drawer()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if (
            self._incoming_file_path
            and self.border_anim.state() == QPropertyAnimation.State.Paused
        ):
            self.border_anim.resume()
        self.schedule_state_check()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._incoming_file_path:
            self._incoming_drag_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self._incoming_file_path
            and self._incoming_drag_pos is not None
            and (event.buttons() & Qt.MouseButton.LeftButton)
        ):
            dist = (
                event.position().toPoint() - self._incoming_drag_pos
            ).manhattanLength()
            if dist >= QApplication.startDragDistance():
                self._incoming_drag_pos = None
                self.is_dragging_out = True
                self.border_anim.pause()
                self.setWindowOpacity(0.45)
                act = execute_os_file_drag(
                    self, self._incoming_file_path, self._incoming_pixmap
                )
                self.is_dragging_out = False
                self.setWindowOpacity(1.0)
                if act != Qt.DropAction.IgnoreAction:
                    self._dismiss_incoming_card()
                else:
                    self.border_anim.resume()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._incoming_file_path
            and self._incoming_drag_pos is not None
        ):
            open_with_default_app(self._incoming_file_path)
            self._dismiss_incoming_card()
        self._incoming_drag_pos = None
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        src = event.source()
        if self.is_dragging_out or (
            isinstance(src, QWidget) and (src is self or self.isAncestorOf(src))
        ):
            event.ignore()
            return

        if event.mimeData().hasUrls():
            self.is_drag_hovering = True
            self.state_timer.stop()
            event.acceptProposedAction()
            if self.state != self.STATE_TRAY:
                self.expand_drawer()
            self.update()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        src = event.source()
        if self.is_dragging_out or (
            isinstance(src, QWidget) and (src is self or self.isAncestorOf(src))
        ):
            event.ignore()
            return
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.is_drag_hovering = False
        self.update()
        self.schedule_state_check()

    def dropEvent(self, event: QDropEvent):
        self.is_drag_hovering = False
        src = event.source()
        if self.is_dragging_out or (
            isinstance(src, QWidget) and (src is self or self.isAncestorOf(src))
        ):
            event.setDropAction(Qt.DropAction.IgnoreAction)
            event.ignore()
            self.update()
            return

        urls = event.mimeData().urls()
        local_files = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if local_files:
            if self.state != self.STATE_TRAY:
                self.expand_drawer()
            self.add_files_to_shelf(local_files)
            event.acceptProposedAction()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        spec = get_theme_spec(self.theme_key)

        if self.state == self.STATE_BAR and not self.content_frame.isVisible():
            rect = QRectF(self.rect()).adjusted(1.0, 0.5, -1.0, -1.0)
            radius = min(12.0, rect.width() / 2.0, rect.height() / 2.0)
            path = QPainterPath()
            path.addRoundedRect(rect, radius, radius)
            painter.fillPath(path, build_theme_bar_brush(rect, self.theme_key))
            painter.setPen(
                QPen(QColor(spec["text_primary"]), 1.1, Qt.PenStyle.SolidLine)
            )
            painter.drawPath(path)
        else:
            top_inset = 0.5 if self.direction == "top" else 3.0
            rect = QRectF(self.rect()).adjusted(3.0, top_inset, -3.0, -3.0)
            radius = min(26.0, rect.width() / 2.0, rect.height() / 2.0)
            path = QPainterPath()
            path.addRoundedRect(rect, radius, radius)

            painter.fillPath(path, build_theme_bg_brush(rect, self.theme_key))

            if self._border_progress > 0.002:
                painter.setPen(
                    QPen(
                        QColor(*spec["track_color"]),
                        self.BORDER_WIDTH,
                        Qt.PenStyle.SolidLine,
                    )
                )
                perim = build_clockwise_perimeter_path(rect, radius)
                painter.drawPath(perim)

                pen = QPen(
                    build_theme_border_brush(rect, self.theme_key),
                    self.BORDER_WIDTH,
                    Qt.PenStyle.CustomDashLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
                total_u = perim.length() / self.BORDER_WIDTH
                active_u = max(0.01, total_u * self._border_progress)
                pen.setDashPattern([active_u, total_u])
                painter.setPen(pen)
                painter.drawPath(perim)
            else:
                pen_width = 2.8 if self.is_drag_hovering else 2.0
                painter.setPen(
                    QPen(
                        build_theme_border_brush(rect, self.theme_key),
                        pen_width,
                        Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap,
                        Qt.PenJoinStyle.RoundJoin,
                    )
                )
                painter.drawPath(path)

        painter.end()

    def close_all(self):
        self.proximity_strip.close()
        self.close()


class _ProximityStrip(QWidget):
    def __init__(self, drawer: EdgeDrawer):
        super().__init__()
        self.drawer = drawer
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAcceptDrops(True)

    def enterEvent(self, event):
        if self.drawer.state == EdgeDrawer.STATE_HIDDEN:
            self.drawer.transition_to_bar()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.drawer.schedule_state_check()
        super().leaveEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if self.drawer.is_dragging_out:
            event.ignore()
            return
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drawer.expand_drawer()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if self.drawer.is_dragging_out:
            event.ignore()
            return
        urls = event.mimeData().urls()
        local_files = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if local_files:
            self.drawer.expand_drawer()
            self.drawer.add_files_to_shelf(local_files)
            event.acceptProposedAction()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        painter.end()


# ---------------------------------------------------------------------------
# 9. Gelişmiş Ayarlar Penceresi (Yönler, Tema ve Auto-Start CheckBox)
# ---------------------------------------------------------------------------
class SettingsWindow(QMainWindow):
    def __init__(self, controller: "UniversalFileDropApp"):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Universal File Drop Catcher — Ayarlar")
        self.setFixedSize(530, 650)
        self.setWindowIcon(self.controller.app_icon)

        self._apply_window_stylesheet(self.controller.config.get("theme", "ocean"))
        self._build_ui()
        self.refresh_status_ui()

    def _apply_window_stylesheet(self, theme_key: str):
        spec = get_theme_spec(theme_key)
        accent = spec["accent_primary"]
        accent2 = spec["accent_secondary"]
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: #0B151E;
            }}
            QFrame#cardFrame {{
                background-color: #112230;
                border: 1px solid #1E3A4C;
                border-radius: 14px;
            }}
            QLabel {{
                color: #E2E8F0;
                font-family: 'Segoe UI', 'Sans Serif';
            }}
            QLabel#headerTitle {{
                font-size: 19px;
                font-weight: bold;
                color: #F8FAFC;
            }}
            QLabel#headerSub {{
                font-size: 12px;
                color: {accent};
            }}
            QLabel#sectionTitle {{
                font-size: 13px;
                font-weight: bold;
                color: #F1F5F9;
            }}
            QCheckBox {{
                color: #F8FAFC;
                font-size: 13px;
                font-weight: bold;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 1.5px solid {accent};
                background-color: #0B151E;
            }}
            QCheckBox::indicator:checked {{
                background-color: {accent};
                border: 1.5px solid {accent2};
            }}
            QSpinBox, QComboBox {{
                background-color: #0B151E;
                color: #F8FAFC;
                border: 1px solid {accent};
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 13px;
                font-weight: bold;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #112230;
                color: #F8FAFC;
                selection-background-color: {accent};
                selection-color: #0B151E;
                border: 1px solid {accent};
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: #1E3A4C;
                border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent}, stop:1 {accent2});
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: #F8FAFC;
                border: 2px solid {accent};
                width: 16px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QPushButton {{
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton#startBtn {{
                background-color: #10B981;
                color: #FFFFFF;
                border: none;
            }}
            QPushButton#startBtn:hover {{
                background-color: #059669;
            }}
            QPushButton#startBtn:disabled {{
                background-color: #193242;
                color: #64748B;
            }}
            QPushButton#stopBtn {{
                background-color: #EF4444;
                color: #FFFFFF;
                border: none;
            }}
            QPushButton#stopBtn:hover {{
                background-color: #DC2626;
            }}
            QPushButton#stopBtn:disabled {{
                background-color: #193242;
                color: #64748B;
            }}
            """
        )

    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(22, 16, 22, 16)
        root.setSpacing(10)

        header_title = QLabel("Universal File Drop Catcher")
        header_title.setObjectName("headerTitle")
        header_sub = QLabel(
            "Morf Butonlar, Sıfır Boşluklu Kenar, Yerel Paylaşım ve Dinamik Tema Sistemi."
        )
        header_sub.setObjectName("headerSub")
        root.addWidget(header_title)
        root.addWidget(header_sub)

        # 1. Kart: Dinleme Durumu & Sistem Başlangıcı (Auto-Start)
        status_card = QFrame()
        status_card.setObjectName("cardFrame")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(16, 12, 16, 12)
        status_layout.setSpacing(10)

        top_row = QHBoxLayout()
        sec_status = QLabel("Dinleme Durumu")
        sec_status.setObjectName("sectionTitle")
        self.status_badge = QLabel("● Aktif")
        top_row.addWidget(sec_status)
        top_row.addStretch()
        top_row.addWidget(self.status_badge)
        status_layout.addLayout(top_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.start_btn = QPushButton("▶  Sistemi Başlat")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.controller.start_listening)

        self.stop_btn = QPushButton("■  Sistemi Durdur")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.controller.stop_listening)

        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        status_layout.addLayout(btn_row)

        self.autostart_cb = QCheckBox(
            "🚀  Sistem Başlangıcında Çalıştır (Run on Startup)"
        )
        self.autostart_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.autostart_cb.setChecked(
            bool(self.controller.config.get("run_on_startup", False))
        )
        self.autostart_cb.toggled.connect(self.controller.update_autostart)
        status_layout.addWidget(self.autostart_cb)

        root.addWidget(status_card)

        # 2. Kart: Popup Süresi
        duration_card = QFrame()
        duration_card.setObjectName("cardFrame")
        dur_layout = QVBoxLayout(duration_card)
        dur_layout.setContentsMargins(16, 12, 16, 12)
        dur_layout.setSpacing(8)

        dur_header = QHBoxLayout()
        dur_title = QLabel("Popup Ekranda Kalma Süresi")
        dur_title.setObjectName("sectionTitle")

        current_dur = int(self.controller.config.get("popup_duration_seconds", 10))

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(2, 60)
        self.duration_spin.setSuffix(" sn")
        self.duration_spin.setValue(current_dur)

        dur_header.addWidget(dur_title)
        dur_header.addStretch()
        dur_header.addWidget(self.duration_spin)
        dur_layout.addLayout(dur_header)

        self.duration_slider = QSlider(Qt.Orientation.Horizontal)
        self.duration_slider.setRange(2, 60)
        self.duration_slider.setValue(current_dur)
        dur_layout.addWidget(self.duration_slider)

        self.duration_slider.valueChanged.connect(self.duration_spin.setValue)
        self.duration_spin.valueChanged.connect(self.duration_slider.setValue)
        self.duration_spin.valueChanged.connect(self.controller.update_popup_duration)
        root.addWidget(duration_card)

        # 3. Kart: Tepsi Yönü, Popup Yönü ve Tema Seçimi
        dir_card = QFrame()
        dir_card.setObjectName("cardFrame")
        dir_col = QVBoxLayout(dir_card)
        dir_col.setContentsMargins(16, 12, 16, 12)
        dir_col.setSpacing(10)

        tray_row = QHBoxLayout()
        tray_lbl = QLabel("🗄️  Tepsi (Dropzone) Yönü")
        tray_lbl.setObjectName("sectionTitle")
        self.tray_dir_combo = QComboBox()
        cur_tray_dir = self.controller.config.get("tray_direction", "top")
        tray_idx = 0
        for idx, (label_text, code) in enumerate(DIRECTION_ITEMS):
            self.tray_dir_combo.addItem(label_text, userData=code)
            if code == cur_tray_dir:
                tray_idx = idx
        self.tray_dir_combo.setCurrentIndex(tray_idx)
        self.tray_dir_combo.currentIndexChanged.connect(self._on_tray_dir_changed)
        tray_row.addWidget(tray_lbl)
        tray_row.addStretch()
        tray_row.addWidget(self.tray_dir_combo)
        dir_col.addLayout(tray_row)

        pop_row = QHBoxLayout()
        pop_lbl = QLabel("🔔  Gelen Dosya Popup Yönü")
        pop_lbl.setObjectName("sectionTitle")
        self.popup_dir_combo = QComboBox()
        cur_pop_dir = self.controller.config.get("popup_direction", "top")
        pop_idx = 0
        for idx, (label_text, code) in enumerate(DIRECTION_ITEMS):
            self.popup_dir_combo.addItem(label_text, userData=code)
            if code == cur_pop_dir:
                pop_idx = idx
        self.popup_dir_combo.setCurrentIndex(pop_idx)
        self.popup_dir_combo.currentIndexChanged.connect(self._on_popup_dir_changed)
        pop_row.addWidget(pop_lbl)
        pop_row.addStretch()
        pop_row.addWidget(self.popup_dir_combo)
        dir_col.addLayout(pop_row)

        theme_row = QHBoxLayout()
        theme_lbl = QLabel("🎨  Tema Seçimi")
        theme_lbl.setObjectName("sectionTitle")
        self.theme_combo = QComboBox()
        cur_theme = self.controller.config.get("theme", "ocean")
        theme_idx = 0
        for idx, (label_text, code) in enumerate(THEME_ITEMS):
            self.theme_combo.addItem(label_text, userData=code)
            if code == cur_theme:
                theme_idx = idx
        self.theme_combo.setCurrentIndex(theme_idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(theme_lbl)
        theme_row.addStretch()
        theme_row.addWidget(self.theme_combo)
        dir_col.addLayout(theme_row)

        self.smart_mode_label = QLabel()
        self.smart_mode_label.setStyleSheet(
            "color: #2DD4BF; font-size: 11px; font-weight: bold;"
        )
        dir_col.addWidget(self.smart_mode_label)
        self._update_smart_mode_hint()

        root.addWidget(dir_card)

        # 4. Kart: Bilgi
        info_card = QFrame()
        info_card.setObjectName("cardFrame")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(16, 10, 16, 10)
        info_layout.setSpacing(4)

        watched_count = len(self.controller.watched_dirs)
        self.folders_label = QLabel(
            f"📂 İzlenen kök dizin sayısı: {watched_count} (Alt klasörler dahil)  •  OS: {platform.system()}"
        )
        self.folders_label.setStyleSheet("color: #99F6E4; font-size: 12px;")

        tray_hint = QLabel(
            "💡 Aksiyon butonlarının üzerine gelindiğinde butonlar ve pencere OutBack animasyonuyla genişler. "
            "Üst kenar seçildiğinde y=0 noktasında sıfır boşlukla tetiklenir."
        )
        tray_hint.setWordWrap(True)
        tray_hint.setStyleSheet("color: #64748B; font-size: 11px;")

        info_layout.addWidget(self.folders_label)
        info_layout.addWidget(tray_hint)
        root.addWidget(info_card)

        root.addStretch()

    def _update_smart_mode_hint(self):
        t_dir = self.tray_dir_combo.currentData()
        p_dir = self.popup_dir_combo.currentData()
        if t_dir == p_dir:
            self.smart_mode_label.setText(
                "✨ Akıllı Entegre Mod Aktif: Yeni dosyalar doğrudan Tepsi içinde morf olarak açılır."
            )
            self.smart_mode_label.setStyleSheet(
                "color: #34D399; font-size: 11px; font-weight: bold;"
            )
        else:
            self.smart_mode_label.setText(
                "🔀 Bağımsız Mod Aktif: Tepsi ve Popup kendi seçili kenarlarının ortasında açılır."
            )
            self.smart_mode_label.setStyleSheet(
                "color: #38BDF8; font-size: 11px; font-weight: bold;"
            )

    def _on_tray_dir_changed(self, index: int):
        code = self.tray_dir_combo.itemData(index)
        if code:
            self.controller.update_tray_direction(code)
            self._update_smart_mode_hint()

    def _on_popup_dir_changed(self, index: int):
        code = self.popup_dir_combo.itemData(index)
        if code:
            self.controller.update_popup_direction(code)
            self._update_smart_mode_hint()

    def _on_theme_changed(self, index: int):
        theme_code = self.theme_combo.itemData(index)
        if theme_code:
            self._apply_window_stylesheet(theme_code)
            self.controller.update_theme(theme_code)

    def refresh_status_ui(self):
        if self.controller.is_listening:
            self.status_badge.setText("● Dinleniyor (Aktif)")
            self.status_badge.setStyleSheet(
                "color: #34D399; font-weight: bold; font-size: 13px;"
            )
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:
            self.status_badge.setText("○ Durduruldu (Pasif)")
            self.status_badge.setStyleSheet(
                "color: #F87171; font-weight: bold; font-size: 13px;"
            )
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def closeEvent(self, event: QCloseEvent):
        if self.controller.is_quitting:
            event.accept()
            return

        event.ignore()
        self.hide()
        self.controller.notify_minimized_to_tray()


# ---------------------------------------------------------------------------
# 10. Ana Uygulama Kontrolcüsü
# ---------------------------------------------------------------------------
class UniversalFileDropApp:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.config = load_config()
        if self.config.get("run_on_startup", False):
            set_autostart_enabled(True)

        self.bridge = FileCatcherBridge()
        self.bridge.file_caught.connect(self.spawn_popup)

        self.observer: Optional[Observer] = None
        self.is_listening = False
        self.is_quitting = False
        self._tray_notified_once = False

        self.watched_dirs: List[str] = []
        self.active_popups: List[UniversalDropPopup] = []

        self.app_icon = self._create_app_icon()
        self._collect_watch_directories()
        self.start_listening()

        initial_tray_dir = self.config.get("tray_direction", "top")
        initial_theme = self.config.get("theme", "ocean")
        self.edge_drawer = EdgeDrawer(
            direction=initial_tray_dir, theme_key=initial_theme
        )

        self.settings_win = SettingsWindow(self)
        self._setup_system_tray()

    def _create_app_icon(self) -> QIcon:
        pix = QPixmap(64, 64)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        grad = QLinearGradient(0, 0, 64, 64)
        grad.setColorAt(0.0, QColor("#2DD4BF"))
        grad.setColorAt(1.0, QColor("#0284C7"))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(6, 6, 52, 52, 18, 18)

        painter.setPen(QPen(QColor("#0B151E")))
        painter.setFont(QFont("Sans Serif", 24, QFont.Weight.Bold))
        painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "⬇")
        painter.end()
        return QIcon(pix)

    def _collect_watch_directories(self):
        self.watched_dirs.clear()
        raw_paths = self.config.get("watch_paths", DEFAULT_CONFIG["watch_paths"])
        seen = set()

        for raw_p in raw_paths:
            expanded = Path(os.path.expandvars(os.path.expanduser(raw_p)))
            if expanded.exists() and expanded.is_dir():
                resolved = str(expanded.resolve())
                if resolved not in seen:
                    seen.add(resolved)
                    self.watched_dirs.append(resolved)

    def start_listening(self):
        if self.is_listening:
            return

        self._collect_watch_directories()
        ignore_exts = self.config.get(
            "ignore_extensions", DEFAULT_CONFIG["ignore_extensions"]
        )
        handler = UnifiedDropHandler(ignore_exts=ignore_exts, bridge=self.bridge)

        self.observer = Observer()
        for folder in self.watched_dirs:
            self.observer.schedule(handler, folder, recursive=True)
            print(f"[Watchdog] Dinleniyor (Alt klasörler dahil): {folder}")

        self.observer.start()
        self.is_listening = True

        if hasattr(self, "settings_win"):
            self.settings_win.refresh_status_ui()
        if hasattr(self, "tray_status_action"):
            self.tray_status_action.setText("Durum: ● Aktif")

    def stop_listening(self):
        if not self.is_listening:
            return

        if self.observer is not None:
            try:
                self.observer.stop()
                self.observer.join(timeout=2)
            except Exception as exc:
                print(f"[Watchdog] Durdurma hatası: {exc}")
            self.observer = None

        self.is_listening = False
        print("[Watchdog] Dinleme durduruldu.")

        if hasattr(self, "settings_win"):
            self.settings_win.refresh_status_ui()
        if hasattr(self, "tray_status_action"):
            self.tray_status_action.setText("Durum: ○ Durduruldu")

    def update_popup_duration(self, seconds: int):
        self.config["popup_duration_seconds"] = int(seconds)
        save_config(self.config)

    def update_tray_direction(self, direction: str):
        self.config["tray_direction"] = direction
        save_config(self.config)
        self.edge_drawer.reposition_for_direction(direction)
        print(f"[Config] Tepsi yönü '{direction}' olarak güncellendi.")

    def update_popup_direction(self, direction: str):
        self.config["popup_direction"] = direction
        save_config(self.config)
        print(f"[Config] Popup yönü '{direction}' olarak güncellendi.")

    def update_theme(self, theme_key: str):
        self.config["theme"] = theme_key
        save_config(self.config)
        self.edge_drawer.apply_theme(theme_key)
        for popup in list(self.active_popups):
            popup.apply_theme(theme_key)
        print(f"[Config] Tema '{theme_key}' olarak güncellendi.")

    def update_autostart(self, enabled: bool):
        self.config["run_on_startup"] = bool(enabled)
        save_config(self.config)
        set_autostart_enabled(bool(enabled))
        print(f"[Config] Sistem başlangıcında çalıştırma: {enabled}")

    def _setup_system_tray(self):
        self.tray = QSystemTrayIcon(self.app_icon, self.qt_app)
        self.tray.setToolTip("Universal File Drop Catcher")

        menu = QMenu()
        self.tray_status_action = QAction("Durum: ● Aktif", menu)
        self.tray_status_action.setEnabled(False)
        menu.addAction(self.tray_status_action)
        menu.addSeparator()

        drawer_action = QAction("🗄️  Dosya Rafını Göster", menu)
        drawer_action.triggered.connect(self.edge_drawer.expand_drawer)
        menu.addAction(drawer_action)

        settings_action = QAction("⚙️  Ayarlar", menu)
        settings_action.triggered.connect(self.show_settings_window)
        menu.addAction(settings_action)

        menu.addSeparator()
        quit_action = QAction("🚪  Çıkış", menu)
        quit_action.triggered.connect(self.quit_application)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self.show_settings_window()

    def show_settings_window(self):
        self.settings_win.showNormal()
        self.settings_win.raise_()
        self.settings_win.activateWindow()

    def notify_minimized_to_tray(self):
        if not self._tray_notified_once and self.tray.supportsMessages():
            self.tray.showMessage(
                "Universal File Drop Catcher",
                "Uygulama ve Akıllı Morf Kenar Rafı arka planda çalışmaya devam ediyor.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            self._tray_notified_once = True

    def spawn_popup(
        self,
        file_path: str,
        source_name: str,
        source_icon: str,
        accent_color: str,
    ):
        duration_sec = int(self.config.get("popup_duration_seconds", 10))
        tray_dir = self.config.get("tray_direction", "top")
        popup_dir = self.config.get("popup_direction", "top")
        theme_key = self.config.get("theme", "ocean")

        if tray_dir == popup_dir:
            self.edge_drawer.present_incoming_file(
                file_path=file_path,
                source_name=source_name,
                source_icon=source_icon,
                accent_color=accent_color,
                duration_sec=duration_sec,
            )
            return

        popup = UniversalDropPopup(
            file_path=file_path,
            source_name=source_name,
            source_icon=source_icon,
            accent_color=accent_color,
            duration_sec=duration_sec,
            direction=popup_dir,
            theme_key=theme_key,
            on_add_to_tray=lambda p: self.edge_drawer.add_files_to_shelf([p]),
            stack_index=len(self.active_popups),
        )
        popup.destroyed.connect(lambda: self._on_popup_destroyed(popup))
        self.active_popups.append(popup)
        popup.show()

    def _on_popup_destroyed(self, popup: UniversalDropPopup):
        if popup in self.active_popups:
            self.active_popups.remove(popup)
        gc.collect()

    def quit_application(self):
        self.is_quitting = True
        self.stop_listening()
        for p in list(self.active_popups):
            p.close()
        self.edge_drawer.close_all()
        self.tray.hide()
        self.qt_app.quit()

    def run(self):
        self.show_settings_window()
        sys.exit(self.qt_app.exec())


if __name__ == "__main__":
    app = UniversalFileDropApp()
    app.run()
