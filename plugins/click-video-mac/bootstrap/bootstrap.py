"""NBD Video bootstrap: plain text on purpose, so anyone can read what runs on their computer (user 10/11).

What it does, in order:
1. Speaks MCP (JSON-RPC over stdin/stdout) to the AI client (Claude Code, Codex), with the Python standard library only.
2. Activates the key from the plugin's settings (CLICK_LICENSE) with the licence server: the server answers with a token.
3. Asks the server for the engine. The answer is a manifest SIGNED with the server's Ed25519 key; the public key is in
   config.json next to this file. The signature is checked here (pure Python, below) before anything is downloaded.
4. Downloads the libraries the manifest lists from PyPI (each checked against its SHA-256) and the engine itself from the
   licence server, with a short-lived link bound to this computer (checked against the signed SHA-256).
   Before that, the Licence Agreement in force must be accepted (first key, or a new version): the server refuses rules and
   engine until then. The text is shown in Claude Code's own confirmation box when it has one (MCP elicitation), else
   through two tools Claude may call only on the user's own words.
5. Loads the engine (compiled Python modules) and hands the AI's tool calls to it. At every start: a newer engine replaces the
   old one (same checks); offline, the installed engine is used, re-checked against its signed manifest.
Nothing else is downloaded or run here. Files: %CLAUDE_PLUGIN_DATA% or %PLUGIN_DATA% (Codex), else %LOCALAPPDATA%\\ClickVideo
(Windows) or ~/Library/Application Support/ClickVideo (Mac).
Same bootstrap for Claude Code and Codex, Windows and macOS (user 10/11, 11/11): the key comes from the plugin's settings
(Claude Code), the CLICK_LICENSE_KEY variable, or the kich_hoat tool (asked in the chat, kept for this user only: DPAPI on
Windows, the login Keychain on the Mac).
Usage: start.cmd serve | start.cmd cli <wait|status|activate KEY>   (Mac: sh start.sh …)
"""
import base64
import concurrent.futures
import ctypes
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
SERVER = os.environ.get("CLICK_SERVER") or CONFIG["server"]   # an override can only point at a server that signs with the same key
PUBLIC_KEY = bytes.fromhex(CONFIG["public_key"])
MAC = sys.platform == "darwin"
OS = "mac" if MAC else "win"  # the server sends the engine and the libraries built for this system
HOME_DIR = (os.path.join(os.path.expanduser("~"), "Library", "Application Support", "ClickVideo") if MAC else
            os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ClickVideo"))
POINTER = os.path.join(HOME_DIR, "plugin-data.txt")  # Mac: where the AI client keeps our data (UTF-8 text, read by start.sh)
LINK = os.path.join(HOME_DIR, "data")                 # Windows: a junction to it (start.cmd cannot read letters like ộ from a file)


def _pointed():
    """Where the AI client keeps our data, for click-engine run from a terminal (11/11: the terminal is not told)."""
    try:
        if MAC:
            p = open(POINTER, encoding="utf-8").read().strip()
        else:
            p = os.path.realpath(LINK) if os.path.isjunction(LINK) else ""
        return p if p and os.path.isdir(p) else ""
    except OSError:
        return ""


DATA = os.environ.get("CLAUDE_PLUGIN_DATA") or os.environ.get("PLUGIN_DATA") or _pointed() or HOME_DIR


def remember_data():
    """The AI client tells only the plugin's own process where its data is (CLAUDE_PLUGIN_DATA / PLUGIN_DATA). A terminal it
    opens later (click-engine wait, run by the AI for the Brief form) does not get it: noted here at every start. Windows: the
    junction %LOCALAPPDATA%\\ClickVideo\\data (an ASCII path start.cmd can use whatever the user's name); Mac: a text file."""
    if not (os.environ.get("CLAUDE_PLUGIN_DATA") or os.environ.get("PLUGIN_DATA")):
        return
    try:
        os.makedirs(HOME_DIR, exist_ok=True)
        if MAC:
            with open(POINTER, "w", encoding="utf-8") as f:
                f.write(DATA)
            return
        if os.path.isjunction(LINK) and os.path.normcase(os.path.realpath(LINK)) == os.path.normcase(os.path.realpath(DATA)):
            return
        if os.path.isjunction(LINK):
            os.rmdir(LINK)  # removes the link only
        if not os.path.exists(LINK):
            subprocess.run(["cmd", "/d", "/c", "mklink", "/J", LINK, DATA], capture_output=True)
    except OSError as e:
        log("không ghi được chỉ dẫn thư mục dữ liệu:", e)
RUNTIME = os.path.join(DATA, "runtime")
SITE = os.path.join(RUNTIME, "lib", "python3.12", "site-packages") if MAC else os.path.join(RUNTIME, "Lib", "site-packages")
ENGINES = os.path.join(DATA, "engine")
UA = "click-bootstrap/" + CONFIG.get("version", "1")


def log(*a):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + " ".join(str(x) for x in a)
    try:
        with open(os.path.join(DATA, "bootstrap.log"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    sys.stderr.write(line + "\n")


# ---------------------------------------------------------------- Ed25519 signature check (RFC 8032, section 6, verify only)
_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_I = pow(2, (_P - 1) // 4, _P)


def _recover_x(y, sign):
    if y >= _P:
        return None
    x2 = (y * y - 1) * pow(_D * y * y + 1, _P - 2, _P)
    if x2 % _P == 0:
        return None if sign else 0
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P:
        x = x * _I % _P
    if (x * x - x2) % _P:
        return None
    return _P - x if (x & 1) != sign else x


_GY = 4 * pow(5, _P - 2, _P) % _P
_GX = _recover_x(_GY, 0)
_G = (_GX, _GY, 1, _GX * _GY % _P)


def _add(p, q):
    a, b = (p[1] - p[0]) * (q[1] - q[0]) % _P, (p[1] + p[0]) * (q[1] + q[0]) % _P
    c, d = 2 * p[3] * q[3] * _D % _P, 2 * p[2] * q[2] % _P
    e, f, g, h = b - a, d - c, d + c, b + a
    return e * f % _P, g * h % _P, f * g % _P, e * h % _P


def _mul(s, p):
    q = (0, 1, 1, 0)
    while s:
        if s & 1:
            q = _add(q, p)
        p, s = _add(p, p), s >> 1
    return q


def _point(b):
    y = int.from_bytes(b, "little")
    x = _recover_x(y & ((1 << 255) - 1), y >> 255)
    return None if x is None else (x, y & ((1 << 255) - 1), 1, x * (y & ((1 << 255) - 1)) % _P)


def ed25519_verify(pub, msg, sig):
    if len(pub) != 32 or len(sig) != 64:
        return False
    a, r = _point(pub), _point(sig[:32])
    s = int.from_bytes(sig[32:], "little")
    if a is None or r is None or s >= _L:
        return False
    h = int.from_bytes(hashlib.sha512(sig[:32] + pub + msg).digest(), "little") % _L
    p, q = _mul(s, _G), _add(r, _mul(h, a))
    return (p[0] * q[2] - q[0] * p[2]) % _P == 0 and (p[1] * q[2] - q[1] * p[2]) % _P == 0


def b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def signed_part(m):
    """What the server signed: everything but the per-request link and the signature itself."""
    return json.dumps({k: m[k] for k in ("version", "file", "sha256", "size", "wheels")}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def check_manifest(m):
    if not ed25519_verify(PUBLIC_KEY, signed_part(m), b64d(m.get("sig", ""))):
        raise RuntimeError("Chữ ký của bộ máy không hợp lệ: đã dừng, không tải gì.")


# ---------------------------------------------------------------- the licence server
def _out(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def machine_id():
    """Same as the engine (click_engine/plat.py): a hash of this install and its hardware, never the raw values.
    Windows: the registry. Mac: the platform UUID (ioreg), the model and the chip (sysctl)."""
    if MAC:
        m = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', _out(["/usr/sbin/ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]))
        vals = ["mac", m.group(1) if m else "", _out(["/usr/sbin/sysctl", "-n", "hw.model"]).strip(),
                _out(["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"]).strip()]
        return hashlib.sha256("|".join(vals).encode()).hexdigest()[:32]
    import winreg
    vals = []
    for sub, name in ((r"SOFTWARE\Microsoft\Cryptography", "MachineGuid"), (r"HARDWARE\DESCRIPTION\System\BIOS", "BaseBoardManufacturer"),
                      (r"HARDWARE\DESCRIPTION\System\BIOS", "BaseBoardProduct"), (r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", "ProcessorNameString")):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
                vals.append(str(winreg.QueryValueEx(k, name)[0]))
        except OSError:
            vals.append("")
    return hashlib.sha256("|".join(vals).encode()).hexdigest()[:32]


class Refused(Exception):
    pass


class NoKey(Refused):
    pass


class NeedEula(Refused):
    def __init__(self, msg, version):
        super().__init__(msg)
        self.version = version


def http(url, payload=None, token=None, timeout=60):
    headers = {"User-Agent": UA, "Content-Type": "application/json", "X-Click-Machine": machine_id(), "X-Click-OS": OS}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except ValueError:
            body = {}
        if body.get("eula"):
            raise NeedEula(body.get("error", ""), body["eula"]) from e
        raise Refused(body.get("error") or f"Máy chủ trả lỗi {e.code}") from e


def token_path():
    return os.path.join(DATA, "licence.tok")


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi(data, protect):
    """Windows' own per-user encryption (DPAPI): the key file opens only for this Windows account on this machine."""
    src = _Blob(len(data), ctypes.cast(ctypes.create_string_buffer(data, len(data)), ctypes.POINTER(ctypes.c_char)))
    out = _Blob()
    fn = ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData
    if not fn(ctypes.byref(src), None, None, None, None, 0, ctypes.byref(out)):
        raise OSError("DPAPI")
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out.pbData)


def key_path():
    return os.path.join(DATA, "key.dat")


KEYCHAIN = "CLICK Video"


def read_secret(path):
    """What keep_key stored: DPAPI on Windows; on the Mac the login Keychain (the file only says where), else the file itself."""
    if not MAC:
        return _dpapi(open(path, "rb").read(), False).decode()
    mark = open(path, encoding="utf-8").read()
    if mark.startswith("plain:"):
        return mark[6:]
    r = subprocess.run(["/usr/bin/security", "find-generic-password", "-a", os.path.basename(path), "-s", KEYCHAIN, "-w"], capture_output=True, text=True)
    if r.returncode:
        raise OSError("Keychain")
    return r.stdout.strip()


def write_secret(path, text):
    if not MAC:
        with open(path, "wb") as f:
            f.write(_dpapi(text.encode(), True))
        return
    r = subprocess.run(["/usr/bin/security", "add-generic-password", "-U", "-a", os.path.basename(path), "-s", KEYCHAIN, "-w", text], capture_output=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("keychain" if r.returncode == 0 else "plain:" + text)
    os.chmod(path, 0o600)


def given_key():
    """The key: the plugin's settings (Claude Code), CLICK_LICENSE_KEY, or the one entered with kich_hoat. An option left
    empty may arrive as the raw "${user_config.license_key}": that is no key."""
    for name in ("CLICK_LICENSE", "CLICK_LICENSE_KEY"):
        v = os.environ.get(name, "").strip()
        if v and not v.startswith("${"):
            return v.upper()
    try:
        return read_secret(key_path()).strip().upper()
    except (OSError, UnicodeDecodeError):
        return ""


def keep_key(key):
    write_secret(key_path(), key)


KEY_FORM = re.compile(r"^CLK-[A-Z2-9]{5}-[A-Z2-9]{5}-[A-Z2-9]{5}-[A-Z2-9]{5}$")


def activate(key=None):
    key = (key or given_key()).strip().upper()
    if not key:
        raise NoKey("Chưa có key bản quyền. Hỏi người dùng key (dạng CLK-XXXXX-XXXXX-XXXXX-XXXXX) rồi gọi kich_hoat.")
    tok = json.loads(http(SERVER + "/v1/activate", {"key": key, "mid": machine_id(), "ver": UA, "host": os.environ.get("COMPUTERNAME") or __import__("socket").gethostname()}))["token"]
    with open(token_path(), "w", encoding="utf-8") as f:
        f.write(tok)
    os.environ["CLICK_LICENSE"] = key  # the engine renews with it later (same process)
    return tok


def manifest():
    tok = open(token_path(), encoding="utf-8").read().strip() if os.path.exists(token_path()) else activate()
    try:
        m = json.loads(http(SERVER + "/v1/engine", token=tok))
    except NeedEula:
        raise
    except Refused:
        try:  # an old token: the server renews it for this machine, else the key is activated again
            tok = json.loads(http(SERVER + "/v1/refresh", {"mid": machine_id(), "ver": UA}, token=tok))["token"]
            with open(token_path(), "w", encoding="utf-8") as f:
                f.write(tok)
        except Refused:
            tok = activate()
        m = json.loads(http(SERVER + "/v1/engine", token=tok))
    check_manifest(m)
    return m


# ---------------------------------------------------------------- installing what the signed manifest lists
def fetch(url, sha256, token=None):
    data = http(url, token=token, timeout=600)
    if hashlib.sha256(data).hexdigest() != sha256.lower():
        raise RuntimeError(f"Mã kiểm tra sai: {url.rsplit('/', 1)[-1]}. Không dùng tệp này.")
    return data


def install_wheels(m):
    """Libraries the engine imports (cryptography…), from PyPI, unpacked into site-packages (a wheel is a zip)."""
    os.makedirs(SITE, exist_ok=True)
    for w in m["wheels"]:
        mark = os.path.join(SITE, ".click-" + w["file"] + ".ok")
        if os.path.exists(mark):
            continue
        log("tải thư viện", w["file"])
        with zipfile.ZipFile(io.BytesIO(fetch(w["url"], w["sha256"]))) as z:
            z.extractall(SITE)
        open(mark, "w").close()


def install_engine(m):
    tok = open(token_path(), encoding="utf-8").read().strip()
    data = fetch(SERVER + m["url"], m["sha256"], token=tok)
    if len(data) != m["size"]:
        raise RuntimeError("Kích thước bộ máy không khớp.")
    dest = os.path.join(ENGINES, m["version"])
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    with open(dest + ".zip", "wb") as f:
        f.write(data)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(dest)
    with open(os.path.join(ENGINES, "current.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False)
    for old in os.listdir(ENGINES):  # one engine kept, plus nothing else of ours
        p = os.path.join(ENGINES, old)
        if old not in (m["version"], m["version"] + ".zip", "current.json"):
            shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)
    log("đã cài bộ máy", m["version"])


def installed():
    """The engine on disk, re-checked: its manifest's signature, the zip's hash, and each unpacked file against the zip."""
    p = os.path.join(ENGINES, "current.json")
    if not os.path.exists(p):
        return None
    m = json.load(open(p, encoding="utf-8"))
    check_manifest(m)
    z = os.path.join(ENGINES, m["version"] + ".zip")
    data = open(z, "rb").read()
    if hashlib.sha256(data).hexdigest() != m["sha256"]:
        raise RuntimeError("Bộ máy trên máy đã bị thay đổi: cần tải lại (kết nối mạng).")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist():
            f = os.path.join(ENGINES, m["version"], info.filename)
            if not info.is_dir() and (not os.path.exists(f) or open(f, "rb").read() != zf.read(info)):
                raise RuntimeError("Bộ máy trên máy đã bị thay đổi: cần tải lại (kết nối mạng).")
    return m


def token():
    return open(token_path(), encoding="utf-8").read().strip()


def eula_text():
    return json.loads(http(SERVER + "/v1/eula", token=token()))


def eula_accept(version, how):
    http(SERVER + "/v1/eula", {"version": version, "agree": True, "how": how}, token=token())
    log("đã đồng ý thoả thuận", version, "qua", how)


LICENSE_FILE = os.path.normpath(os.path.join(HERE, "..", "LICENSE.md"))


def note_runtime():
    """The installer of the engine must not unpack Python again: this one is the same official build."""
    p = os.path.join(DATA, "installed.json")
    done = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    if done.get("python") != CONFIG["python"]:
        done["python"] = CONFIG["python"]
        json.dump(done, open(p, "w", encoding="utf-8"))


PENDING = os.path.join(DATA, "ban-moi.json")   # a newer version waiting for the customer's yes (read by the engine and the Brief form)
REFRESH_FLAG = os.path.join(DATA, "cap-nhat.flag")  # a new engine is in: its pack (app/) is refreshed by cai_dat at the next start


def set_pending(info):
    if info:
        json.dump(info, open(PENDING, "w", encoding="utf-8"), ensure_ascii=False)
    elif os.path.exists(PENDING):
        os.remove(PENDING)


def pending():
    try:
        return json.load(open(PENDING, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def watch_updates(every=86400):
    """While the plugin runs, look for a newer version once a day (user 12/11, besides the check at every start: a customer who keeps one chat open never
    started a new one, so the check at start never ran and the Brief form showed nothing). Only noted, never installed here."""
    while True:
        time.sleep(every)
        try:
            m = manifest()
            cur = json.load(open(os.path.join(ENGINES, "current.json"), encoding="utf-8"))["version"]
            if cur != m["version"]:
                set_pending({"phien_ban": m["version"], "dang_dung": cur, "ghi_chu": m.get("ghi_chu", ""), "luc": time.strftime("%d/%m/%Y")})
        except Exception as e:  # noqa: BLE001  (offline or a bad answer: try again next time)
            log("kiểm tra bản mới:", e)


def prepare():
    """The engine module: the installed one; a newer one on the server is only noted (ban-moi.json) and installed when the
    customer agrees (tool cap_nhat), unless the server marks it mandatory. First start: the server's one."""
    os.makedirs(ENGINES, exist_ok=True)
    note_runtime()
    try:
        m = manifest()
        cur = None
        try:
            cur = installed()
        except RuntimeError as e:
            log(e)
        install_wheels(m)
        fresh = not os.path.isdir(os.path.join(DATA, "app", "scripts"))  # not installed yet: no project to protect, take the fixed one
        if not cur or (cur["version"] != m["version"] and (m.get("bat_buoc") or fresh)):
            log("bộ máy mới", m["version"], "(đang có", cur and cur["version"], ")")
            install_engine(m)
            set_pending(None)
        elif cur["version"] != m["version"]:  # never switched under a customer's running project (user 11/11): told, applied on their yes
            set_pending({"phien_ban": m["version"], "dang_dung": cur["version"], "ghi_chu": m.get("ghi_chu", ""), "luc": time.strftime("%d/%m/%Y")})
        else:
            set_pending(None)
    except (OSError, urllib.error.URLError) as e:  # offline: the installed engine checks its own licence (7 days)
        log("không kết nối được máy chủ:", e)
    m = installed()
    if not m:
        raise RuntimeError("Chưa có bộ máy: cần kết nối mạng lần đầu.")
    for p in (SITE, os.path.join(ENGINES, m["version"])):
        if p not in sys.path:
            sys.path.insert(0, p)
    import importlib
    importlib.invalidate_caches()
    from click_engine import server  # noqa: E402  (the engine checks its licence again on each call)
    return server, m["version"]


# ---------------------------------------------------------------- MCP over stdio
class Mcp:
    def __init__(self):
        self.out = sys.stdout.buffer
        self.lock = threading.Lock()
        self.engine, self.version, self.state, self.error = None, None, "đang chuẩn bị", ""
        self.pool = concurrent.futures.ThreadPoolExecutor(8)
        self.ready = False
        self.initialized = threading.Event()
        self.client_caps = {}
        self.pending, self.next_id = {}, 0
        self.eula = None  # the agreement waiting for the user's yes
        self.need_key = False

    def ask_client(self, method, params, timeout=1800):
        """A request from us to Claude Code (elicitation): its answer arrives on stdin like any message."""
        with self.lock:
            self.next_id += 1
            rid = f"click-{self.next_id}"
        fut = concurrent.futures.Future()
        self.pending[rid] = fut
        self.send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        return fut.result(timeout=timeout)

    def ask_roots(self):
        """The project folder the AI client is working in (Codex starts us in the plugin's own folder): its first root,
        unless the client already said (Claude Code's CLICK_WORKSPACE)."""
        cur = os.environ.get("CLICK_WORKSPACE", "")
        if cur and not cur.startswith("${"):
            return
        try:
            roots = (self.ask_client("roots/list", {}, timeout=30) or {}).get("roots") or []
        except Exception as e:  # noqa: BLE001
            log("không lấy được thư mục dự án:", e)
            return
        for r in roots:
            uri = r.get("uri", "")
            if uri.startswith("file:"):
                import urllib.parse
                path = urllib.request.url2pathname(urllib.parse.urlparse(uri).path)
                os.environ["CLICK_WORKSPACE"] = path.lstrip("\\") if re.match(r"^\\[A-Za-z]:", path) else path
                log("thư mục dự án:", os.environ["CLICK_WORKSPACE"])
                return

    def agree_flow(self, need):
        """Show the agreement and wait for the user's own yes: Claude Code's confirmation box when it has one."""
        self.eula = eula_text()
        self.state, self.error = "cần đồng ý thoả thuận", str(need)
        if self.ready:
            self.send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
        self.initialized.wait(60)
        if "elicitation" not in self.client_caps:
            return False
        e = self.eula
        msg = (f"{e.get('notice_vi', '')}\n\nThoả thuận cấp phép phiên bản {e['version']}: toàn văn ở {LICENSE_FILE}\n\n"
               f"{e.get('short_en', '')} Full Licence Agreement: {LICENSE_FILE}")
        r = self.ask_client("elicitation/create", {"message": msg, "requestedSchema": {"type": "object", "properties": {
            "dong_y": {"type": "boolean", "title": f"Tôi đã đọc và đồng ý Thoả thuận cấp phép phiên bản {e['version']} / I accept the Licence Agreement",
                       "default": False}}, "required": ["dong_y"]}})
        if r.get("action") == "accept" and (r.get("content") or {}).get("dong_y") is True:
            eula_accept(e["version"], "elicitation")
            return True
        self.state, self.error = "chưa đồng ý thoả thuận", "Người dùng chưa đồng ý. Gọi xem_thoa_thuan để xem lại."
        return False

    def setup_form(self):
        """First start, no key yet: ONE box asks for the key, the folders and the consent to the agreement (user 11/11: no
        separate boxes). Only where the AI client has a confirmation box (MCP elicitation, Claude Code); elsewhere (Codex)
        the AI asks in the chat with kich_hoat and the agreement tools, as before. Returns True when activated and agreed."""
        self.initialized.wait(60)
        if "elicitation" not in self.client_caps:
            return False
        try:
            e = json.loads(http(SERVER + "/v1/eula/public"))
        except (Refused, OSError, ValueError) as ex:
            log("không lấy được thoả thuận:", ex)
            return False
        note = ""
        for _ in range(3):
            msg = (f"{note}NBD Video: kích hoạt trên máy này.\n\n{e.get('notice_vi', '')}\n\n"
                   f"Thoả thuận cấp phép phiên bản {e.get('version')}: toàn văn ở {LICENSE_FILE}\n{e.get('short_en', '')}")
            r = self.ask_client("elicitation/create", {"message": msg, "requestedSchema": {"type": "object", "properties": {
                "key": {"type": "string", "title": "Key bản quyền", "description": "Dạng CLK-XXXXX-XXXXX-XXXXX-XXXXX, nhận khi mua."},
                "thu_muc_du_an": {"type": "string", "title": "Thư mục lưu dự án (tuỳ chọn)",
                                  "description": "Đường dẫn đầy đủ. Để trống: thư mục bạn đang mở trợ lý AI."},
                "thu_muc_ban_nhap_capcut": {"type": "string", "title": "Thư mục bản nháp CapCut (tuỳ chọn)",
                                            "description": "Để trống: đúng thư mục bạn đã chọn trong CapCut."},
                "dong_y": {"type": "boolean", "title": f"Tôi đã đọc và đồng ý Thoả thuận cấp phép phiên bản {e.get('version')} / I accept the Licence Agreement",
                           "default": False}}, "required": ["key", "dong_y"]}})
            if r.get("action") != "accept":
                return False
            c = r.get("content") or {}
            key = str(c.get("key", "")).strip().upper()
            if not KEY_FORM.match(key):
                note = "Key chưa đúng dạng CLK-XXXXX-XXXXX-XXXXX-XXXXX. Nhập lại.\n\n"
                continue
            if c.get("dong_y") is not True:
                note = "Cần đánh dấu đồng ý Thoả thuận cấp phép để dùng.\n\n"
                continue
            try:
                activate(key)
            except Refused as ex:
                note = f"Máy chủ không nhận key: {ex}\n\n"
                continue
            keep_key(key)
            eula_accept(e["version"], "form")
            folders = {k: str(c.get(f, "")).strip() for k, f in (("lam_viec", "thu_muc_du_an"), ("ban_nhap", "thu_muc_ban_nhap_capcut"))}
            folders = {k: v for k, v in folders.items() if v and os.path.isabs(v)}
            if folders:  # the engine reads them from settings.json (config.settings, same as its chon_thu_muc tool)
                p = os.path.join(DATA, "settings.json")
                cur = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
                json.dump({**cur, **folders}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            log("đã kích hoạt và đồng ý qua một hộp hỏi")
            return True
        return False

    def send(self, msg):
        with self.lock:
            self.out.write(json.dumps(msg, ensure_ascii=False).encode() + b"\n")
            self.out.flush()

    def load(self):
        try:
            try:
                self.engine, self.version = prepare()
            except NeedEula as need:
                if not self.agree_flow(need):
                    return  # waits for dong_y_thoa_thuan
                self.engine, self.version = prepare()
            except NoKey as e:
                self.state = "chờ người dùng nhập key"
                if self.setup_form():
                    self.engine, self.version = prepare()
                    self.eula, self.state, self.error = None, "sẵn sàng", ""
                    if self.ready:
                        self.send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
                    return
                self.need_key, self.state, self.error = True, "cần key bản quyền", str(e)
                if self.ready:
                    self.send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
                return
            self.eula, self.state, self.error = None, "sẵn sàng", ""
            if self.ready:
                self.send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
        except Exception as e:  # noqa: BLE001 — told to Claude through trang_thai
            self.state, self.error = "lỗi", str(e)
            log("lỗi chuẩn bị:", traceback.format_exc())

    UPDATE_TOOL = {"name": "cap_nhat", "description": "Có bản NBD Video mới (xem trang_thai › ban_moi). Báo khách ngay khi thấy, kèm lời khuyên: "
                   "làm xong dự án đang dở rồi hãy cập nhật, dự án đã làm vẫn giữ nguyên. CHỈ gọi khi chính khách đồng ý cập nhật; không tự gọi. "
                   "Từ chối khi đang có việc dựng chạy. Sau khi gọi: dặn khách mở phiên mới, ở phiên mới gọi cai_dat để cập nhật phần dựng.",
                   "inputSchema": {"type": "object", "properties": {}}}

    def update_now(self):
        try:
            from click_engine import runner
            if any(j.get("state") == "running" for j in runner.JOBS.values()):
                return "Đang có việc dựng chạy: chờ xong rồi mới cập nhật.", True
        except Exception:  # noqa: BLE001
            pass
        m = manifest()  # a fresh, signed manifest and download link
        install_wheels(m)
        install_engine(m)
        set_pending(None)
        open(REFRESH_FLAG, "w").close()
        log("khách đồng ý cập nhật lên", m["version"])
        return (f"Đã tải bản {m['version']}. Để dùng: đóng phiên này và mở phiên mới của trợ lý AI. Ở phiên mới, trợ lý cài nốt phần dựng "
                "(vài phút, có báo tiến độ). Dự án và thư viện của khách giữ nguyên."), False

    def tools(self):
        if self.engine:
            out = [{"name": n, "description": d, "inputSchema": s} for n, _, d, s in self.engine.TOOLS]
            return out + ([self.UPDATE_TOOL] if pending() else [])
        out = [{"name": "trang_thai", "description": "Tình trạng của plugin: đang tải bộ máy, cần đồng ý thoả thuận, lỗi giấy phép hay đã sẵn sàng. Gọi đầu tiên mỗi phiên.",
                "inputSchema": {"type": "object", "properties": {}}}]
        if self.need_key:
            out.append({"name": "kich_hoat", "description": "Nhập key bản quyền do người dùng cung cấp (dạng CLK-XXXXX-XXXXX-XXXXX-XXXXX) để kích hoạt plugin trên máy này. "
                        "Hỏi người dùng key khi trang_thai báo chưa có key; không tự đoán key.",
                        "inputSchema": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}})
        if self.eula:
            out += [{"name": "xem_thoa_thuan", "description": "Toàn văn Thoả thuận cấp phép đang chờ người dùng đồng ý (tiếng Việt là bản gốc, kèm bản tiếng Anh). "
                     "Đưa nguyên văn cho người dùng đọc, không tóm tắt thay.", "inputSchema": {"type": "object", "properties": {}}},
                    {"name": "dong_y_thoa_thuan", "description": "Ghi nhận người dùng ĐÃ ĐỒNG Ý Thoả thuận cấp phép. Chỉ gọi khi chính người dùng vừa gõ rằng họ đồng ý "
                     "sau khi đã được cho xem thoả thuận; tuyệt đối không tự đồng ý thay người dùng. cau_tra_loi: nguyên văn câu người dùng gõ.",
                     "inputSchema": {"type": "object", "properties": {"cau_tra_loi": {"type": "string"}}, "required": ["cau_tra_loi"]}}]
        return out

    def call(self, name, args):
        if self.engine and name == "cap_nhat" and pending():
            return self.update_now()
        if self.engine:
            fn = next((f for n, f, _, _ in self.engine.TOOLS if n == name), None)
            if fn:
                r = fn(**(args or {}))
                if name == "trang_thai" and isinstance(r, dict) and pending():
                    r["ban_moi"] = {**pending(), "huong_dan": "Báo khách có bản mới; khuyên làm xong dự án đang dở rồi mới cập nhật. "
                                    "Khách đồng ý thì gọi cap_nhat."}
                return r if isinstance(r, str) else json.dumps(r, ensure_ascii=False), False
        if name == "kich_hoat" and self.need_key:
            key = str((args or {}).get("key", "")).strip().upper()
            if not KEY_FORM.match(key):
                return "Key không đúng dạng CLK-XXXXX-XXXXX-XXXXX-XXXXX. Hỏi lại người dùng.", True
            try:
                activate(key)
            except Refused as e:
                return f"Máy chủ không nhận key này: {e}", True
            keep_key(key)
            log("đã kích hoạt key trên máy này")
            self.need_key, self.state, self.error = False, "đang chuẩn bị", ""
            threading.Thread(target=self.load, daemon=True).start()
            return "Đã kích hoạt. Bộ máy đang tải; nếu cần đồng ý Thoả thuận cấp phép, công cụ sẽ hiện ngay sau đây.", False
        if name == "xem_thoa_thuan" and self.eula:
            e = self.eula
            return f"THOẢ THUẬN CẤP PHÉP, phiên bản {e['version']} (tệp: {LICENSE_FILE})\n\n{e.get('notice_vi', '')}\n\n{e.get('text_vi', '')}\n\n---\n\n{e.get('text_en', '')}", False
        if name == "dong_y_thoa_thuan" and self.eula:
            said = str((args or {}).get("cau_tra_loi", "")).strip()
            if not said:
                return "Cần nguyên văn câu người dùng đồng ý.", True
            eula_accept(self.eula["version"], "tool")
            log("câu đồng ý của người dùng:", said[:200])
            self.eula, self.state = None, "đang chuẩn bị"
            threading.Thread(target=self.load, daemon=True).start()
            return "Đã ghi nhận đồng ý. Bộ máy đang tải; danh sách công cụ tự cập nhật trong giây lát.", False
        if name == "trang_thai":
            return json.dumps({"bo_khoi_dong": self.state, "loi": self.error, "ghi_chu": "Bộ máy tải xong thì danh sách công cụ tự cập nhật."}, ensure_ascii=False), False
        return f"Bộ máy chưa sẵn sàng ({self.state}{': ' + self.error if self.error else ''}). Gọi trang_thai.", True

    def handle(self, msg):
        mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
        try:
            if method == "initialize":
                self.client_caps = params.get("capabilities") or {}
                result = {"protocolVersion": params.get("protocolVersion", "2025-06-18"), "capabilities": {"tools": {"listChanged": True}},
                          "serverInfo": {"name": "click-video", "version": CONFIG.get("version", "1")},
                          "instructions": self.engine.INSTRUCTIONS if self.engine else
                          "Bộ máy dựng video CLICK. Gọi trang_thai trước; khi bộ máy tải xong, danh sách công cụ tự cập nhật. Trả lời người dùng bằng tiếng Việt."}
            elif method == "notifications/initialized":
                self.ready = True
                self.initialized.set()
                if "roots" in self.client_caps:
                    threading.Thread(target=self.ask_roots, daemon=True).start()
                if self.need_key:
                    self.send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
                if self.eula:
                    self.send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
                return
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": self.tools()}
            elif method == "tools/call":
                text, err = self.call(params.get("name"), params.get("arguments"))
                result = {"content": [{"type": "text", "text": text}], "isError": err}
            elif mid is None:
                return  # other notifications
            else:
                self.send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "Method not found: " + str(method)}})
                return
        except Exception as e:  # noqa: BLE001
            log("lỗi công cụ:", traceback.format_exc())
            result = {"content": [{"type": "text", "text": "LỖI: " + str(e)}], "isError": True}
        if mid is not None:
            self.send({"jsonrpc": "2.0", "id": mid, "result": result})

    def run(self):
        threading.Thread(target=self.load, daemon=True).start()
        threading.Thread(target=watch_updates, daemon=True).start()
        for raw in sys.stdin.buffer:
            raw = raw.strip()
            if not raw:
                continue
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            for m in msg if isinstance(msg, list) else [msg]:
                if "method" not in m and m.get("id") in self.pending:  # Claude Code's answer to our request
                    fut = self.pending.pop(m["id"])
                    fut.set_result(m.get("result") or {"action": "cancel", "error": m.get("error")})
                    continue
                self.pool.submit(self.handle, m)
        self.pool.shutdown(wait=False, cancel_futures=True)


def drop_old_runtime():
    """start.cmd / start.sh swapped in the Python copied to the customer's other drive; the old one goes (in the background)."""
    old = os.path.join(DATA, "runtime.old")
    if not os.path.lexists(old):
        return
    try:
        if os.path.islink(old) or (not MAC and os.path.isjunction(old)):  # it already lived on another drive: delete that copy, then the link
            target = os.path.realpath(old)
            os.remove(old) if MAC else os.rmdir(old)
            shutil.rmtree(target, ignore_errors=True)
        else:
            shutil.rmtree(old, ignore_errors=True)
        log("đã xoá bản Python cũ sau khi chuyển dữ liệu")
    except OSError as e:
        log(f"chưa xoá được bản Python cũ: {e}")


def main(argv):
    os.makedirs(DATA, exist_ok=True)
    cmd = argv[1] if len(argv) > 1 else "serve"
    threading.Thread(target=drop_old_runtime, daemon=True).start()
    if cmd == "serve":
        remember_data()
        Mcp().run()
        return 0
    if cmd == "cli":  # click-engine wait | status | activate
        os.environ.setdefault("CLAUDE_PLUGIN_DATA", DATA)  # the engine finds the same folder (from plugin-data.txt in a terminal)
        try:
            server, _ = prepare()
        except NeedEula as e:
            sys.stderr.write(f"CLICK: {e} Mở trợ lý AI có cài plugin và nhắn bất kỳ yêu cầu dựng video nào để xem và đồng ý.\n")
            return 3
        return server.cli(["click-engine", *argv[2:]])
    sys.stderr.write(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
