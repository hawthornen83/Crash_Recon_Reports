import tkinter as tk
from typing import List, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox
from docx import Document

from constants import (
    INCIDENT_TYPES, OFFICER_RANKS, COLLISION_TYPES,
    WEATHER_CONDITIONS, LIGHTING_CONDITIONS, SURFACE_CONDITIONS,
    TRAFFIC_CONTROL_TYPES
)
from dialogs import PersonDialog, VehicleDialog
from impact_diagram import ImpactDiagram
from models import InvolvedPerson, Vehicle
from scale_diagram import ScaleDiagramEditor


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CrashReconReportApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Crash Reconstruction Report")
        self.geometry("1500x980")
        self.minsize(1220, 780)

        self.vehicles: List[Vehicle] = []
        self.involved_people: List[InvolvedPerson] = []
        self.scale_editor: Optional[ScaleDiagramEditor] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main = ctk.CTkFrame(self, corner_radius=18)
        self.main.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_columnconfigure(0, weight=2)
        self.main.grid_columnconfigure(1, weight=3)

        self.input_panel = ctk.CTkScrollableFrame(self.main, width=560, height=900, corner_radius=14, fg_color="transparent")
        self.input_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 10), pady=10)
        self.input_panel.grid_columnconfigure(0, weight=1)

        self.preview_panel = ctk.CTkScrollableFrame(self.main, width=700, height=900, corner_radius=14, fg_color="transparent")
        self.preview_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        self.preview_panel.grid_columnconfigure(0, weight=1)

        self.fields = {}
        self._build_input()
        self._build_preview()
        self._set_defaults()
        self._bind_live_updates()
        self.refresh_vehicle_list()
        self.refresh_people_list()
        self.update_preview()

    def _build_input(self):
        ctk.CTkLabel(self.input_panel, text="Crash Reconstruction Report",
                     font=ctk.CTkFont(size=30, weight="bold"), anchor="w").grid(
            row=0, column=0, sticky="ew", padx=10, pady=(10, 18))

        self._section_title("Case Information", 1)
        self.fields["case_number"]  = self.add_field("Case Number", 2)
        self.fields["report_date"]  = self.add_field("Report Date", 3)
        self.fields["crash_date"]   = self.add_field("Crash Date", 4)
        self.fields["crash_time"]   = self.add_field("Crash Time (24hr)", 5)
        self.fields["incident_type"]= self.add_dropdown("Incident Type", 6, INCIDENT_TYPES)
        self.fields["location"]     = self.add_field("Crash Location", 7)
        self.fields["county"]       = self.add_field("County", 8)
        self.fields["city"]         = self.add_field("City", 9)
        self.fields["agency"]       = self.add_field("Agency", 10)
        self.fields["officer"]      = self.add_field("Investigating Officer", 11)
        self.fields["badge"]        = self.add_field("Badge / Serial Number", 12)
        self.fields["officer_rank"] = self.add_dropdown("Officer Rank", 13, OFFICER_RANKS)

        self._section_title("Crash Details", 14)
        self.fields["collision_type"]  = self.add_dropdown("Collision Type", 15, COLLISION_TYPES)
        self.fields["roadway"]         = self.add_field("Roadway / Route", 16)
        self.fields["weather"]         = self.add_dropdown("Weather", 17, WEATHER_CONDITIONS)
        self.fields["lighting"]        = self.add_dropdown("Lighting Conditions", 18, LIGHTING_CONDITIONS)
        self.fields["surface"]         = self.add_dropdown("Surface Condition", 19, SURFACE_CONDITIONS)
        self.fields["speed_limit"]     = self.add_field("Speed Limit", 20)
        self.fields["traffic_control"] = self.add_dropdown("Traffic Control", 21, TRAFFIC_CONTROL_TYPES)

        self.fields["point_of_impact"] = ImpactDiagram(self.input_panel, command=self.update_preview)
        self.fields["point_of_impact"].grid(row=22, column=0, sticky="ew", padx=10, pady=(0, 8))

        self.fields["scene_desc"] = self.add_field("Scene Description", 23)

        self._section_title("Scale Diagram", 24)
        ctk.CTkButton(self.input_panel, text="Open Scale Diagram Editor",
                      height=36, command=self.open_scale_diagram).grid(
            row=25, column=0, sticky="ew", padx=10, pady=(0, 10))

        self._section_title("Vehicles", 26)
        vehicle_row = ctk.CTkFrame(self.input_panel, fg_color="transparent")
        vehicle_row.grid(row=27, column=0, sticky="ew", padx=10, pady=(0, 8))
        for col in (0, 1, 2):
            vehicle_row.grid_columnconfigure(col, weight=1)

        ctk.CTkButton(vehicle_row, text="Add Vehicle",    command=self.add_vehicle).grid(row=0, column=0, padx=6, sticky="ew")
        ctk.CTkButton(vehicle_row, text="Edit Vehicle",   command=self.edit_vehicle).grid(row=0, column=1, padx=6, sticky="ew")
        ctk.CTkButton(vehicle_row, text="Delete Vehicle", command=self.delete_vehicle).grid(row=0, column=2, padx=6, sticky="ew")

        list_frame = ctk.CTkFrame(self.input_panel, fg_color="transparent")
        list_frame.grid(row=28, column=0, sticky="ew", padx=10, pady=(0, 10))
        list_frame.grid_columnconfigure(0, weight=1)
        self.vehicle_listbox = tk.Listbox(list_frame, height=6, exportselection=False)
        self.vehicle_listbox.grid(row=0, column=0, sticky="ew")

        self._section_title("Involved Person", 29)
        people_row = ctk.CTkFrame(self.input_panel, fg_color="transparent")
        people_row.grid(row=30, column=0, sticky="ew", padx=10, pady=(0, 8))
        for col in (0, 1, 2):
            people_row.grid_columnconfigure(col, weight=1)

        ctk.CTkButton(people_row, text="Add Person",    command=self.add_person).grid(row=0, column=0, padx=6, sticky="ew")
        ctk.CTkButton(people_row, text="Edit Person",   command=self.edit_person).grid(row=0, column=1, padx=6, sticky="ew")
        ctk.CTkButton(people_row, text="Delete Person", command=self.delete_person).grid(row=0, column=2, padx=6, sticky="ew")

        ppl_frame = ctk.CTkFrame(self.input_panel, fg_color="transparent")
        ppl_frame.grid(row=31, column=0, sticky="ew", padx=10, pady=(0, 10))
        ppl_frame.grid_columnconfigure(0, weight=1)
        self.people_listbox = tk.Listbox(ppl_frame, height=6, exportselection=False)
        self.people_listbox.grid(row=0, column=0, sticky="ew")

        self._section_title("Narrative / Reconstruction Findings", 32)
        self.fields["narrative"] = ctk.CTkTextbox(self.input_panel, height=220, corner_radius=10, border_width=1)
        self.fields["narrative"].grid(row=33, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def open_scale_diagram(self):
        if self.scale_editor is None or not self.scale_editor.winfo_exists():
            self.scale_editor = ScaleDiagramEditor(self)
        else:
            self.scale_editor.present()

    def _build_preview(self):
        ctk.CTkLabel(self.preview_panel, text="Live Final Report",
                     font=ctk.CTkFont(size=24, weight="bold"), anchor="w").grid(
            row=0, column=0, sticky="ew", padx=10, pady=(10, 10))
        self.preview_text = ctk.CTkTextbox(self.preview_panel, height=800, width=620,
                                            corner_radius=10, border_width=1)
        self.preview_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.preview_text.configure(state="disabled")

        export_row = ctk.CTkFrame(self.preview_panel, fg_color="transparent")
        export_row.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        ctk.CTkButton(export_row, text="Export .txt",  command=self.export_txt).pack(side="left", padx=(0, 8))
        ctk.CTkButton(export_row, text="Export .docx", command=self.export_docx).pack(side="left")

    def _set_defaults(self):
        self.fields["case_number"].insert(0, "CR-2026-014")
        self.fields["report_date"].insert(0, "08/18/2026")
        self.fields["crash_date"].insert(0, "08/18/2026")
        self.fields["crash_time"].insert(0, "15:42")
        self.fields["incident_type"].set("Traffic Crash")
        self.fields["location"].insert(0, "Highway 275 & Blondo St.")
        self.fields["county"].insert(0, "Douglas")
        self.fields["city"].insert(0, "Waterloo")
        self.fields["agency"].insert(0, "Waterloo Police Department")
        self.fields["officer"].insert(0, "N. Hawthorne")
        self.fields["badge"].insert(0, "W147")
        self.fields["officer_rank"].set("Officer")
        self.fields["collision_type"].set("Angle")
        self.fields["roadway"].insert(0, "Highway 275")
        self.fields["weather"].set("Clear")
        self.fields["lighting"].set("Daylight")
        self.fields["surface"].set("Dry")
        self.fields["speed_limit"].insert(0, "45 MPH")
        self.fields["traffic_control"].set("Traffic Signal")
        self.fields["scene_desc"].insert(0, "Dry roadway, no debris field, moderate skid marks, clear sightlines.")
        self.fields["narrative"].insert("0.0", "Enter reconstruction narrative here.")

    def _bind_live_updates(self):
        for widget in self.fields.values():
            if isinstance(widget, ctk.CTkEntry):
                widget.bind("<KeyRelease>", lambda _e: self.update_preview())
            elif isinstance(widget, ctk.CTkTextbox):
                widget.bind("<KeyRelease>", lambda _e: self.update_preview())

    def _section_title(self, text: str, row: int):
        ctk.CTkLabel(self.input_panel, text=text,
                     font=ctk.CTkFont(size=18, weight="bold"), anchor="w").grid(
            row=row, column=0, sticky="ew", padx=10, pady=(14, 8))

    def add_field(self, label_text: str, row: int):
        frame = ctk.CTkFrame(self.input_panel, corner_radius=10, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 8))
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=label_text, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=2, pady=(0, 4))
        entry = ctk.CTkEntry(frame, width=420, height=32)
        entry.grid(row=1, column=0, sticky="ew", padx=2)
        return entry

    def add_dropdown(self, label_text: str, row: int, values: List[str]):
        frame = ctk.CTkFrame(self.input_panel, corner_radius=10, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 8))
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=label_text, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=2, pady=(0, 4))
        menu = ctk.CTkOptionMenu(frame, values=values, width=420)
        menu.grid(row=1, column=0, sticky="ew", padx=2)
        menu.configure(command=lambda *_: self.update_preview())
        return menu

    def vehicle_label(self, v: Vehicle, idx: int) -> str:
        base = f"{idx + 1}. {v.year} {v.make} {v.model}".strip()
        return f"{base} | Plate: {v.plate}" if v.plate else base

    def refresh_vehicle_list(self):
        self.vehicle_listbox.delete(0, tk.END)
        for i, v in enumerate(self.vehicles):
            self.vehicle_listbox.insert(tk.END, self.vehicle_label(v, i))
        self.update_preview()

    def selected_index(self, listbox: tk.Listbox) -> Optional[int]:
        sel = listbox.curselection()
        return sel[0] if sel else None

    def add_vehicle(self):
        dlg = VehicleDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self.vehicles.append(dlg.result)
            self.refresh_vehicle_list()

    def edit_vehicle(self):
        idx = self.selected_index(self.vehicle_listbox)
        if idx is None:
            messagebox.showinfo("No selection", "Select a vehicle to edit.")
            return
        dlg = VehicleDialog(self, self.vehicles[idx])
        self.wait_window(dlg)
        if dlg.result:
            self.vehicles[idx] = dlg.result
            self.refresh_vehicle_list()

    def delete_vehicle(self):
        idx = self.selected_index(self.vehicle_listbox)
        if idx is None:
            messagebox.showinfo("No selection", "Select a vehicle to delete.")
            return
        del self.vehicles[idx]
        self.refresh_vehicle_list()

    def person_label(self, p: InvolvedPerson, idx: int) -> str:
        name = f"{p.first_name} {p.last_name}".strip() or "Unnamed"
        return f"{idx + 1}. [{p.involvement_type}] {name}"

    def vehicle_options_for_people(self) -> List[str]:
        return [self.vehicle_label(v, i) for i, v in enumerate(self.vehicles)]

    def refresh_people_list(self):
        self.people_listbox.delete(0, tk.END)
        for i, p in enumerate(self.involved_people):
            self.people_listbox.insert(tk.END, self.person_label(p, i))
        self.update_preview()

    def add_person(self):
        dlg = PersonDialog(self, vehicle_options=self.vehicle_options_for_people())
        self.wait_window(dlg)
        if dlg.result:
            self.involved_people.append(dlg.result)
            self.refresh_people_list()

    def edit_person(self):
        idx = self.selected_index(self.people_listbox)
        if idx is None:
            messagebox.showinfo("No selection", "Select a person to edit.")
            return
        dlg = PersonDialog(self, self.involved_people[idx], self.vehicle_options_for_people())
        self.wait_window(dlg)
        if dlg.result:
            self.involved_people[idx] = dlg.result
            self.refresh_people_list()

    def delete_person(self):
        idx = self.selected_index(self.people_listbox)
        if idx is None:
            messagebox.showinfo("No selection", "Select a person to delete.")
            return
        del self.involved_people[idx]
        self.refresh_people_list()

    def build_report_text(self) -> str:
        def get_value(key: str, default: str = "[Not entered]") -> str:
            w = self.fields.get(key)
            val = w.get() if w and hasattr(w, "get") else ""
            val = str(val).strip()
            return val if val else default

        diagram_summary = "Not created"
        if self.scale_editor and self.scale_editor.winfo_exists() and self.scale_editor.objects:
            n = len(self.scale_editor.objects)
            diagram_summary = f"{n} object(s) plotted — see exported diagram"

        report = f"""
CRASH RECONSTRUCTION REPORT

Case Number: {get_value("case_number")}
Report Date: {get_value("report_date")}
Crash Date: {get_value("crash_date")}
Crash Time: {get_value("crash_time")}
Incident Type: {get_value("incident_type")}
Crash Location: {get_value("location")}
County: {get_value("county")}
City: {get_value("city")}
Agency: {get_value("agency")}
Investigating Officer: {get_value("officer")}
Officer Rank: {get_value("officer_rank")}
Badge / Serial Number: {get_value("badge")}

Crash Details:
Collision Type: {get_value("collision_type")}
Roadway / Route: {get_value("roadway")}
Weather: {get_value("weather")}
Lighting Conditions: {get_value("lighting")}
Surface Condition: {get_value("surface")}
Speed Limit: {get_value("speed_limit")}
Traffic Control: {get_value("traffic_control")}
Area of Impact: {get_value("point_of_impact")}
Scene Description: {get_value("scene_desc")}
Scale Diagram: {diagram_summary}

Vehicle Information:
"""

        if self.vehicles:
            for idx, v in enumerate(self.vehicles, start=1):
                owner_addr = ", ".join(part for part in [v.owner_street, v.owner_city, v.owner_state, v.owner_zip] if part)
                report += f"""
                Vehicle {idx}
                - Year / Make / Model: {v.year} {v.make} {v.model}
                - Color: {v.color}
                - Plate #: {v.plate}
                - VIN: {v.vin}
                - Impact Area: {v.impact_area}
                - Owner: {v.owner_name}
                - Owner Address: {owner_addr or 'N/A'}
                - Insurance Company: {v.insurance_company}
                - Policy Number: {v.policy_number}
                - Phone: {v.phone_number}
                - Notes: {v.notes or 'None'}
                """
                if v.occupants:
                    report += "Occupants:\n"
                    for i, occ in enumerate(v.occupants, start=1):
                        occ_addr = ", ".join(part for part in [occ.street, occ.city, occ.state, occ.zip_code] if part)
                        report += (
                            f"  {i}. {occ.first_name} {occ.last_name}\n"
                            f"     Role: {occ.relation_to_vehicle}\n"
                            f"     Seat Position: {occ.seat_location}\n"
                            f"     DOB: {occ.dob}\n"
                            f"     Phone: {occ.phone}\n"
                            f"     Address: {occ_addr or 'N/A'}\n"
                            f"     License: {occ.license_number or 'N/A'} ({occ.license_state or 'N/A'})\n"
                            f"     Injury Severity: {occ.injury_severity or 'N/A'}\n"
                            f"     Injury Description: {occ.injury_description or 'N/A'}\n"
                            f"     Died: {'Yes' if occ.died else 'No'}\n"
                            f"     Death Location/Details: {occ.death_location or 'N/A'}\n"
                            f"     Notes: {occ.notes or 'N/A'}\n"
                        )
                report += "\n"
        else:
            report += "No vehicles added.\n\n"

        report += "Involved Person:\n"
        if self.involved_people:
            for idx, p in enumerate(self.involved_people, start=1):
                p_addr = ", ".join(part for part in [p.street, p.city, p.state, p.zip_code] if part)
                report += (
                    f"{idx}. [{p.involvement_type}] {p.first_name} {p.last_name}\n"
                    f"   Phone: {p.phone or 'N/A'}\n"
                    f"   Address: {p_addr or 'N/A'}\n"
                    f"   Related Vehicle: {p.related_vehicle or 'None'}\n"
                    f"   Injury Severity: {p.injury_severity or 'N/A'}\n"
                    f"   Injury Description: {p.injury_description or 'N/A'}\n"
                    f"   Transported By/Location: {p.transported_by_location or 'N/A'}\n"
                    f"   Died: {'Yes' if p.died else 'No'}\n"
                    f"   Death Location/Details: {p.death_location or 'N/A'}\n"
                    f"   Statement: {p.statement or 'N/A'}\n"
                    f"   Notes: {p.notes or 'N/A'}\n\n"
                )
        else:
            report += "No involved persons added.\n\n"

        narrative = self.fields["narrative"].get("0.0", "end").strip() or "Narrative not entered."
        report += f"""Narrative / Reconstruction Findings:
{narrative}
"""
        return report.strip() + "\n"

    def update_preview(self):
        report = self.build_report_text()
        self.preview_text.configure(state="normal")
        self.preview_text.delete("0.0", "end")
        self.preview_text.insert("0.0", report)
        self.preview_text.configure(state="disabled")

    def export_txt(self):
        report = self.build_report_text()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt")],
            title="Save report as .txt"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report)
            messagebox.showinfo("Saved", f"Report saved to:\n{file_path}")

    def export_docx(self):
        report = self.build_report_text()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word document", "*.docx")],
            title="Save report as .docx"
        )
        if file_path:
            doc = Document()
            for line in report.splitlines():
                doc.add_paragraph(line)
            doc.save(file_path)
            messagebox.showinfo("Saved", f"Report saved to:\n{file_path}")