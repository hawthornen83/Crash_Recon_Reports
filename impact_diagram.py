import tkinter as tk
import customtkinter as ctk
import math
import re


class ImpactDiagram(ctk.CTkFrame):
    CLOCK_LABELS = {
        12: "Front",
        1:  "Front-Right",
        2:  "Right-Front",
        3:  "Right",
        4:  "Right-Rear",
        5:  "Rear-Right",
        6:  "Rear",
        7:  "Rear-Left",
        8:  "Left-Rear",
        9:  "Left",
        10: "Left-Front",
        11: "Front-Left",
    }

    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.selected = set()
        self.command = command
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Area of Impact", anchor="w").grid(
            row=0, column=0, sticky="ew", padx=2, pady=(0, 4)
        )

        canvas_frame = ctk.CTkFrame(self, corner_radius=10)
        canvas_frame.grid(row=1, column=0, sticky="ew", padx=2)

        self.canvas = tk.Canvas(canvas_frame, width=260, height=290,
                                bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(padx=8, pady=8)
        self.canvas.bind("<Button-1>", self._on_click)

        self.selection_label = ctk.CTkLabel(
            self, text="None selected", anchor="w",
            font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.selection_label.grid(row=2, column=0, sticky="ew", padx=2, pady=(6, 0))

        ctk.CTkButton(self, text="Clear Selection", height=28,
                      command=self._clear).grid(
            row=3, column=0, sticky="w", padx=2, pady=(4, 0)
        )

        self._render_diagram()

    def _render_diagram(self):
        self.canvas.delete("all")
        cx, cy = 130, 148
        r = 112

        # Car body
        cw, ch = 52, 90
        self.canvas.create_rectangle(
            cx - cw // 2, cy - ch // 2,
            cx + cw // 2, cy + ch // 2,
            fill="#4a4a4a", outline="#888888", width=2
        )
        # Front windshield line
        self.canvas.create_line(
            cx - cw // 2 + 6, cy - ch // 2 + 18,
            cx + cw // 2 - 6, cy - ch // 2 + 18,
            fill="#777", width=1
        )
        # Rear windshield line
        self.canvas.create_line(
            cx - cw // 2 + 6, cy + ch // 2 - 18,
            cx + cw // 2 - 6, cy + ch // 2 - 18,
            fill="#777", width=1
        )
        # Front bumper
        self.canvas.create_rectangle(
            cx - cw // 2 + 5, cy - ch // 2 - 5,
            cx + cw // 2 - 5, cy - ch // 2,
            fill="#555555", outline=""
        )
        # Rear bumper
        self.canvas.create_rectangle(
            cx - cw // 2 + 5, cy + ch // 2,
            cx + cw // 2 - 5, cy + ch // 2 + 5,
            fill="#555555", outline=""
        )

        # FRONT / REAR labels
        self.canvas.create_text(cx, cy - 68, text="FRONT",
                                fill="#aaaaaa", font=("Arial", 8, "bold"))
        self.canvas.create_text(cx, cy + 68, text="REAR",
                                fill="#aaaaaa", font=("Arial", 8, "bold"))

        # Clock numbers
        self.hit_areas = {}
        for hour in range(1, 13):
            angle = math.radians(hour * 30 - 90)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)

            selected = hour in self.selected
            fill_color    = "#1f6aa5" if selected else "#3a3a3a"
            outline_color = "#5ba3d9" if selected else "#555555"
            oval_r = 17

            self.canvas.create_oval(
                x - oval_r, y - oval_r, x + oval_r, y + oval_r,
                fill=fill_color, outline=outline_color, width=2
            )
            self.canvas.create_text(
                x, y, text=str(hour), fill="white",
                font=("Arial", 11, "bold")
            )
            self.hit_areas[hour] = (x, y, oval_r)

    def _on_click(self, event):
        for hour, (x, y, r) in self.hit_areas.items():
            if math.sqrt((event.x - x) ** 2 + (event.y - y) ** 2) <= r:
                if hour in self.selected:
                    self.selected.discard(hour)
                else:
                    self.selected.add(hour)
                self._render_diagram()
                self._update_label()
                if self.command:
                    self.command()
                break

    def _clear(self):
        self.selected.clear()
        self._render_diagram()
        self._update_label()
        if self.command:
            self.command()

    def _update_label(self):
        if self.selected:
            parts = sorted(self.selected)
            text = ", ".join(f"{h} o'clock ({self.CLOCK_LABELS[h]})" for h in parts)
            self.selection_label.configure(text=text, text_color="white")
        else:
            self.selection_label.configure(text="None selected", text_color="gray")

    def get(self) -> str:
        if not self.selected:
            return "Not specified"
        parts = sorted(self.selected)
        return ", ".join(f"{h} o'clock ({self.CLOCK_LABELS[h]})" for h in parts)

    def set(self, value: str):
        self.selected.clear()
        if not value or str(value).strip().lower() == "not specified":
            self._render_diagram()
            self._update_label()
            return

        text = str(value)
        matches = re.findall(r"(\d+)\s*o'clock", text)
        for match in matches:
            hour = int(match)
            if 1 <= hour <= 12:
                self.selected.add(hour)

        if not self.selected:
            for chunk in text.split(","):
                chunk = chunk.strip()
                if not chunk:
                    continue
                try:
                    hour = int(chunk.split()[0])
                    if 1 <= hour <= 12:
                        self.selected.add(hour)
                except ValueError:
                    pass

        self._render_diagram()
        self._update_label()