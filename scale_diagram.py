import csv
import math
import tkinter as tk
from typing import Any, Dict, List, Optional, Tuple

import customtkinter as ctk
from tkinter import filedialog, messagebox


class ScaleDiagramEditor(ctk.CTkToplevel):
    OBJECT_TYPES = ["Vehicle", "Point", "Road Segment", "Skid Mark", "Evidence Marker", "Label"]
    ZOOM_LEVELS = ["25%", "50%", "75%", "100%", "125%", "150%", "200%", "300%", "400%"]
    SCALE_BAR_LENGTHS = ["Auto", "5 ft", "10 ft", "20 ft", "50 ft", "100 ft"]
    SCALE_BAR_POSITIONS = ["Bottom Left", "Bottom Right", "Top Left", "Top Right"]

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Scale Diagram Editor")
        self.geometry("1200x820")
        self.minsize(900, 620)
        self.resizable(True, True)
        self.attributes("-topmost", True)
        self.after(10, self.present)

        self.objects: List[Dict[str, Any]] = []
        self.selected_idx: Optional[int] = None
        self.active_tool = tk.StringVar(value="select")
        self.input_mode = tk.StringVar(value="baseline")
        self.scale_ratio = tk.StringVar(value="1:110")
        self.zoom_factor = 1.0
        self.zoom_level_var = tk.StringVar(value="100%")
        self.scale_bar_length_var = tk.StringVar(value="Auto")
        self.scale_bar_position_var = tk.StringVar(value="Bottom Left")

        self.diagram_dpi = 96.0
        self.scale = self._ratio_to_scale(self.scale_ratio.get()) * self.zoom_factor
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._drag_start = None
        self._pan_start = None
        self._pending_line: Optional[Dict[str, Any]] = None
        self._hover_world: Optional[Tuple[float, float]] = None
        self._tool_buttons: Dict[str, ctk.CTkButton] = {}

        self.gps_ref_lat: Optional[float] = None
        self.gps_ref_lon: Optional[float] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_toolbar()
        self._build_main()
        self._build_statusbar()
        self._update_form_units()
        self._sync_zoom_level()
        self._update_status()
        self._redraw()

    def present(self):
        self.state("normal")
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()

    def _build_toolbar(self):
        bar = ctk.CTkFrame(self, height=52, corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")

        tools = [
            ("↖  Select", "select"),
            ("🚗  Vehicle", "vehicle"),
            ("●  Point", "point"),
            ("━  Road", "road"),
            ("///  Skid", "skid"),
            ("◆  Evidence", "evidence"),
            ("T  Label", "label"),
        ]

        col = 0
        for name, tool in tools:
            btn = ctk.CTkButton(bar, text=name, width=98, height=34, command=lambda t=tool: self._set_tool(t))
            btn.grid(row=0, column=col, padx=3, pady=9)
            self._tool_buttons[tool] = btn
            col += 1

        ctk.CTkLabel(bar, text="|", text_color="gray").grid(row=0, column=col, padx=6)
        col += 1

        ctk.CTkButton(bar, text="＋", width=38, height=34, command=self._zoom_in).grid(
            row=0, column=col, padx=2, pady=9
        )
        col += 1

        ctk.CTkButton(bar, text="－", width=38, height=34, command=self._zoom_out).grid(
            row=0, column=col, padx=2, pady=9
        )
        col += 1

        ctk.CTkLabel(bar, text="Zoom:").grid(row=0, column=col, padx=(12, 2))
        col += 1

        self.zoom_menu = ctk.CTkOptionMenu(
            bar,
            variable=self.zoom_level_var,
            values=self.ZOOM_LEVELS,
            width=110,
            height=34,
            dynamic_resizing=False,
            fg_color="#1f6aa5",
            button_color="#184f7a",
            button_hover_color="#143f61",
            text_color="white",
            dropdown_fg_color="#2b2b2b",
            dropdown_text_color="white",
            dropdown_hover_color="#1f6aa5",
            command=self._set_zoom_level,
        )
        self.zoom_menu.grid(row=0, column=col, padx=2, pady=9)
        col += 1

        ctk.CTkButton(bar, text="Fit All", width=72, height=34, command=self._fit_all).grid(
            row=0, column=col, padx=2, pady=9
        )
        col += 1

        ctk.CTkLabel(bar, text="Scale:").grid(row=0, column=col, padx=(12, 2))
        col += 1

        ctk.CTkOptionMenu(
            bar,
            variable=self.scale_ratio,
            values=["1:110", "1:220"],
            width=78,
            height=34,
            command=lambda _: self._set_scale_ratio(),
        ).grid(row=0, column=col, padx=2, pady=9)
        col += 1

        ctk.CTkLabel(bar, text="Bar:").grid(row=0, column=col, padx=(12, 2))
        col += 1

        ctk.CTkOptionMenu(
            bar,
            variable=self.scale_bar_length_var,
            values=self.SCALE_BAR_LENGTHS,
            width=95,
            height=34,
            command=lambda _: self._redraw(),
        ).grid(row=0, column=col, padx=2, pady=9)
        col += 1

        ctk.CTkLabel(bar, text="Bar Pos:").grid(row=0, column=col, padx=(12, 2))
        col += 1

        ctk.CTkOptionMenu(
            bar,
            variable=self.scale_bar_position_var,
            values=self.SCALE_BAR_POSITIONS,
            width=120,
            height=34,
            command=lambda _: self._redraw(),
        ).grid(row=0, column=col, padx=2, pady=9)
        col += 1

        ctk.CTkButton(bar, text="Export PNG", width=98, height=34, command=self._export_png).grid(
            row=0, column=col, padx=(14, 4), pady=9
        )
        col += 1

        ctk.CTkButton(bar, text="Export PDF", width=98, height=34, command=self._export_pdf).grid(
            row=0, column=col, padx=(4, 4), pady=9
        )
        col += 1

        ctk.CTkButton(bar, text="Import CSV", width=98, height=34, command=self._import_csv).grid(
            row=0, column=col, padx=(4, 4), pady=9
        )

        self._highlight_tool("select")

    def _build_main(self):
        main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=0)
        main.grid_rowconfigure(0, weight=1)

        canvas_bg = ctk.CTkFrame(main, corner_radius=8)
        canvas_bg.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        canvas_bg.grid_rowconfigure(0, weight=1)
        canvas_bg.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_bg, bg="#1a1a1a", cursor="crosshair", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self.canvas.bind("<ButtonPress-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_start)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
        self.canvas.bind("<MouseWheel>", self._on_scroll)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Configure>", lambda _: self._redraw())

        side = ctk.CTkScrollableFrame(main, width=310, corner_radius=8)
        side.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
        side.grid_columnconfigure(0, weight=1)
        self._build_side(side)

    def _build_side(self, p):
        r = 0

        ctk.CTkLabel(p, text="Input Mode", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").grid(
            row=r, column=0, sticky="ew", padx=10, pady=(10, 4)
        )
        r += 1

        mf = ctk.CTkFrame(p, fg_color="transparent")
        mf.grid(row=r, column=0, sticky="ew", padx=10)
        r += 1
        mf.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkRadioButton(
            mf, text="Baseline", variable=self.input_mode, value="baseline", command=self._toggle_mode
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkRadioButton(
            mf, text="GPS", variable=self.input_mode, value="gps", command=self._toggle_mode
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(p, text="Object Type", anchor="w").grid(row=r, column=0, sticky="ew", padx=10, pady=(10, 2))
        r += 1

        self.obj_type_var = tk.StringVar(value="Vehicle")
        self.obj_type_menu = ctk.CTkOptionMenu(
            p,
            variable=self.obj_type_var,
            values=self.OBJECT_TYPES,
            command=lambda _v: self._on_object_type_change(),
        )
        self.obj_type_menu.grid(row=r, column=0, sticky="ew", padx=10)
        r += 1

        ctk.CTkLabel(p, text="Label", anchor="w").grid(row=r, column=0, sticky="ew", padx=10, pady=(6, 2))
        r += 1

        self.lbl_entry = ctk.CTkEntry(p, placeholder_text="e.g. V1, Debris")
        self.lbl_entry.grid(row=r, column=0, sticky="ew", padx=10)
        r += 1

        input_row = r
        r += 1

        self.baseline_frame = ctk.CTkFrame(p, fg_color="transparent")
        self.baseline_frame.grid(row=input_row, column=0, sticky="ew")
        self.baseline_frame.grid_columnconfigure(0, weight=1)

        bf = 0
        ctk.CTkLabel(
            self.baseline_frame,
            text="── Baseline Measurement ──",
            text_color="gray",
            font=ctk.CTkFont(size=11),
        ).grid(row=bf, column=0, sticky="ew", padx=10, pady=(8, 4))
        bf += 1

        self.station_label = ctk.CTkLabel(self.baseline_frame, text="Station (decimal feet)", anchor="w")
        self.station_label.grid(row=bf, column=0, sticky="ew", padx=10, pady=(4, 2))
        bf += 1

        self.station_entry = ctk.CTkEntry(self.baseline_frame, placeholder_text="e.g. 42.5")
        self.station_entry.grid(row=bf, column=0, sticky="ew", padx=10)
        bf += 1

        self.offset_label = ctk.CTkLabel(self.baseline_frame, text="Offset (+Right / -Left, decimal feet)", anchor="w")
        self.offset_label.grid(row=bf, column=0, sticky="ew", padx=10, pady=(4, 2))
        bf += 1

        self.offset_entry = ctk.CTkEntry(self.baseline_frame, placeholder_text="e.g. -8.0")
        self.offset_entry.grid(row=bf, column=0, sticky="ew", padx=10)
        bf += 1

        self.gps_frame = ctk.CTkFrame(p, fg_color="transparent")
        self.gps_frame.grid(row=input_row, column=0, sticky="ew")
        self.gps_frame.grid_remove()
        self.gps_frame.grid_columnconfigure(0, weight=1)

        gf = 0
        ctk.CTkLabel(
            self.gps_frame,
            text="── GPS Coordinates ──",
            text_color="gray",
            font=ctk.CTkFont(size=11),
        ).grid(row=gf, column=0, sticky="ew", padx=10, pady=(8, 4))
        gf += 1

        ctk.CTkLabel(self.gps_frame, text="Latitude", anchor="w").grid(row=gf, column=0, sticky="ew", padx=10, pady=(4, 2))
        gf += 1

        self.lat_entry = ctk.CTkEntry(self.gps_frame, placeholder_text="e.g. 41.256847")
        self.lat_entry.grid(row=gf, column=0, sticky="ew", padx=10)
        gf += 1

        ctk.CTkLabel(self.gps_frame, text="Longitude", anchor="w").grid(row=gf, column=0, sticky="ew", padx=10, pady=(4, 2))
        gf += 1

        self.lon_entry = ctk.CTkEntry(self.gps_frame, placeholder_text="e.g. -96.032541")
        self.lon_entry.grid(row=gf, column=0, sticky="ew", padx=10)
        gf += 1

        ctk.CTkButton(self.gps_frame, text="Set as Origin (0, 0)", height=30, command=self._set_gps_ref).grid(
            row=gf, column=0, sticky="ew", padx=10, pady=(6, 2)
        )
        gf += 1

        self.gps_ref_lbl = ctk.CTkLabel(
            self.gps_frame,
            text="No reference set",
            text_color="gray",
            font=ctk.CTkFont(size=10),
            anchor="w",
        )
        self.gps_ref_lbl.grid(row=gf, column=0, sticky="ew", padx=10)
        gf += 1

        ctk.CTkLabel(p, text="Angle ° (vehicles — 0 = North)", anchor="w").grid(
            row=r, column=0, sticky="ew", padx=10, pady=(6, 2)
        )
        r += 1

        self.angle_entry = ctk.CTkEntry(p, placeholder_text="0")
        self.angle_entry.grid(row=r, column=0, sticky="ew", padx=10)
        r += 1

        ctk.CTkLabel(p, text="Notes", anchor="w").grid(row=r, column=0, sticky="ew", padx=10, pady=(6, 2))
        r += 1

        self.notes_entry = ctk.CTkEntry(p, placeholder_text="Optional")
        self.notes_entry.grid(row=r, column=0, sticky="ew", padx=10)
        r += 1

        ctk.CTkButton(p, text="➕  Add Object", height=36, command=self._add_from_form).grid(
            row=r, column=0, sticky="ew", padx=10, pady=(12, 4)
        )
        r += 1

        nav = ctk.CTkFrame(p, fg_color="transparent")
        nav.grid(row=r, column=0, sticky="ew", padx=10, pady=(6, 2))
        for i in range(3):
            nav.grid_columnconfigure(i, weight=1)

        pan_step = 12.0

        def pan(dx: float, dy: float):
            return lambda: self._pan_view(dx, dy)

        ctk.CTkButton(nav, text="↖", width=34, height=30, command=pan(-pan_step, pan_step)).grid(
            row=0, column=0, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(nav, text="↑", width=34, height=30, command=pan(0.0, pan_step)).grid(
            row=0, column=1, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(nav, text="↗", width=34, height=30, command=pan(pan_step, pan_step)).grid(
            row=0, column=2, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(nav, text="←", width=34, height=30, command=pan(-pan_step, 0.0)).grid(
            row=1, column=0, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(nav, text="Recenter", width=34, height=30, command=self._recenter_view).grid(
            row=1, column=1, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(nav, text="→", width=34, height=30, command=pan(pan_step, 0.0)).grid(
            row=1, column=2, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(nav, text="↙", width=34, height=30, command=pan(-pan_step, -pan_step)).grid(
            row=2, column=0, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(nav, text="↓", width=34, height=30, command=pan(0.0, -pan_step)).grid(
            row=2, column=1, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(nav, text="↘", width=34, height=30, command=pan(pan_step, -pan_step)).grid(
            row=2, column=2, padx=2, pady=2, sticky="ew"
        )

        r += 1

        ctk.CTkLabel(p, text="──────────────────", text_color="gray", anchor="w").grid(
            row=r, column=0, padx=10, pady=6
        )
        r += 1

        ctk.CTkLabel(p, text="Objects", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").grid(
            row=r, column=0, sticky="ew", padx=10, pady=(4, 4)
        )
        r += 1

        lf = ctk.CTkFrame(p, fg_color="transparent")
        lf.grid(row=r, column=0, sticky="ew", padx=10)
        r += 1
        lf.grid_columnconfigure(0, weight=1)

        self.obj_listbox = tk.Listbox(
            lf,
            height=9,
            exportselection=False,
            bg="#2b2b2b",
            fg="white",
            selectbackground="#1f6aa5",
            borderwidth=0,
            highlightthickness=0,
            font=("Arial", 10),
        )
        self.obj_listbox.grid(row=0, column=0, sticky="ew")
        self.obj_listbox.bind("<<ListboxSelect>>", self._on_list_select)

        bf2 = ctk.CTkFrame(p, fg_color="transparent")
        bf2.grid(row=r, column=0, sticky="ew", padx=10, pady=(4, 0))
        r += 1
        bf2.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(bf2, text="Edit", height=30, command=self._edit_selected).grid(
            row=0, column=0, padx=(0, 3), sticky="ew"
        )
        ctk.CTkButton(bf2, text="Delete", height=30, command=self._delete_selected).grid(
            row=0, column=1, padx=(3, 0), sticky="ew"
        )

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, height=28, corner_radius=0)
        bar.grid(row=2, column=0, sticky="ew")

        self.status_var = tk.StringVar(value="Tool: Select  |  Scroll to zoom  |  Right-click drag to pan")
        ctk.CTkLabel(bar, textvariable=self.status_var, anchor="w", font=ctk.CTkFont(size=11)).pack(
            side="left", padx=10
        )

        self.coord_var = tk.StringVar(value="")
        ctk.CTkLabel(bar, textvariable=self.coord_var, anchor="e", font=ctk.CTkFont(size=11)).pack(
            side="right", padx=10
        )

    def _ratio_to_scale(self, ratio_text: str) -> float:
        ratio = int(ratio_text.split(":")[1])
        return self.diagram_dpi / ratio

    def _feet_to_inches(self, value: float) -> float:
        return value * 12.0

    def _inches_to_feet(self, value: float) -> float:
        return value / 12.0

    def _format_feet(self, inches: float, decimals: int = 2) -> str:
        return f"{self._inches_to_feet(inches):.{decimals}f}"

    def _update_form_units(self):
        self.station_label.configure(text="Station (decimal feet)")
        self.offset_label.configure(text="Offset (+Right / -Left, decimal feet)")

    def _on_object_type_change(self):
        self._update_form_units()

    def _rescale(self, zoom_factor: Optional[float] = None, focal: Optional[Tuple[float, float]] = None):
        cw = self.canvas.winfo_width() or 600
        ch = self.canvas.winfo_height() or 400
        fx, fy = focal if focal is not None else (cw / 2, ch / 2)
        before_x, before_y = self._c2w(fx, fy)

        if zoom_factor is not None:
            self.zoom_factor = max(0.1, min(10.0, zoom_factor))

        self.scale = self._ratio_to_scale(self.scale_ratio.get()) * self.zoom_factor
        self._sync_zoom_level()
        self.offset_x = fx - cw / 2 - before_x * self.scale
        self.offset_y = fy - ch / 2 + before_y * self.scale
        self._redraw()
        self._update_status()

    def _set_scale_ratio(self):
        self._rescale(zoom_factor=self.zoom_factor)

    def _set_zoom_level(self, value: str):
        zoom_text = value.strip().replace("%", "")
        self._rescale(zoom_factor=float(zoom_text) / 100.0)

    def _sync_zoom_level(self):
        self.zoom_level_var.set(f"{int(round(self.zoom_factor * 100))}%")

    def _w2c(self, wx, wy):
        cw = self.canvas.winfo_width() or 600
        ch = self.canvas.winfo_height() or 400
        return cw / 2 + self.offset_x + wx * self.scale, ch / 2 + self.offset_y - wy * self.scale

    def _c2w(self, cx, cy):
        cw = self.canvas.winfo_width() or 600
        ch = self.canvas.winfo_height() or 400
        return (cx - cw / 2 - self.offset_x) / self.scale, -(cy - ch / 2 - self.offset_y) / self.scale

    def _update_status(self):
        self.status_var.set(
            f"Tool: {self.active_tool.get().title()}  |  Scale: {self.scale_ratio.get()}  |  Zoom: {self.zoom_level_var.get()}  |  Right-click drag to pan"
        )

    def _set_tool(self, tool):
        self.active_tool.set(tool)
        self._highlight_tool(tool)
        self._update_status()

    def _highlight_tool(self, active):
        active_color = "#1f6aa5"
        default_color = "#3b3b3b"
        for tool, btn in self._tool_buttons.items():
            btn.configure(fg_color=active_color if tool == active else default_color)

    def _toggle_mode(self):
        if self.input_mode.get() == "baseline":
            self.gps_frame.grid_remove()
            self.baseline_frame.grid()
        else:
            self.baseline_frame.grid_remove()
            self.gps_frame.grid()

    def _set_gps_ref(self):
        try:
            lat = float(self.lat_entry.get())
            lon = float(self.lon_entry.get())
            self.gps_ref_lat = lat
            self.gps_ref_lon = lon
            self.gps_ref_lbl.configure(text=f"Ref: {lat:.6f}, {lon:.6f}", text_color="#5ba3d9")
        except ValueError:
            messagebox.showerror("Invalid Input", "Enter valid decimal lat/lon values.")

    def _gps_to_local(self, lat, lon):
        if self.gps_ref_lat is None or self.gps_ref_lon is None:
            raise ValueError("Set a GPS reference point first.")
        dx_m = (lon - self.gps_ref_lon) * 111320 * math.cos(math.radians(self.gps_ref_lat))
        dy_m = (lat - self.gps_ref_lat) * 111320
        inches_per_meter = 39.37007874015748
        return dx_m * inches_per_meter, dy_m * inches_per_meter

    def _pan_view(self, dx_inches: float, dy_inches: float):
        self.offset_x += dx_inches * self.scale
        self.offset_y += dy_inches * self.scale
        self._redraw()

    def _recenter_view(self):
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._redraw()

    def _on_click(self, event):
        tool = self.active_tool.get()
        wx, wy = self._c2w(event.x, event.y)

        if tool == "select":
            self._try_select(event.x, event.y)
            self._drag_start = (event.x, event.y)
            return

        type_map = {
            "vehicle": "Vehicle",
            "point": "Point",
            "road": "Road Segment",
            "skid": "Skid Mark",
            "evidence": "Evidence Marker",
            "label": "Label",
        }
        prefix_map = {
            "Vehicle": "V",
            "Point": "P",
            "Road Segment": "R",
            "Skid Mark": "S",
            "Evidence Marker": "E",
            "Label": "L",
        }
        if tool in type_map:
            otype = type_map[tool]
            n = len(self.objects) + 1
            obj = {
                "type": otype,
                "x": round(wx, 2),
                "y": round(wy, 2),
                "end_x": round(wx + 15, 2),
                "end_y": round(wy, 2),
                "label": f"{prefix_map[otype]}{n}",
                "angle": 0.0,
                "notes": "",
            }
            self.objects.append(obj)
            self._refresh_list()
            self._redraw()

    def _on_drag(self, event):
        if self.active_tool.get() == "select" and self._drag_start and self.selected_idx is not None:
            dx = (event.x - self._drag_start[0]) / self.scale
            dy = -(event.y - self._drag_start[1]) / self.scale
            obj = self.objects[self.selected_idx]
            obj["x"] = round(obj["x"] + dx, 2)
            obj["y"] = round(obj["y"] + dy, 2)
            obj["end_x"] = round(obj.get("end_x", obj["x"]) + dx, 2)
            obj["end_y"] = round(obj.get("end_y", obj["y"]) + dy, 2)
            self._drag_start = (event.x, event.y)
            self._redraw()

    def _on_release(self, _event):
        self._drag_start = None

    def _on_pan_start(self, event):
        self._pan_start = (event.x, event.y, self.offset_x, self.offset_y)

    def _on_pan_drag(self, event):
        if self._pan_start:
            sx, sy, ox, oy = self._pan_start
            self.offset_x = ox + (event.x - sx)
            self.offset_y = oy + (event.y - sy)
            self._redraw()

    def _on_scroll(self, event):
        factor = 1.12 if event.delta > 0 else 0.89
        self._rescale(zoom_factor=self.zoom_factor * factor, focal=(event.x, event.y))

    def _on_mouse_move(self, event):
        wx, wy = self._c2w(event.x, event.y)
        self.coord_var.set(
            f"X: {self._format_feet(wx)} ft   Y: {self._format_feet(wy)} ft"
        )

    def _try_select(self, cx, cy):
        hit = 20
        self.selected_idx = None
        self.obj_listbox.selection_clear(0, tk.END)

        for i, obj in enumerate(self.objects):
            ox, oy = self._w2c(obj["x"], obj["y"])
            if math.hypot(cx - ox, cy - oy) <= hit:
                self.selected_idx = i
                self.obj_listbox.selection_set(i)
                break

        self._redraw()

    def _on_list_select(self, _event):
        sel = self.obj_listbox.curselection()
        self.selected_idx = sel[0] if sel else None
        self._redraw()

    def _refresh_list(self):
        self.obj_listbox.delete(0, tk.END)
        for i, obj in enumerate(self.objects):
            self.obj_listbox.insert(tk.END, f"{i + 1}. [{obj['type']}] {obj['label']}")

    def _add_from_form(self):
        try:
            otype = self.obj_type_var.get()
            if self.input_mode.get() == "baseline":
                station_ft = float(self.station_entry.get())
                offset_ft = float(self.offset_entry.get())
                wx = self._feet_to_inches(station_ft)
                wy = self._feet_to_inches(offset_ft)
            else:
                lat = float(self.lat_entry.get())
                lon = float(self.lon_entry.get())
                wx, wy = self._gps_to_local(lat, lon)

            angle_str = self.angle_entry.get().strip()
            angle = float(angle_str) if angle_str else 0.0
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid coordinates:\n{e}")
            return

        label = self.lbl_entry.get().strip() or f"{otype[0]}{len(self.objects) + 1}"
        notes = self.notes_entry.get().strip()

        obj = {
            "type": otype,
            "x": round(wx, 2),
            "y": round(wy, 2),
            "end_x": round(wx + 15, 2),
            "end_y": round(wy, 2),
            "label": label,
            "angle": angle,
            "notes": notes,
        }
        self.objects.append(obj)
        self._refresh_list()
        self._redraw()
        self._fit_all()

    def _edit_selected(self):
        if self.selected_idx is None:
            messagebox.showinfo("No Selection", "Select an object from the list first.")
            return
        dlg = ObjectEditDialog(self, self.objects[self.selected_idx])
        self.wait_window(dlg)
        if dlg.result:
            self.objects[self.selected_idx] = dlg.result
            self._refresh_list()
            self._redraw()

    def _delete_selected(self):
        if self.selected_idx is None:
            return
        del self.objects[self.selected_idx]
        self.selected_idx = None
        self.obj_listbox.selection_clear(0, tk.END)
        self._refresh_list()
        self._redraw()

    def _zoom_in(self):
        self._rescale(zoom_factor=self.zoom_factor * 1.25)

    def _zoom_out(self):
        self._rescale(zoom_factor=self.zoom_factor / 1.25)

    def _fit_all(self):
        if not self.objects:
            return

        xs = [o["x"] for o in self.objects] + [o.get("end_x", o["x"]) for o in self.objects]
        ys = [o["y"] for o in self.objects] + [o.get("end_y", o["y"]) for o in self.objects]
        span_x = max(max(xs) - min(xs), 1)
        span_y = max(max(ys) - min(ys), 1)

        cw = self.canvas.winfo_width() or 600
        ch = self.canvas.winfo_height() or 400

        base_scale = self._ratio_to_scale(self.scale_ratio.get())
        target_scale = min(cw * 0.75 / span_x, ch * 0.75 / span_y)
        self.zoom_factor = max(0.1, min(10.0, target_scale / base_scale))
        self.scale = base_scale * self.zoom_factor
        self._sync_zoom_level()

        cx_mid = (min(xs) + max(xs)) / 2
        cy_mid = (min(ys) + max(ys)) / 2
        self.offset_x = cw / 2 - cx_mid * self.scale
        self.offset_y = ch / 2 + cy_mid * self.scale
        self._redraw()
        self._update_status()

    def _redraw(self):
        self.canvas.delete("all")
        self._draw_grid()
        self._draw_origin()
        self._draw_scale_bar()
        for i, obj in enumerate(self.objects):
            self._draw_obj(obj, selected=(i == self.selected_idx))

    def _draw_grid(self):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 4 or ch < 4:
            return

        raw = 60.0 / self.scale
        mag = 10 ** math.floor(math.log10(max(raw, 1e-6)))
        grid_w = next((mag * m for m in (1, 2, 5, 10) if mag * m >= raw), mag * 10)

        x0, y0 = self._c2w(0, 0)
        x1, y1 = self._c2w(cw, ch)

        x = math.floor(x0 / grid_w) * grid_w
        while x <= x1:
            px, _ = self._w2c(x, 0)
            is_axis = abs(x) < grid_w * 0.01
            self.canvas.create_line(px, 0, px, ch, fill="#3a3a3a" if is_axis else "#252525", width=1)
            if not is_axis and abs(x) > 0.001:
                self.canvas.create_text(
                    px + 3,
                    ch - 14,
                    text=f"{self._inches_to_feet(x):.0f}",
                    fill="#444",
                    font=("Arial", 8),
                    anchor="w",
                )
            x += grid_w

        y = math.floor(y1 / grid_w) * grid_w
        while y <= y0:
            _, py = self._w2c(0, y)
            is_axis = abs(y) < grid_w * 0.01
            self.canvas.create_line(0, py, cw, py, fill="#3a3a3a" if is_axis else "#252525", width=1)
            if not is_axis and abs(y) > 0.001:
                self.canvas.create_text(
                    8,
                    py - 3,
                    text=f"{self._inches_to_feet(y):.0f}",
                    fill="#444",
                    font=("Arial", 8),
                    anchor="w",
                )
            y += grid_w

    def _draw_origin(self):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        ox, oy = self._w2c(0, 0)
        self.canvas.create_line(ox, 0, ox, ch, fill="#4a4a4a", width=1, dash=(6, 4))
        self.canvas.create_line(0, oy, cw, oy, fill="#4a4a4a", width=1, dash=(6, 4))
        self.canvas.create_text(ox + 6, 14, text="N ↑", fill="#666", font=("Arial", 9, "bold"), anchor="w")

    def _draw_scale_bar(self):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return

        selected = self.scale_bar_length_var.get().strip()
        if selected == "Auto":
            raw_inches = 80.0 / self.scale
            mag = 10 ** math.floor(math.log10(max(raw_inches, 1e-6)))
            bar_w_inches = next((mag * m for m in (1, 2, 5, 10) if mag * m >= raw_inches), mag * 10)
        else:
            feet = float(selected.replace("ft", "").strip())
            bar_w_inches = feet * 12.0

        bar_px = bar_w_inches * self.scale
        bar_w_feet = bar_w_inches / 12.0
        pos = self.scale_bar_position_var.get()
        margin = 20

        if pos == "Bottom Left":
            x1, y1 = margin, ch - 28
        elif pos == "Bottom Right":
            x1, y1 = max(margin, cw - margin - bar_px), ch - 28
        elif pos == "Top Left":
            x1, y1 = margin, 28
        else:
            x1, y1 = max(margin, cw - margin - bar_px), 28

        x2 = x1 + bar_px

        self.canvas.create_line(x1, y1, x2, y1, fill="#aaa", width=3)
        self.canvas.create_line(x1, y1 - 5, x1, y1 + 5, fill="#aaa", width=2)
        self.canvas.create_line(x2, y1 - 5, x2, y1 + 5, fill="#aaa", width=2)

        label = f"{bar_w_feet:.0f} ft" if bar_w_feet.is_integer() else f"{bar_w_feet:.1f} ft"
        text_y = y1 - 11 if "Bottom" in pos else y1 + 11
        self.canvas.create_text((x1 + x2) / 2, text_y, text=label, fill="#aaa", font=("Arial", 9))

    def _draw_obj(self, obj, selected):
        cx, cy = self._w2c(obj["x"], obj["y"])
        otype = obj["type"]
        label = obj["label"]
        sel = "#5ba3d9"

        if otype == "Vehicle":
            self._draw_vehicle(cx, cy, obj.get("angle", 0), label, selected)

        elif otype == "Point":
            size = 9
            color = "#e74c3c"
            line_w = 4 if selected else 3
            self.canvas.create_line(cx - size, cy - size, cx + size, cy + size, fill=color, width=line_w)
            self.canvas.create_line(cx - size, cy + size, cx + size, cy - size, fill=color, width=line_w)
            self.canvas.create_text(cx, cy - 18, text=label, fill="white", font=("Arial", 9, "bold"))

        elif otype in ("Road Segment", "Skid Mark"):
            ex, ey = self._w2c(obj.get("end_x", obj["x"] + 15), obj.get("end_y", obj["y"]))
            color = "#888" if otype == "Road Segment" else "#444"
            dash = None if otype == "Road Segment" else (10, 5)
            width = 7 if otype == "Road Segment" else 4
            if selected:
                self.canvas.create_line(cx, cy, ex, ey, fill=sel, width=width + 6, dash=dash, capstyle="round")
            self.canvas.create_line(cx, cy, ex, ey, fill=color, width=width, dash=dash, capstyle="round")
            length = math.hypot(
                obj.get("end_x", obj["x"] + 15) - obj["x"],
                obj.get("end_y", obj["y"]) - obj["y"],
            )
            mx, my = (cx + ex) / 2, (cy + ey) / 2
            self.canvas.create_text(
                mx,
                my - 10,
                fill="#aaa",
                font=("Arial", 8),
                text=f"{label} ({self._inches_to_feet(length):.1f} ft)",
            )

        elif otype == "Evidence Marker":
            pts = [cx, cy - 11, cx + 10, cy + 6, cx - 10, cy + 6]
            self.canvas.create_polygon(pts, fill="#f39c12", outline=sel if selected else "#d68910", width=2)
            self.canvas.create_text(cx, cy - 20, text=label, fill="white", font=("Arial", 9, "bold"))

        elif otype == "Label":
            tw = len(label) * 7 + 8
            self.canvas.create_rectangle(cx, cy - 12, cx + tw, cy + 6, fill=sel if selected else "#2c2c2c", outline="")
            self.canvas.create_text(cx + 4, cy - 3, text=label, fill="white", font=("Arial", 10), anchor="w")

        if selected:
            self.canvas.create_text(
                cx + 14,
                cy + 14,
                text=f"({self._format_feet(obj['x'], 1)}, {self._format_feet(obj['y'], 1)}) ft",
                fill=sel,
                font=("Arial", 8),
                anchor="w",
            )

    def _draw_vehicle(self, cx, cy, angle_deg, label, selected):
        vw = max(10, min(28, int(8 * self.scale / 18)))
        vh = max(16, min(48, int(15 * self.scale / 18)))
        a = math.radians(-angle_deg)
        ca, sa = math.cos(a), math.sin(a)

        def rot(rx, ry):
            return cx + rx * ca - ry * sa, cy + rx * sa + ry * ca

        corners = [rot(-vw, -vh), rot(vw, -vh), rot(vw, vh), rot(-vw, vh)]
        flat = [c for pt in corners for c in pt]
        self.canvas.create_polygon(
            flat,
            fill="#4a90d9",
            outline="#5ba3d9" if selected else "#2c6fad",
            width=3 if selected else 2,
        )

        arr = vh * 0.65
        ax = cx + arr * math.sin(math.radians(angle_deg))
        ay = cy - arr * math.cos(math.radians(angle_deg))
        self.canvas.create_line(cx, cy, ax, ay, fill="white", width=2, arrow="last")
        self.canvas.create_text(cx, cy + vh + 12, text=label, fill="white", font=("Arial", 9, "bold"))

    def _capture_canvas_image(self):
        try:
            from PIL import ImageGrab
        except ImportError:
            messagebox.showerror("Missing Library", "Install Pillow first:\n\npip install Pillow")
            return None

        self.update_idletasks()
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        return ImageGrab.grab(bbox=(x, y, x + w, y + h))

    def _export_png(self):
        image = self._capture_canvas_image()
        if image is None:
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
            title="Export Diagram as PNG",
        )
        if not path:
            return

        image.save(path)
        messagebox.showinfo("Saved", f"Diagram saved to:\n{path}")

    def _export_pdf(self):
        image = self._capture_canvas_image()
        if image is None:
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            title="Export Diagram as PDF",
        )
        if not path:
            return

        image.convert("RGB").save(path, "PDF", resolution=96.0)
        messagebox.showinfo("Saved", f"Diagram saved to:\n{path}")

    def _import_csv(self):
        path = filedialog.askopenfilename(
            title="Import Scale Diagram CSV",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return

        imported = []
        prefix_map = {
            "Vehicle": "V",
            "Point": "P",
            "Road Segment": "R",
            "Skid Mark": "S",
            "Evidence Marker": "E",
            "Label": "L",
        }

        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                messagebox.showerror("Import Error", "CSV file is missing a header row.")
                return

            for row_num, row in enumerate(reader, start=2):
                try:
                    otype = (row.get("type") or "").strip()
                    if otype not in self.OBJECT_TYPES:
                        raise ValueError(f"Invalid type '{otype}'")

                    label = (row.get("label") or "").strip()
                    mode = (row.get("mode") or "baseline").strip().lower()
                    angle = float(row.get("angle_deg") or 0)
                    notes = (row.get("notes") or "").strip()

                    if mode == "gps":
                        lat = float(row.get("lat") or "")
                        lon = float(row.get("lon") or "")
                        wx, wy = self._gps_to_local(lat, lon)
                    elif mode == "baseline":
                        station_ft = float(row.get("station_ft") or "")
                        offset_ft = float(row.get("offset_ft") or "")
                        wx = self._feet_to_inches(station_ft)
                        wy = self._feet_to_inches(offset_ft)
                    else:
                        raise ValueError(f"Invalid mode '{mode}'")

                    imported.append(
                        {
                            "type": otype,
                            "x": round(wx, 2),
                            "y": round(wy, 2),
                            "end_x": round(wx + 15, 2),
                            "end_y": round(wy, 2),
                            "label": label or f"{prefix_map[otype]}{len(self.objects) + len(imported) + 1}",
                            "angle": angle,
                            "notes": notes,
                        }
                    )
                except Exception as exc:
                    messagebox.showerror("Import Error", f"Row {row_num} could not be imported:\n{exc}")
                    return

        self.objects.extend(imported)
        self._refresh_list()
        self._redraw()
        self._fit_all()


class ObjectEditDialog(ctk.CTkToplevel):
    FEET_FIELDS = {"x", "y", "end_x", "end_y"}
    FIELDS = [
        ("Label", "label"),
        ("X (ft)", "x"),
        ("Y (ft)", "y"),
        ("End X (ft)", "end_x"),
        ("End Y (ft)", "end_y"),
        ("Angle °", "angle"),
        ("Notes", "notes"),
    ]

    def __init__(self, master, obj: dict, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Edit Object")
        self.geometry("340x520")
        self.resizable(False, False)
        self.transient(master)
        self.lift()
        self.focus_force()
        self.after(1, self.lift)
        self.after(1, self.focus_force)

        self.obj = dict(obj)
        self.result = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.scroll.grid_columnconfigure(0, weight=1)

        self._build()

    def _display_value(self, key: str) -> str:
        value = self.obj.get(key, "")
        if key in self.FEET_FIELDS:
            return f"{float(value) / 12.0:.2f}"
        return str(value)

    def _build(self):
        self.entries: Dict[str, ctk.CTkEntry] = {}

        for row, (lbl, key) in enumerate(self.FIELDS):
            ctk.CTkLabel(self.scroll, text=lbl, anchor="w").grid(
                row=row * 2, column=0, sticky="ew", padx=8, pady=(8, 2)
            )
            e = ctk.CTkEntry(self.scroll)
            e.insert(0, self._display_value(key))
            e.grid(row=row * 2 + 1, column=0, sticky="ew", padx=8)
            self.entries[key] = e

        n = len(self.FIELDS) * 2
        bf = ctk.CTkFrame(self.scroll, fg_color="transparent")
        bf.grid(row=n, column=0, sticky="ew", padx=8, pady=12)
        bf.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(bf, text="Save", command=self._save).grid(
            row=0, column=0, padx=(0, 4), sticky="ew"
        )
        ctk.CTkButton(bf, text="Cancel", command=self.destroy).grid(
            row=0, column=1, padx=(4, 0), sticky="ew"
        )

    def _save(self):
        try:
            self.obj["label"] = self.entries["label"].get().strip()
            self.obj["x"] = float(self.entries["x"].get()) * 12.0
            self.obj["y"] = float(self.entries["y"].get()) * 12.0
            self.obj["end_x"] = float(self.entries["end_x"].get() or (self.obj["x"] / 12.0)) * 12.0
            self.obj["end_y"] = float(self.entries["end_y"].get() or (self.obj["y"] / 12.0)) * 12.0
            self.obj["angle"] = float(self.entries["angle"].get() or 0)
            self.obj["notes"] = self.entries["notes"].get().strip()
            self.result = self.obj
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid", "X, Y, End X, End Y, and Angle must be numbers.")