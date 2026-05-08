"""
╔══════════════════════════════════════════════════════════════╗
║          RACE TIMER PRO — v3.0                              ║
║  تطبيق Python كامل مع Serial ثنائي الاتجاه                 ║
║  pip install pyserial                                       ║
╚══════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading, time, csv, os, winsound
from datetime import datetime

try:
    import serial
    import serial.tools.list_ports
    SERIAL_OK = True
except ImportError:
    SERIAL_OK = False

# ═══════════════════════════════════════════════
#  الألوان والخطوط
# ═══════════════════════════════════════════════
C = {
    "bg":      "#080B12",
    "panel":   "#0E1220",
    "card":    "#141826",
    "card2":   "#1A1F30",
    "border":  "#252C45",
    "accent":  "#4484FF",
    "green":   "#18D860",
    "green2":  "#0FA844",
    "red":     "#FF3A3A",
    "amber":   "#FFB020",
    "purple":  "#9066FF",
    "muted":   "#4A5270",
    "dim":     "#1E2338",
    "gold":    "#FFD700",
    "text":    "#DDE2F0",
    "white":   "#FFFFFF",
}

RACER_COLORS = ["#4484FF","#18D860","#9066FF","#FFB020","#FF3A3A","#06C8D8","#FF7A30"]

def fmt(ms: int) -> str:
    return f"{ms//60000:02d}:{(ms%60000)//1000:02d}.{ms%1000:03d}"

def btn(parent, text, cmd, bg, fg, px=12, py=7, font_size=10):
    return tk.Button(parent, text=text, command=cmd,
                     font=("Segoe UI", font_size, "bold"),
                     bg=bg, fg=fg, activebackground=bg,
                     activeforeground=fg, relief="flat",
                     cursor="hand2", padx=px, pady=py,
                     bd=0, highlightthickness=0)

# ═══════════════════════════════════════════════
#  التطبيق
# ═══════════════════════════════════════════════
class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Race Timer Pro")
        self.root.configure(bg=C["bg"])
        self.root.geometry("980x700")
        self.root.minsize(820, 600)

        # Serial
        self.ser        = None
        self.connected  = False

        # سباق
        self.racers     = []
        self.curr       = 0
        self.racing     = False
        self.armed      = False
        self.t0         = 0.0
        self.tick_id    = None

        self._style()
        self._topbar()
        self._statusbar()
        self.frame = tk.Frame(self.root, bg=C["bg"])
        self.frame.pack(fill="both", expand=True)

        self._page_port()

    # ─── شريط علوي ──────────────────────────────
    def _topbar(self):
        bar = tk.Frame(self.root, bg=C["panel"], height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="  ⏱  RACE TIMER PRO",
                 font=("Segoe UI", 14, "bold"),
                 bg=C["panel"], fg=C["accent"]).pack(side="left", pady=14)

        self.lbl_conn = tk.Label(bar, text="● غير متصل",
                                  font=("Segoe UI", 9),
                                  bg=C["panel"], fg=C["red"])
        self.lbl_conn.pack(side="right", padx=16)

        self.lbl_port_info = tk.Label(bar, text="",
                                       font=("Consolas", 9),
                                       bg=C["panel"], fg=C["muted"])
        self.lbl_port_info.pack(side="right", padx=8)

    # ─── شريط حالة ──────────────────────────────
    def _statusbar(self):
        self.sb_var = tk.StringVar(value="  جاهز")
        self.sb_clr = C["muted"]
        bar = tk.Frame(self.root, bg=C["panel"], height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.sb_lbl = tk.Label(bar, textvariable=self.sb_var,
                                font=("Segoe UI", 9),
                                bg=C["panel"], fg=C["muted"], anchor="w")
        self.sb_lbl.pack(fill="x", padx=10, pady=3)

    def _status(self, msg, color=None):
        self.sb_var.set(f"  {msg}")
        self.sb_lbl.config(fg=color or C["muted"])

    # ─── مساعد تنظيف ────────────────────────────
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
                    rowheight=34, font=("Consolas", 11))
        s.configure("Race.Treeview.Heading",
                    background=C["panel"], foreground=C["muted"],
                    font=("Segoe UI", 9), relief="flat")
        s.map("Race.Treeview",
              background=[("selected", C["accent"])],
              foreground=[("selected", C["white"])])

    # ════════════════════════════════════════════
    #  شاشة 1 — اختيار المنفذ
    # ════════════════════════════════════════════
    def _page_port(self):
        self._clear()

        outer = tk.Frame(self.frame, bg=C["bg"])
        outer.place(relx=.5, rely=.5, anchor="center")

        card = tk.Frame(outer, bg=C["card"],
                        highlightbackground=C["border"],
                        highlightthickness=1)
        card.pack(ipadx=50, ipady=40)

        # أيقونة
        tk.Label(card, text="⏱", font=("Segoe UI", 64),
                 bg=C["card"], fg=C["accent"]).pack()

        tk.Label(card, text="Race Timer Pro",
                 font=("Segoe UI", 24, "bold"),
                 bg=C["card"], fg=C["text"]).pack()

        tk.Label(card, text="اختر منفذ Arduino ثم اضغط اتصال",
                 font=("Segoe UI", 11),
                 bg=C["card"], fg=C["muted"]).pack(pady=(4, 30))

        # منفذ
        row = tk.Frame(card, bg=C["card"])
        row.pack()

        tk.Label(row, text="COM Port:", font=("Segoe UI", 11),
                 bg=C["card"], fg=C["muted"]).pack(side="left", padx=(0, 8))

        self.cmb = ttk.Combobox(row, width=11, state="readonly",
                                  font=("Segoe UI", 11))
        self.cmb.pack(side="left")

        btn(row, "↻", self._refresh,
            C["dim"], C["muted"], px=8, py=6).pack(side="left", padx=(6, 0))

        # سرعة
        row2 = tk.Frame(card, bg=C["card"])
        row2.pack(pady=(10, 0))
        tk.Label(row2, text="Baud Rate:", font=("Segoe UI", 11),
                 bg=C["card"], fg=C["muted"]).pack(side="left", padx=(0, 8))
        self.cmb_baud = ttk.Combobox(row2, width=9, state="readonly",
                                      values=["9600","115200"], font=("Segoe UI", 11))
        self.cmb_baud.set("9600")
        self.cmb_baud.pack(side="left")

        # أزرار
        btn(card, "  اتصال بـ Arduino  ",
            self._connect, C["accent"], C["white"], px=28, py=10,
            font_size=12).pack(pady=(24, 0))

        sep = tk.Frame(card, bg=C["border"], height=1)
        sep.pack(fill="x", pady=(22, 16))

        btn(card, "▷  محاكاة (بدون Arduino)",
            self._demo_mode, C["dim"], C["muted"], px=16).pack()

        if not SERIAL_OK:
            tk.Label(card,
                     text="⚠  pip install pyserial",
                     font=("Segoe UI", 9),
                     bg=C["card"], fg=C["amber"]).pack(pady=(12, 0))

        self._refresh()

    def _refresh(self):
        if SERIAL_OK:
            ports = [p.device for p in serial.tools.list_ports.comports()]
        else:
            ports = ["COM3", "COM4", "COM5", "COM6", "COM7"]
        self.cmb["values"] = ports
        if ports:
            self.cmb.current(0)

    def _connect(self):
        port = self.cmb.get()
        baud = int(self.cmb_baud.get())
        if not port:
            messagebox.showwarning("تنبيه", "اختر منفذاً")
            return
        if not SERIAL_OK:
            messagebox.showwarning("تنبيه", "pip install pyserial")
            return
        try:
            self.ser = serial.Serial(port, baud, timeout=0.5)
            time.sleep(2)
            self.connected = True
            self.lbl_conn.config(text=f"● {port} @ {baud}", fg=C["green"])
            self.lbl_port_info.config(text=f"baud={baud}")
            self._status(f"متصل على {port}", C["green"])
            threading.Thread(target=self._serial_loop, daemon=True).start()
            self._page_setup()
        except Exception as e:
            messagebox.showerror("خطأ في الاتصال", str(e))

    def _demo_mode(self):
        self.connected = False
        self.lbl_conn.config(text="● محاكاة", fg=C["amber"])
        self._status("وضع المحاكاة — لا يوجد Arduino", C["amber"])
        self._page_setup()

    # ════════════════════════════════════════════
    #  شاشة 2 — إعداد المتسابقين
    # ════════════════════════════════════════════
    def _page_setup(self):
        self._clear()
        self.racers = []

        main = tk.Frame(self.frame, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=44, pady=28)

        # عنوان
        tk.Label(main, text="إعداد المتسابقين",
                 font=("Segoe UI", 20, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w")
        tk.Label(main, text="أضف كل متسابق واضغط + أو Enter",
                 font=("Segoe UI", 11),
                 bg=C["bg"], fg=C["muted"]).pack(anchor="w", pady=(2, 20))

        # صف الإضافة
        add = tk.Frame(main, bg=C["card"],
                       highlightbackground=C["border"],
                       highlightthickness=1)
        add.pack(fill="x")
        inn = tk.Frame(add, bg=C["card"])
        inn.pack(padx=18, pady=14, fill="x")

        tk.Label(inn, text="اسم المتسابق أو الجولة:",
                 font=("Segoe UI", 10),
                 bg=C["card"], fg=C["muted"]).pack(anchor="w", pady=(0, 6))

        row = tk.Frame(inn, bg=C["card"])
        row.pack(fill="x")

        self.ent = tk.Entry(row, font=("Segoe UI", 13),
                             bg=C["card2"], fg=C["text"],
                             insertbackground=C["text"],
                             relief="flat",
                             highlightbackground=C["border"],
                             highlightthickness=1)
        self.ent.pack(side="left", fill="x", expand=True, ipady=8)
        self.ent.bind("<Return>", lambda e: self._add_racer())
        self.ent.focus()

        btn(row, " +  إضافة ", self._add_racer,
            C["green2"], C["white"], px=18, py=8).pack(side="left", padx=(10, 0))

        # القائمة
        tk.Label(main, text="المتسابقون:",
                 font=("Segoe UI", 12, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w", pady=(18, 8))

        self.list_fr = tk.Frame(main, bg=C["card"],
                                 highlightbackground=C["border"],
                                 highlightthickness=1)
        self.list_fr.pack(fill="both", expand=True)

        self.lbl_empty = tk.Label(self.list_fr,
                                   text="لا يوجد متسابقون — أضف واحداً على الأقل",
                                   font=("Segoe UI", 11),
                                   bg=C["card"], fg=C["muted"])
        self.lbl_empty.pack(pady=34)

        # أزرار الأسفل
        sep = tk.Frame(main, bg=C["border"], height=1)
        sep.pack(fill="x", pady=(16, 14))
        bot = tk.Frame(main, bg=C["bg"])
        bot.pack(fill="x")

        btn(bot, "← تغيير المنفذ",
            self._page_port, C["dim"], C["muted"], px=12).pack(side="left")

        self.btn_go = btn(bot, "  ابدأ السباق  ▶",
                           self._page_race,
                           C["dim"], C["muted"], px=26, py=9, font_size=12)
        self.btn_go.pack(side="right")

    def _add_racer(self):
        name = self.ent.get().strip()
        if not name:
            self.ent.focus()
            return
        self.racers.append({"name": name, "ms": None, "state": "waiting"})
        self.ent.delete(0, tk.END)
        self._render_list()
        if len(self.racers) == 1:
            self.btn_go.config(bg=C["accent"], fg=C["white"])

    def _del_racer(self, i):
        self.racers.pop(i)
        self._render_list()
        if not self.racers:
            self.btn_go.config(bg=C["dim"], fg=C["muted"])

    def _render_list(self):
        for w in self.list_fr.winfo_children():
            w.destroy()
        if not self.racers:
            tk.Label(self.list_fr,
                     text="لا يوجد متسابقون — أضف واحداً على الأقل",
                     font=("Segoe UI", 11),
                     bg=C["card"], fg=C["muted"]).pack(pady=34)
            return
        for i, r in enumerate(self.racers):
            col = RACER_COLORS[i % len(RACER_COLORS)]
            row = tk.Frame(self.list_fr, bg=C["card2"],
                           highlightbackground=C["border"],
                           highlightthickness=1)
            row.pack(fill="x", padx=8, pady=3)
            tk.Label(row, text=f" {i+1} ",
                     font=("Consolas", 12, "bold"),
                     bg=col, fg=C["white"]).pack(side="left")
            tk.Label(row, text=r["name"],
                     font=("Segoe UI", 12, "bold"),
                     bg=C["card2"], fg=C["text"]).pack(side="left", padx=12, pady=9)
            tk.Button(row, text="✕",
                      font=("Segoe UI", 9),
                      bg=C["card2"], fg=C["muted"],
                      relief="flat", cursor="hand2",
                      command=lambda x=i: self._del_racer(x)).pack(side="right", padx=10)

    # ════════════════════════════════════════════
    #  شاشة 3 — السباق الحي
    # ════════════════════════════════════════════
    def _page_race(self):
        if not self.racers:
            return
        self._clear()
        self.curr   = 0
        self.racing = False
        self.armed  = False
        for r in self.racers:
            r["ms"] = None
            r["state"] = "waiting"

        # هيكل
        main = tk.Frame(self.frame, bg=C["bg"])
        main.pack(fill="both", expand=True)

        # ─ يسار ─────────────────────────────────
        left = tk.Frame(main, bg=C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=30, pady=22)

        self.lbl_num  = tk.Label(left, text="",
                                  font=("Segoe UI", 11, "bold"),
                                  bg=C["bg"], fg=C["muted"])
        self.lbl_num.pack(anchor="w")

        self.lbl_name = tk.Label(left, text="",
                                  font=("Segoe UI", 26, "bold"),
                                  bg=C["bg"], fg=C["text"])
        self.lbl_name.pack(anchor="w", pady=(0, 10))

        # كارت العداد
        tc = tk.Frame(left, bg=C["card"],
                      highlightbackground=C["border"],
                      highlightthickness=1)
        tc.pack(fill="x")

        tk.Label(tc, text="الزمن", font=("Segoe UI", 9),
                 bg=C["card"], fg=C["muted"]).pack(pady=(14, 0))

        self.lbl_t = tk.Label(tc, text="00:00.000",
                               font=("Consolas", 56, "bold"),
                               bg=C["card"], fg=C["text"])
        self.lbl_t.pack()

        # شريط تقدم
        self.c_bar = tk.Canvas(tc, height=6,
                                bg=C["card"], highlightthickness=0)
        self.c_bar.pack(fill="x", pady=(0, 14))
        self._bar = self.c_bar.create_rectangle(0, 0, 0, 6,
                                                  fill=C["accent"], outline="")

        # الحساسات
        sr = tk.Frame(left, bg=C["bg"])
        sr.pack(fill="x", pady=(14, 0))

        self.d1 = tk.Label(sr, text="●", font=("Segoe UI", 20),
                            bg=C["bg"], fg=C["muted"])
        self.d1.pack(side="left")
        self.l1 = tk.Label(sr, text="حساس 1 — في انتظار",
                            font=("Segoe UI", 10),
                            bg=C["bg"], fg=C["muted"])
        self.l1.pack(side="left", padx=(4, 20))

        self.d2 = tk.Label(sr, text="●", font=("Segoe UI", 20),
                            bg=C["bg"], fg=C["muted"])
        self.d2.pack(side="left")
        self.l2 = tk.Label(sr, text="حساس 2 — في انتظار",
                            font=("Segoe UI", 10),
                            bg=C["bg"], fg=C["muted"])
        self.l2.pack(side="left", padx=4)

        # أزرار
        br = tk.Frame(left, bg=C["bg"])
        br.pack(fill="x", pady=(22, 0))

        self.btn_demo = btn(br, "▷ محاكاة",
                             self._demo_curr, C["dim"], C["muted"], px=14)
        self.btn_demo.pack(side="left")

        btn(br, "⟳ إعادة", self._restart_race,
            C["dim"], C["amber"], px=14).pack(side="left", padx=8)

        btn(br, "← الإعداد", self._page_setup,
            C["dim"], C["red"], px=14).pack(side="right")

        # ─ يمين — لائحة المتسابقين ───────────────
        right = tk.Frame(main, bg=C["panel"], width=300)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)

        tk.Label(right, text="المتسابقون",
                 font=("Segoe UI", 12, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(anchor="w", padx=18, pady=(18, 10))

        self.rl_fr = tk.Frame(right, bg=C["panel"])
        self.rl_fr.pack(fill="both", expand=True, padx=10)

        sep = tk.Frame(right, bg=C["border"], height=1)
        sep.pack(fill="x", padx=10, pady=8)

        btn(right, "⬇ تصدير CSV", self._export,
            C["card"], C["muted"], px=12).pack(padx=10, pady=(0, 14), fill="x")

        self._activate(0)

    # ─── تفعيل متسابق ───────────────────────────
    def _activate(self, idx):
        if idx >= len(self.racers):
            self.root.after(500, self._page_results)
            return

        self.curr   = idx
        self.racing = False
        self.armed  = True
        self.racers[idx]["state"] = "ready"

        col = RACER_COLORS[idx % len(RACER_COLORS)]

        self.lbl_num.config(
            text=f"المتسابق {idx+1} من {len(self.racers)}", fg=col)
        self.lbl_name.config(text=self.racers[idx]["name"], fg=col)
        self.lbl_t.config(text="00:00.000", fg=C["text"])

        self.c_bar.coords(self._bar, 0, 0, 0, 6)
        self.c_bar.itemconfig(self._bar, fill=col)

        self._s1(False)
        self._s2(False)

        self._status(f"جاهز — انتظر مرور {self.racers[idx]['name']} من الحساس 1", C["muted"])

        # أرسل ARM للأردوينو
        self._send("ARM")

        self._render_race_list()

    def _render_race_list(self):
        for w in self.rl_fr.winfo_children():
            w.destroy()

        for i, r in enumerate(self.racers):
            is_curr = (i == self.curr)
            col = RACER_COLORS[i % len(RACER_COLORS)]
            bg  = C["card"] if is_curr else C["panel"]
            brd = col if is_curr else C["border"]

            card = tk.Frame(self.rl_fr, bg=bg,
                            highlightbackground=brd,
                            highlightthickness=2 if is_curr else 1)
            card.pack(fill="x", pady=3)

            top = tk.Frame(card, bg=bg)
            top.pack(fill="x", padx=10, pady=(8, 2))

            tk.Label(top, text=str(i+1),
                     font=("Consolas", 9, "bold"),
                     bg=col, fg=C["white"], width=2).pack(side="left")

            nm_fg = C["text"] if is_curr else C["muted"]
            tk.Label(top, text=r["name"],
                     font=("Segoe UI", 11, "bold"),
                     bg=bg, fg=nm_fg).pack(side="left", padx=6)

            if is_curr:
                tk.Label(top, text="◀ الآن",
                         font=("Segoe UI", 8),
                         bg=col, fg=C["white"], padx=4).pack(side="right")

            bot = tk.Frame(card, bg=bg)
            bot.pack(fill="x", padx=10, pady=(0, 8))

            if r["state"] == "done" and r["ms"] is not None:
                # تحقق من أفضل زمن
                done_ms = [x["ms"] for x in self.racers
                           if x["state"] == "done" and x["ms"]]
                is_best = done_ms and r["ms"] == min(done_ms)
                t_col = C["gold"] if is_best else col
                tk.Label(bot, text=fmt(r["ms"]),
                         font=("Consolas", 15, "bold"),
                         bg=bg, fg=t_col).pack(side="left")
                if is_best:
                    tk.Label(bot, text=" ★ أفضل",
                             font=("Segoe UI", 9),
                             bg=bg, fg=C["gold"]).pack(side="left")
            elif r["state"] == "running":
                tk.Label(bot, text="◉ جارٍ...",
                         font=("Segoe UI", 10),
                         bg=bg, fg=C["green"]).pack(side="left")
            else:
                tk.Label(bot, text="انتظار",
                         font=("Segoe UI", 9),
                         bg=bg, fg=C["muted"]).pack(side="left")

    # ─── بدء العداد ─────────────────────────────
    def _on_start(self):
        if not self.armed or self.racing:
            return
        self.racing = True
        self.armed  = False
        self.t0     = time.time()
        self.racers[self.curr]["state"] = "running"
        col = RACER_COLORS[self.curr % len(RACER_COLORS)]
        self.lbl_t.config(fg=C["green"])
        self.c_bar.itemconfig(self._bar, fill=col)
        self._s1(True)
        self._status(f"▶ يعدّ — {self.racers[self.curr]['name']}", C["green"])
        self._tick()
        self._render_race_list()

    def _tick(self):
        if not self.racing:
            return
        el = int((time.time() - self.t0) * 1000)
        self.lbl_t.config(text=fmt(el))
        w = self.c_bar.winfo_width()
        frac = min(el / 30000, 1.0)
        self.c_bar.coords(self._bar, 0, 0, int(w * frac), 6)
        self.tick_id = self.root.after(30, self._tick)

    # ─── إيقاف العداد ───────────────────────────
    def _on_stop(self, ms: int):
        if not self.racing:
            return
        self.racing = False
        if self.tick_id:
            self.root.after_cancel(self.tick_id)

        self.racers[self.curr]["ms"]    = ms
        self.racers[self.curr]["state"] = "done"

        col = RACER_COLORS[self.curr % len(RACER_COLORS)]
        self.lbl_t.config(text=fmt(ms), fg=col)
        self._s2(True)
        w = self.c_bar.winfo_width()
        self.c_bar.coords(self._bar, 0, 0, w, 6)

        self._status(f"✓ {self.racers[self.curr]['name']}  →  {fmt(ms)}", col)
        self._render_race_list()

        threading.Thread(target=_beep_finish, daemon=True).start()

        nxt = self.curr + 1
        delay = 2400
        if nxt < len(self.racers):
            self.root.after(delay, lambda: self._activate(nxt))
        else:
            self.root.after(delay, self._page_results)

    def _restart_race(self):
        if self.tick_id:
            self.root.after_cancel(self.tick_id)
        self._activate(self.curr)

    def _demo_curr(self):
        if self.racing:
            return
        import random
        delay = random.randint(1200, 7000)
        self.root.after(300, self._on_start)
        self.root.after(300 + delay, lambda: self._on_stop(delay))

    # ════════════════════════════════════════════
    #  شاشة 4 — النتائج النهائية
    # ════════════════════════════════════════════
    def _page_results(self):
        self._clear()
        threading.Thread(target=_fanfare, daemon=True).start()

        done   = [r for r in self.racers if r["ms"] is not None]
        ranked = sorted(done, key=lambda r: r["ms"])
        best   = ranked[0]["ms"] if ranked else 0

        main = tk.Frame(self.frame, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=40, pady=24)

        # عنوان
        tk.Label(main, text="🏆  نتائج السباق",
                 font=("Segoe UI", 22, "bold"),
                 bg=C["bg"], fg=C["gold"]).pack(anchor="w")
        tk.Label(main,
                 text=f"{len(done)} متسابق  |  {datetime.now().strftime('%H:%M  %Y-%m-%d')}",
                 font=("Segoe UI", 10),
                 bg=C["bg"], fg=C["muted"]).pack(anchor="w", pady=(2, 20))

        # جدول
        tbl = tk.Frame(main, bg=C["card"],
                        highlightbackground=C["border"],
                        highlightthickness=1)
        tbl.pack(fill="x")

        # رأس
        hdr = tk.Frame(tbl, bg=C["dim"])
        hdr.pack(fill="x")
        for txt, w in [("المركز",60),("الاسم",220),("الزمن",160),("الفارق",110)]:
            tk.Label(hdr, text=txt, font=("Segoe UI", 9),
                     bg=C["dim"], fg=C["muted"],
                     width=0, anchor="center").pack(side="left", padx=14, pady=7)

        medals = ["🥇","🥈","🥉"]
        row_bg = ["#1E1800","#151A1A","#1A1414"]

        for rank, r in enumerate(ranked, 1):
            rbg   = row_bg[min(rank-1, 2)] if rank <= 3 else C["card"]
            rfg   = C["gold"] if rank == 1 else C["text"]
            medal = medals[rank-1] if rank <= 3 else str(rank)
            diff  = r["ms"] - best

            row = tk.Frame(tbl, bg=rbg,
                            highlightbackground=C["border"],
                            highlightthickness=1)
            row.pack(fill="x", pady=2)

            tk.Label(row, text=medal, font=("Segoe UI", 15),
                     bg=rbg, width=5, anchor="center").pack(side="left", pady=10)
            tk.Label(row, text=r["name"],
                     font=("Segoe UI", 13, "bold"),
                     bg=rbg, fg=rfg, width=18, anchor="w").pack(side="left", padx=6)
            tk.Label(row, text=fmt(r["ms"]),
                     font=("Consolas", 15, "bold"),
                     bg=rbg,
                     fg=C["gold"] if rank == 1 else rfg,
                     width=12, anchor="center").pack(side="left")
            diff_txt = f"+{fmt(diff)}" if diff else "—"
            tk.Label(row, text=diff_txt,
                     font=("Consolas", 10),
                     bg=rbg,
                     fg=C["red"] if diff else C["muted"],
                     width=11, anchor="center").pack(side="left")

        # إحصائيات
        if ranked:
            avg = int(sum(r["ms"] for r in done) / len(done))
            sf = tk.Frame(main, bg=C["bg"])
            sf.pack(fill="x", pady=(18, 16))
            for col, (lbl, val, clr) in enumerate([
                ("أفضل زمن",    fmt(best),   C["gold"]),
                ("متوسط",       fmt(avg),    C["accent"]),
                ("المتسابقون",  str(len(done)), C["green"]),
            ]):
                sf.columnconfigure(col, weight=1)
                c = tk.Frame(sf, bg=C["card"],
                              highlightbackground=C["border"],
                              highlightthickness=1)
                c.grid(row=0, column=col, sticky="ew",
                       padx=(0 if col==0 else 8, 0), ipadx=8, ipady=10)
                tk.Label(c, text=lbl, font=("Segoe UI", 9),
                         bg=C["card"], fg=C["muted"]).pack()
                tk.Label(c, text=val,
                         font=("Consolas", 18, "bold"),
                         bg=C["card"], fg=clr).pack()

        # أزرار
        bot = tk.Frame(main, bg=C["bg"])
        bot.pack(fill="x")

        btn(bot, "↺  نفس المتسابقين مجدداً",
            self._page_race, C["accent"], C["white"], px=20, py=9).pack(side="left")
        btn(bot, "⬅  إعداد جديد",
            self._page_setup, C["dim"], C["muted"], px=16, py=9).pack(side="left", padx=10)
        btn(bot, "⬇  تصدير CSV",
            self._export, C["green2"], C["white"], px=16, py=9).pack(side="right")

    # ════════════════════════════════════════════
    #  Serial Loop
    # ════════════════════════════════════════════
    def _serial_loop(self):
        while self.connected and self.ser and self.ser.is_open:
            try:
                raw  = self.ser.readline()
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                if line == "START":
                    self.root.after(0, self._on_start)
                elif line.startswith("TIME:"):
                    try:
                        ms = int(line.split(":")[1])
                        self.root.after(0, lambda m=ms: self._on_stop(m))
                    except ValueError:
                        pass
                elif line == "PING":
                    self._send("PONG")
                elif line in ("ARMED_OK", "RESET_OK", "READY"):
                    self.root.after(0, lambda l=line:
                        self._status(f"Arduino: {l}", C["green"]))
            except Exception:
                break

    def _send(self, cmd: str):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((cmd + "\n").encode())
            except Exception:
                pass

    # ════════════════════════════════════════════
    #  تصدير
    # ════════════════════════════════════════════
    def _export(self):
        done = [r for r in self.racers if r["ms"] is not None]
        if not done:
            messagebox.showinfo("تنبيه", "لا توجد نتائج")
            return
        ranked = sorted(done, key=lambda r: r["ms"])
        fname  = f"race_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path   = os.path.join(os.path.expanduser("~"), "Desktop", fname)
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["المركز","الاسم","الزمن (ms)","الزمن"])
                for rank, r in enumerate(ranked, 1):
                    w.writerow([rank, r["name"], r["ms"], fmt(r["ms"])])
            messagebox.showinfo("✓ تم الحفظ", f"على سطح المكتب:\n{fname}")
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    # ─── مساعدات الحساسات ───────────────────────
    def _s1(self, on):
        if not hasattr(self, "d1"):
            return
        self.d1.config(fg=C["green"] if on else C["muted"])
        self.l1.config(text="حساس 1 ✓ اكتشف!" if on else "حساس 1 — في انتظار",
                       fg=C["green"] if on else C["muted"])

    def _s2(self, on):
        if not hasattr(self, "d2"):
            return
        self.d2.config(fg=C["accent"] if on else C["muted"])
        self.l2.config(text="حساس 2 ✓ اكتشف!" if on else "حساس 2 — في انتظار",
                       fg=C["accent"] if on else C["muted"])

# ═══════════════════════════════════════════════
#  الصوت
# ═══════════════════════════════════════════════
def _beep_finish():
    try:
        for f, d in [(880,110),(0,35),(1100,110),(0,35),(1320,200)]:
            if f: winsound.Beep(f, d)
            else:  time.sleep(d/1000)
    except Exception:
        pass

def _fanfare():
    try:
        notes = [(523,90),(0,25),(659,90),(0,25),(784,90),(0,25),
                 (1047,130),(0,40),(1047,130),(0,40),(1047,280)]
        for f, d in notes:
            if f: winsound.Beep(f, d)
            else:  time.sleep(d/1000)
    except Exception:
        pass

# ═══════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
