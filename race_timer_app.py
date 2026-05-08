"""
╔══════════════════════════════════════════════════════════════╗
║          RACE TIMER PRO — v4.1 (Legendary Edition)           ║
║  تطبيق Python كامل مع Serial ثنائي الاتجاه                 ║
║  تم التعديل لإضافة مظهر أسطوري واستخدام الأيقونة المخصصة     ║
╚══════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading, time, csv, os, sys, winsound, json, re
from datetime import datetime
from PIL import Image, ImageTk

try:
    import serial
    import serial.tools.list_ports
    SERIAL_OK = True
except ImportError:
    SERIAL_OK = False

# ═══════════════════════════════════════════════
#  الألوان والخطوط (Legendary Theme)
# ═══════════════════════════════════════════════
DARK_THEME = {
    "bg":      "#05070A",
    "panel":   "#0A0F16",
    "card":    "#111823",
    "card2":   "#18222F",
    "border":  "#1E293B",
    "accent":  "#00D1FF",
    "green":   "#00FF85",
    "green2":  "#00B35D",
    "red":     "#FF3A3A",
    "amber":   "#FFB020",
    "purple":  "#9066FF",
    "muted":   "#4A5568",
    "dim":     "#0F172A",
    "gold":    "#FFD700",
    "text":    "#F1F5F9",
    "white":   "#FFFFFF",
    "racer_colors": ["#00D1FF","#00FF85","#9066FF","#FFB020","#FF3A3A","#06C8D8","#FF7A30"]
}

LIGHT_THEME = {
    "bg":      "#F0F4F8",
    "panel":   "#E2E8F0",
    "card":    "#FFFFFF",
    "card2":   "#F8FAFC",
    "border":  "#CBD5E1",
    "accent":  "#0284C7",
    "green":   "#16A34A",
    "green2":  "#15803D",
    "red":     "#DC2626",
    "amber":   "#D97706",
    "purple":  "#7C3AED",
    "muted":   "#64748B",
    "dim":     "#CBD5E1",
    "gold":    "#D97706",
    "text":    "#0F172A",
    "white":   "#FFFFFF",
    "racer_colors": ["#0284C7","#16A34A","#7C3AED","#D97706","#DC2626","#0891B2","#EA580C"]
}

# ═══════════════════════════════════════════════
#  نظام اللغات (Localization)
# ═══════════════════════════════════════════════
STRINGS = {
    "ar": {
        "title": "نبتكر - Nabtakir", "conn_on": "متصل", "conn_off": "غير متصل",
        "day": "☀ نهار", "night": "🌙 ليل", "lang": "English 🇺🇸",
        "port_title": "إدارة السباقات الذكية", "port_desc": "اختر المنفذ للبدء",
        "connect": "اتصال بـ Arduino", "demo": "▷ محاكاة (بدون Arduino)",
        "setup_title": "إعداد المتسابقين", "setup_desc": "أضف المتسابقين لبدء السباق",
        "add": " + إضافة ", "start_race": "  ابدأ السباق  ▶", "back": "← رجوع",
        "manual_start": "▶ بدء (يدوي)", "manual_stop": "■ إنهاء (يدوي)",
        "reset": "⟳ إعادة", "finish": "← إنهاء", "results": "لوحة النتائج",
        "winner": "🏆 البطل: {name} 🏆", "restart": "إعادة سباق جديد",
        "save_msg": "الرجاء اختيار مجلد لحفظ النتائج تلقائياً.",
        "custom_audio": "تخصيص الأصوات", "audio_start": "صوت البداية", "audio_win": "صوت الفوز"
    },
    "en": {
        "title": "Nabtakir - Timer", "conn_on": "Connected", "conn_off": "Disconnected",
        "day": "☀ Light", "night": "🌙 Dark", "lang": "العربية 🇸🇦",
        "port_title": "Smart Race Management", "port_desc": "Select Port to Start",
        "connect": "Connect Arduino", "demo": "▷ Demo Mode (No Arduino)",
        "setup_title": "Racer Setup", "setup_desc": "Add racers to begin",
        "add": " + Add ", "start_race": "  Start Race  ▶", "back": "← Back",
        "manual_start": "▶ Start (Manual)", "manual_stop": "■ Stop (Manual)",
        "reset": "⟳ Reset", "finish": "← Finish", "results": "Scoreboard",
        "winner": "🏆 Winner: {name} 🏆", "restart": "New Race",
        "save_msg": "Please select a folder to auto-save results.",
        "custom_audio": "Custom Audio", "audio_start": "Start Sound", "audio_win": "Win Sound"
    }
}

def L(key, lang="ar", **kwargs):
    text = STRINGS.get(lang, STRINGS["ar"]).get(key, key)
    if kwargs:
        try: return text.format(**kwargs)
        except: return text
    return text

C = DARK_THEME.copy()

def resource_path(relative_path):
    """ الحصول على المسار الصحيح للملف سواء في وضع التطوير أو بعد البناء (PyInstaller) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def fmt(ms: int) -> str:
    return f"{ms//60000:02d}:{(ms%60000)//1000:02d}.{ms%1000:03d}"

def btn(parent, text, cmd, bg, fg, px=12, py=7, font_size=10):
    return tk.Button(parent, text=text, command=cmd,
                     font=("Segoe UI", font_size, "bold"),
                     bg=bg, fg=fg, activebackground=bg,
                     activeforeground=fg, relief="flat",
                     cursor="hand2", padx=px, pady=py,
                     bd=0, highlightthickness=0)

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        
        self._load_settings()
        self.is_dark_mode = self.settings.get("theme", "dark") == "dark"
        self.lang = self.settings.get("lang", "ar")
        
        global C
        C = DARK_THEME.copy() if self.is_dark_mode else LIGHT_THEME.copy()
        
        self.current_page = None
        self.root.title("Nabtakir - نبتكر")
        self.root.configure(bg=C["bg"])
        self.root.attributes("-alpha", 0.94)  # جعل خلفية التطبيق شفافة (تأثير زجاجي)

        # ربط زر المسافة (Space) باختصار البدء/التوقف في وضع المحاكاة
        self.root.bind("<space>", self._on_space)

        # محاولة تحميل الأيقونة
        self.icon_path = resource_path("icon.ico")
        try:
            if os.path.exists(self.icon_path):
                self.root.iconbitmap(self.icon_path)
        except:
            pass

        w, h = 1000, 720
        ws, hs = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x, y = int((ws/2) - (w/2)), int((hs/2) - (h/2) - 40)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(850, 650)
        
        # العرض في شكل مكتب (تكبير الشاشة ملء الشاشة)
        self.root.state('zoomed')

        self.ser        = None
        self.connected  = False
        self._load_data()
        self.curr       = 0
        self.racing     = False
        self.armed      = False
        self.t0         = 0.0
        self.tick_id    = None

        # متغيرات إعادة الاتصال التلقائي
        self.reconnecting = False
        self.should_reconnect = False
        self.last_port = self.settings.get("port", "")

        # تحميل الشعار من الأيقونة أو ملف خارجي
        self.logo_img = None
        try:
            if os.path.exists(self.icon_path):
                raw = Image.open(self.icon_path)
                self.logo_img = ImageTk.PhotoImage(raw.resize((120, 120), Image.LANCZOS))
        except:
            pass

        self._style()
        self._topbar()
        self._statusbar()
        self.frame = tk.Frame(self.root, bg=C["bg"])
        self.frame.pack(fill="both", expand=True)

        # طلب مسار الحفظ عند أول تشغيل للتطبيق
        if not self.settings.get("save_dir"):
            messagebox.showinfo("Setup", L("save_msg", self.lang))
            d = filedialog.askdirectory(title="اختر مجلد حفظ النتائج")
            if d:
                self.settings["save_dir"] = d
                self._save_settings()

        self._page_port()
        self._auto_reconnect_loop()

    def _load_settings(self):
        self.settings_file = resource_path("nabtakir_settings.json")
        self.settings = {
            "theme": "dark", 
            "port": "", 
            "baud": "9600", 
            "save_dir": "",
            "lang": "ar",
            "sound_start": "",
            "sound_win": ""
        }
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self.settings.update(json.load(f))
        except: pass

    def _save_settings(self):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except: pass

    def _load_data(self):
        self.data_file = resource_path("nabtakir_data.json")
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.racers = json.load(f)
            else:
                self.racers = []
        except:
            self.racers = []

    def _save_data(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.racers, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")

    def _topbar(self):
        self.top_bar = tk.Frame(self.root, bg=C["panel"], height=60)
        self.top_bar.pack(fill="x")
        self.top_bar.pack_propagate(False)

        self.lbl_title = tk.Label(self.top_bar, text=f"  ⏱  {L('title', self.lang)}",
                 font=("Segoe UI", 16, "bold"),
                 bg=C["panel"], fg=C["accent"])
        self.lbl_title.pack(side="left", pady=14)

        # أزرار اللغة والمظهر
        self.btn_lang = tk.Button(self.top_bar, text=L("lang", self.lang), font=("Segoe UI", 10, "bold"),
                                   bg=C["panel"], fg=C["text"], relief="flat",
                                   activebackground=C["panel"], activeforeground=C["accent"], bd=0, cursor="hand2", command=self._toggle_lang)
        self.btn_lang.pack(side="right", padx=15)

        theme_txt = L("day" if self.is_dark_mode else "night", self.lang)
        self.btn_theme = tk.Button(self.top_bar, text=theme_txt, font=("Segoe UI", 11, "bold"),
                                   bg=C["panel"], fg=C["text"], relief="flat",
                                   activebackground=C["panel"], activeforeground=C["accent"], bd=0, cursor="hand2",
                                   command=self._toggle_theme)
        self.btn_theme.pack(side="right", padx=15)

        self.lbl_conn = tk.Label(self.top_bar, text=f"● {L('conn_off', self.lang)}",
                                  font=("Segoe UI", 10),
                                  bg=C["panel"], fg=C["red"])
        self.lbl_conn.pack(side="right", padx=10)

        self.lbl_port_info = tk.Label(self.top_bar, text="",
                                       font=("Consolas", 10),
                                       bg=C["panel"], fg=C["muted"])
        self.lbl_port_info.pack(side="right", padx=10)

    def _statusbar(self):
        self.sb_var = tk.StringVar(value="  Ready")
        self.bot_bar = tk.Frame(self.root, bg=C["panel"], height=30)
        self.bot_bar.pack(fill="x", side="bottom")
        self.bot_bar.pack_propagate(False)
        self.sb_lbl = tk.Label(self.bot_bar, textvariable=self.sb_var,
                                font=("Segoe UI", 9),
                                bg=C["panel"], fg=C["muted"], anchor="w")
        self.sb_lbl.pack(fill="x", padx=12, pady=5)

    def _status(self, msg, color=None):
        self.sb_var.set(f"  {msg}")
        self.sb_lbl.config(fg=color or C["muted"])

    def _toggle_lang(self):
        self.lang = "en" if self.lang == "ar" else "ar"
        self.settings["lang"] = self.lang
        self._save_settings()
        self._update_ui_text()
        if self.current_page: self.current_page()

    def _toggle_theme(self):
        if getattr(self, 'racing', False):
            messagebox.showinfo("تنبيه", "لا يمكن تغيير المظهر أثناء جريان المؤقت.")
            return

        self.is_dark_mode = not getattr(self, 'is_dark_mode', True)
        self.settings["theme"] = "dark" if self.is_dark_mode else "light"
        self._save_settings()
        
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        for k, v in theme.items():
            C[k] = v

        self._update_ui_text()
        self._style()
        if getattr(self, 'current_page', None):
            self.current_page()

    def _update_ui_text(self):
        self.root.configure(bg=C["bg"])
        self.top_bar.configure(bg=C["panel"])
        self.lbl_title.configure(bg=C["panel"], fg=C["accent"], text=f"  ⏱  {L('title', self.lang)}")
        self.lbl_conn.configure(bg=C["panel"], text=f"● {L('conn_on' if self.connected else 'conn_off', self.lang)}")
        self.lbl_port_info.configure(bg=C["panel"])
        self.btn_theme.configure(bg=C["panel"], fg=C["text"], text=L("day" if self.is_dark_mode else "night", self.lang))
        self.btn_lang.configure(bg=C["panel"], text=L("lang", self.lang))
        self.bot_bar.configure(bg=C["panel"])
        self.sb_lbl.configure(bg=C["panel"], fg=C["muted"])
        self.frame.configure(bg=C["bg"])

    def _clear(self):
        for w in self.frame.winfo_children():
            w.destroy()

    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TCombobox",
                    fieldbackground=C["card2"], background=C["card2"],
                    foreground=C["text"], selectbackground=C["accent"],
                    bordercolor=C["border"], arrowcolor=C["muted"])
        s.configure("Race.Treeview",
                    background=C["card"], foreground=C["text"],
                    fieldbackground=C["card"], bordercolor=C["border"],
                    rowheight=38, font=("Consolas", 12))
        s.configure("Race.Treeview.Heading",
                    background=C["panel"], foreground=C["muted"],
                    font=("Segoe UI", 10, "bold"), relief="flat")
        s.map("Race.Treeview",
              background=[("selected", C["accent"])],
              foreground=[("selected", C["bg"])])

    def _page_port(self):
        self.current_page = self._page_port
        self._clear()
        outer = tk.Frame(self.frame, bg=C["bg"])
        outer.place(relx=.5, rely=.5, anchor="center")
        card = tk.Frame(outer, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        card.pack(ipadx=60, ipady=50)

        if self.logo_img:
            tk.Label(card, image=self.logo_img, bg=C["card"]).pack(pady=(0, 15))
        else:
            tk.Label(card, text="⏱", font=("Segoe UI", 72), bg=C["card"], fg=C["accent"]).pack()

        tk.Label(card, text=L("port_title", self.lang), font=("Segoe UI", 28, "bold"), bg=C["card"], fg=C["text"]).pack()
        tk.Label(card, text=L("port_desc", self.lang), font=("Segoe UI", 12), bg=C["card"], fg=C["muted"]).pack(pady=(4, 35))

        row = tk.Frame(card, bg=C["card"])
        row.pack()
        tk.Label(row, text="COM Port:", font=("Segoe UI", 12), bg=C["card"], fg=C["muted"]).pack(side="left", padx=(0, 10))
        self.cmb = ttk.Combobox(row, width=12, state="readonly", font=("Segoe UI", 12))
        self.cmb.pack(side="left")
        btn(row, "↻", self._refresh, C["dim"], C["muted"], px=10, py=7).pack(side="left", padx=(8, 0))

        row2 = tk.Frame(card, bg=C["card"])
        row2.pack(pady=(12, 0))
        tk.Label(row2, text="Baud Rate:", font=("Segoe UI", 12), bg=C["card"], fg=C["muted"]).pack(side="left", padx=(0, 10))
        self.cmb_baud = ttk.Combobox(row2, width=10, state="readonly", values=["9600","115200"], font=("Segoe UI", 12))
        self.cmb_baud.set(self.settings.get("baud", "9600"))
        self.cmb_baud.pack(side="left")

        btn(card, f"  {L('connect', self.lang)}  ", self._connect, C["accent"], C["bg"], px=32, py=12, font_size=13).pack(pady=(30, 0))
        sep = tk.Frame(card, bg=C["border"], height=1)
        sep.pack(fill="x", pady=(20, 15))
        
        # قسم تخصيص الأصوات
        aud = tk.Frame(card, bg=C["card"])
        aud.pack(fill="x", pady=5)
        tk.Label(aud, text=L("custom_audio", self.lang), font=("Segoe UI", 10, "bold"), bg=C["card"], fg=C["accent"]).pack(side="left")
        
        def pick_sound(key):
            f = filedialog.askopenfilename(filetypes=[("Sound Files", "*.wav")])
            if f:
                self.settings[key] = f
                self._save_settings()

        btns_aud = tk.Frame(card, bg=C["card"])
        btns_aud.pack(fill="x", pady=5)
        
        # أيقونة صغيرة أو نص بسيط لاختيار الأصوات
        s_start = "✅" if self.settings.get("sound_start") else "📁"
        s_win = "✅" if self.settings.get("sound_win") else "📁"
        
        tk.Label(btns_aud, text=L("audio_start", self.lang), bg=C["card"], fg=C["muted"], font=("Segoe UI", 9)).pack(side="left")
        tk.Button(btns_aud, text=s_start, bg=C["card2"], fg=C["text"], relief="flat", command=lambda: pick_sound("sound_start")).pack(side="left", padx=5)
        
        tk.Label(btns_aud, text=L("audio_win", self.lang), bg=C["card"], fg=C["muted"], font=("Segoe UI", 9)).pack(side="left", padx=(10, 0))
        tk.Button(btns_aud, text=s_win, bg=C["card2"], fg=C["text"], relief="flat", command=lambda: pick_sound("sound_win")).pack(side="left", padx=5)

        sep2 = tk.Frame(card, bg=C["border"], height=1)
        sep2.pack(fill="x", pady=(15, 15))
        btn(card, L("demo", self.lang), self._demo_mode, C["dim"], C["muted"], px=20).pack()
        self._refresh()

    def _refresh(self):
        if SERIAL_OK:
            ports = [p.device for p in serial.tools.list_ports.comports()]
        else:
            ports = ["COM3", "COM4", "COM5"]
        self.cmb["values"] = ports
        if self.settings.get("port") in ports:
            self.cmb.set(self.settings["port"])
        elif ports:
            self.cmb.current(0)

    def _connect(self):
        port = self.cmb.get()
        baud = int(self.cmb_baud.get())
        if not port: return
        
        self.settings["port"] = port
        self.settings["baud"] = str(baud)
        self._save_settings()
        
        if not self.reconnecting:
            try:
                self.ser = serial.Serial(port, baud, timeout=0.5)
                time.sleep(1.5)
                self.connected = True
                self.should_reconnect = True
                self.last_port = port
                self.lbl_conn.config(text=f"● {port} @ {baud}", fg=C["green"])
                self._status(f"Connected to {port}", C["green"])
                threading.Thread(target=self._serial_loop, daemon=True).start()
                if self.current_page == self._page_port: self._page_setup()
            except Exception as e:
                if not self.reconnecting: messagebox.showerror("Error", str(e))

    def _auto_reconnect_loop(self):
        """ فحص حالة الاتصال ومحاولة إعادة الربط تلقائياً """
        if self.should_reconnect and not self.connected and self.last_port:
            available_ports = [p.device for p in serial.tools.list_ports.comports()]
            if self.last_port in available_ports:
                self.reconnecting = True
                self._status(f"Reconnecting to {self.last_port}...", C["amber"])
                self._connect()
                self.reconnecting = False
        
        self.root.after(2000, self._auto_reconnect_loop)

    def _play_sound(self, mode="start"):
        """ تشغيل الأصوات المخصصة أو النظام """
        s_path = self.settings.get("sound_start" if mode == "start" else "sound_win")
        
        def run():
            try:
                if s_path and os.path.exists(s_path):
                    winsound.PlaySound(s_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    # Fallback to beeps
                    if mode == "start":
                        winsound.Beep(800, 150)
                    else:
                        winsound.Beep(1200, 200)
                        winsound.Beep(1600, 300)
            except: pass
        threading.Thread(target=run, daemon=True).start()

    def _demo_mode(self):
        self.connected = False
        self.should_reconnect = False
        self.lbl_conn.config(text="● محاكاة", fg=C["amber"])
        self._page_setup()

    def _page_setup(self):
        self.current_page = self._page_setup
        self._clear()
        main = tk.Frame(self.frame, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=50, pady=35)
        tk.Label(main, text=L("setup_title", self.lang), font=("Segoe UI", 24, "bold"), bg=C["bg"], fg=C["text"]).pack(anchor="w")
        tk.Label(main, text=L("setup_desc", self.lang), font=("Segoe UI", 12), bg=C["bg"], fg=C["muted"]).pack(anchor="w", pady=(2, 25))

        add = tk.Frame(main, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        add.pack(fill="x")
        row = tk.Frame(add, bg=C["card"], padx=20, pady=20)
        row.pack(fill="x")
        self.ent = tk.Entry(row, font=("Segoe UI", 15), bg=C["card2"], fg=C["text"], insertbackground=C["text"], relief="flat")
        self.ent.pack(side="left", fill="x", expand=True, ipady=10)
        self.ent.bind("<Return>", lambda e: self._add_racer())
        btn(row, L("add", self.lang), self._add_racer, C["green2"], C["white"], px=22, py=10).pack(side="left", padx=(15, 0))

        self.list_fr = tk.Frame(main, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        self.list_fr.pack(fill="both", expand=True, pady=20)
        self._render_list()

        bot = tk.Frame(main, bg=C["bg"])
        bot.pack(fill="x")
        btn(bot, L("back", self.lang), self._page_port, C["dim"], C["muted"], px=15).pack(side="left")
        self.btn_go = btn(bot, L("start_race", self.lang), self._init_race, C["dim"], C["muted"], px=32, py=12, font_size=13)
        self.btn_go.pack(side="right")

    def _add_racer(self):
        name = self.ent.get().strip()
        if not name: return
        self.racers.append({"name": name, "ms": None, "state": "waiting"})
        self.ent.delete(0, tk.END)
        self._save_data()
        self._render_list()
        if self.racers: self.btn_go.config(bg=C["accent"], fg=C["bg"])

    def _render_list(self):
        for w in self.list_fr.winfo_children(): w.destroy()
        if not self.racers:
            tk.Label(self.list_fr, text="لا يوجد متسابقين", bg=C["card"], fg=C["muted"], font=("Segoe UI", 12)).pack(pady=40)
            return
        for i, r in enumerate(self.racers):
            col = C["racer_colors"][i % len(C["racer_colors"])]
            row = tk.Frame(self.list_fr, bg=C["card2"], pady=5)
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=f" {i+1} ", bg=col, fg=C["bg"], font=("Consolas", 12, "bold"), width=3).pack(side="left")
            tk.Label(row, text=r["name"], bg=C["card2"], fg=C["text"], font=("Segoe UI", 13, "bold")).pack(side="left", padx=15)
            tk.Button(row, text="✕", bg=C["card2"], fg=C["red"], relief="flat", command=lambda x=i: self._del_racer(x)).pack(side="right", padx=15)

    def _del_racer(self, i):
        self.racers.pop(i)
        self._save_data()
        self._render_list()
        if not self.racers: self.btn_go.config(bg=C["dim"], fg=C["muted"])

    def _init_race(self):
        self.curr = 0; self.racing = False; self.armed = False
        for r in self.racers: r["ms"] = None; r["state"] = "waiting"
        self._save_data()
        self._page_race()

    def _page_race(self):
        self.current_page = self._page_race
        self._clear()
        
        main = tk.Frame(self.frame, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=40, pady=30)
        
        self.lbl_name = tk.Label(main, text="", font=("Segoe UI", 36, "bold"), bg=C["bg"])
        self.lbl_name.pack(anchor="w")
        
        tc = tk.Frame(main, bg=C["card"], highlightbackground=C["border"], highlightthickness=2)
        tc.pack(fill="x", pady=20)
        self.lbl_t = tk.Label(tc, text="00:00.000", font=("Consolas", 80, "bold"), bg=C["card"], fg=C["text"])
        self.lbl_t.pack(pady=30)
        
        self.c_bar = tk.Canvas(tc, height=8, bg=C["card"], highlightthickness=0)
        self.c_bar.pack(fill="x")
        self._bar = self.c_bar.create_rectangle(0, 0, 0, 8, fill=C["accent"], outline="")
        
        br = tk.Frame(main, bg=C["bg"])
        br.pack(fill="x", pady=20)
        
        if not self.connected:
            btn(br, L("manual_start", self.lang), self._on_start, C["dim"], C["green"], px=15).pack(side="left")
            btn(br, L("manual_stop", self.lang), self._demo_stop, C["dim"], C["red"], px=15).pack(side="left", padx=10)
            
        btn(br, L("reset", self.lang), self._restart_race, C["dim"], C["amber"], px=15).pack(side="left")
        btn(br, L("finish", self.lang), self._page_setup, C["dim"], C["red"], px=20).pack(side="right")
        
        self._activate(self.curr)

    def _activate(self, idx):
        if idx >= len(self.racers): self._page_results(); return
        self.curr = idx; self.racing = False; self.armed = True
        self.racers[idx]["state"] = "ready"
        col = C["racer_colors"][idx % len(C["racer_colors"])]
        self.lbl_name.config(text=self.racers[idx]["name"], fg=col)
        self.lbl_t.config(text="00:00.000", fg=C["text"])
        self.c_bar.itemconfig(self._bar, fill=col)
        self._send("ARM")

    def _on_start(self):
        if self.racing or not self.armed: return
        self.racing = True; self.t0 = time.perf_counter(); self.armed = False
        self.lbl_t.config(fg=C["green"])
        self._play_sound("start")
        self._tick()

    def _tick(self):
        if not self.racing: return
        el = int((time.perf_counter() - self.t0) * 1000)
        self.lbl_t.config(text=fmt(el))
        w = self.c_bar.winfo_width()
        self.c_bar.coords(self._bar, 0, 0, int(w * min(el/30000, 1)), 8)
        self.tick_id = self.root.after(30, self._tick)

    def _on_stop(self, ms):
        if not self.racing: return
        self.racing = False
        self.racers[self.curr]["ms"] = ms
        self.racers[self.curr]["state"] = "done"
        self._save_data()
        
        self._play_sound("win")
            
        self.root.after(2000, lambda: self._activate(self.curr + 1))

    def _restart_race(self): self._activate(self.curr)
    def _demo_stop(self):
        if not self.racing: return
        d = int((time.perf_counter() - self.t0) * 1000)
        self._on_stop(d)

    def _page_results(self):
        self.current_page = self._page_results
        self._clear()
        done = sorted([r for r in self.racers if r["ms"]], key=lambda x: x["ms"])
        
        # الحفظ التلقائي للنتائج في المجلد المختار
        if done and self.settings.get("save_dir"):
            try:
                fn = os.path.join(self.settings["save_dir"], f"Race_Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                with open(fn, mode="w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)
                    writer.writerow(["المركز", "اسم المتسابق", "الزمن (ملي ثانية)", "الزمن (منسق)"])
                    for i, r in enumerate(done):
                        writer.writerow([i+1, r["name"], r["ms"], fmt(r["ms"])])
            except: pass

        # صوت الاحتفال بالنتائج
        def fanfare():
            try:
                for f, d in [(523,150),(659,150),(784,150),(1047,400)]:
                    if f: winsound.Beep(f, d)
                    else: time.sleep(d/1000)
            except: pass
        threading.Thread(target=fanfare, daemon=True).start()

        main = tk.Frame(self.frame, bg=C["bg"], padx=50, pady=40)
        main.pack(fill="both", expand=True)
        
        # أنيميشن البطل (المركز الأول)
        if done:
            winner = done[0]
            self.lbl_win = tk.Label(main, text=L("winner", self.lang, name=winner['name']), font=("Segoe UI", 36, "bold"), bg=C["bg"], fg=C["gold"])
            self.lbl_win.pack(pady=(0, 20))
            self._animate_winner()
            
        tk.Label(main, text=L("results", self.lang), font=("Segoe UI", 24, "bold"), bg=C["bg"], fg=C["text"]).pack(anchor="w", pady=(0, 20))
        
        medals = ["🥇", "🥈", "🥉"]
        m_colors = [C["gold"], "#C0C0C0", "#CD7F32"] # ذهبي، فضي، برونزي
        
        for i, r in enumerate(done):
            row = tk.Frame(main, bg=C["card"], pady=10)
            row.pack(fill="x", pady=5)
            
            is_top3 = i < 3
            m_txt = medals[i] if is_top3 else f"#{i+1}"
            fg_col = m_colors[i] if is_top3 else C["text"]
            
            tk.Label(row, text=m_txt, font=("Segoe UI", 20, "bold"), bg=C["card"], fg=fg_col, width=5).pack(side="left")
            tk.Label(row, text=r["name"], font=("Segoe UI", 18, "bold"), bg=C["card"], fg=fg_col, width=20, anchor="w").pack(side="left")
            tk.Label(row, text=fmt(r["ms"]), font=("Consolas", 20, "bold"), bg=C["card"], fg=C["accent"]).pack(side="right", padx=20)

        bot_fr = tk.Frame(main, bg=C["bg"])
        bot_fr.pack(pady=30)
        btn(bot_fr, L("restart", self.lang), self._page_setup, C["accent"], C["bg"], px=30, py=10).pack()

    def _animate_winner(self):
        if not hasattr(self, 'lbl_win') or not self.lbl_win.winfo_exists(): return
        colors = [C["gold"], "#FFEA00", "#FFC400", C["white"]]
        current = self.lbl_win.cget("fg")
        try:
            nxt = colors[(colors.index(current) + 1) % len(colors)]
        except:
            nxt = C["gold"]
        self.lbl_win.config(fg=nxt)
        self.root.after(250, self._animate_winner)

    def _serial_loop(self):
        while self.connected and self.ser:
            try:
                line = self.ser.readline().decode().strip()
                if line == "START": self.root.after(0, self._on_start)
                elif line.startswith("TIME:"):
                    ms = int(line.split(":")[1])
                    self.root.after(0, lambda m=ms: self._on_stop(m))
            except: 
                self.connected = False
                self.lbl_conn.config(text=f"● {L('conn_off', self.lang)}", fg=C["red"])
                self._status("Connection Lost!", C["red"])
                break

    def _send(self, cmd):
        if self.ser: self.ser.write(f"{cmd}\n".encode())

    def _on_space(self, event=None):
        if self.current_page == self._page_race and not self.connected:
            if self.racing: self._demo_stop()
            else: self._on_start()

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
