import tkinter as tk
from copy import deepcopy
from typing import List, Optional
from impact_diagram import ImpactDiagram

import customtkinter as ctk
from tkinter import messagebox

from constants import RELATION_TYPES, SEAT_POSITIONS, INVOLVEMENT_TYPES
from models import InvolvedPerson, Occupant, Vehicle


class OccupantDialog(ctk.CTkToplevel):
    def __init__(self, parent, occupant: Optional[Occupant] = None):
        super().__init__(parent)
        self.title("Occupant")
        self.geometry("640x800")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.result: Optional[Occupant] = None
        data = deepcopy(occupant) if occupant else Occupant()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1)

        self.entries = {}
        row = 0

        text_fields = [
            ("First Name", "first_name"),
            ("Last Name", "last_name"),
            ("DOB", "dob"),
            ("Phone Number", "phone"),
            ("Street Address", "street"),
            ("City", "city"),
            ("State", "state"),
            ("ZIP", "zip_code"),
            ("Driver License #", "license_number"),
            ("License State", "license_state"),
            ("Injury Severity", "injury_severity"),
            ("Injury Description", "injury_description"),
            ("Death Location / Details", "death_location"),
            ("Notes", "notes"),
        ]

        for label_text, key in text_fields:
            ctk.CTkLabel(self.scroll, text=label_text, anchor="w").grid(
                row=row, column=0, padx=12, pady=(8, 4), sticky="ew"
            )
            entry = ctk.CTkEntry(self.scroll, height=32)
            entry.grid(row=row, column=1, padx=12, pady=(8, 4), sticky="ew")
            entry.insert(0, getattr(data, key))
            self.entries[key] = entry
            row += 1

        ctk.CTkLabel(self.scroll, text="Role / Relation", anchor="w").grid(
            row=row, column=0, padx=12, pady=(8, 4), sticky="ew"
        )
        self.relation_var = tk.StringVar(
            value=data.relation_to_vehicle if data.relation_to_vehicle else "Passenger"
        )
        self.relation_menu = ctk.CTkOptionMenu(self.scroll, values=RELATION_TYPES, variable=self.relation_var)
        self.relation_menu.grid(row=row, column=1, padx=12, pady=(8, 4), sticky="ew")
        row += 1

        ctk.CTkLabel(self.scroll, text="Seat Position", anchor="w").grid(
            row=row, column=0, padx=12, pady=(8, 4), sticky="ew"
        )
        seat_default = data.seat_location if data.seat_location in SEAT_POSITIONS else "Unknown"
        self.seat_var = tk.StringVar(value=seat_default)
        self.seat_menu = ctk.CTkOptionMenu(self.scroll, values=SEAT_POSITIONS, variable=self.seat_var)
        self.seat_menu.grid(row=row, column=1, padx=12, pady=(8, 4), sticky="ew")
        row += 1

        ctk.CTkLabel(self.scroll, text="Died?", anchor="w").grid(
            row=row, column=0, padx=12, pady=(8, 4), sticky="ew"
        )
        self.died_var = tk.StringVar(value="Yes" if data.died else "No")
        self.died_menu = ctk.CTkOptionMenu(self.scroll, values=["No", "Yes"], variable=self.died_var)
        self.died_menu.grid(row=row, column=1, padx=12, pady=(8, 4), sticky="ew")
        row += 1

        btn_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=16)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=8, sticky="ew")
        ctk.CTkButton(btn_frame, text="Save Occupant", command=self.save_occupant).grid(row=0, column=1, padx=8, sticky="ew")

    def save_occupant(self):
        occ = Occupant(
            first_name=self.entries["first_name"].get().strip(),
            last_name=self.entries["last_name"].get().strip(),
            dob=self.entries["dob"].get().strip(),
            phone=self.entries["phone"].get().strip(),
            street=self.entries["street"].get().strip(),
            city=self.entries["city"].get().strip(),
            state=self.entries["state"].get().strip(),
            zip_code=self.entries["zip_code"].get().strip(),
            license_number=self.entries["license_number"].get().strip(),
            license_state=self.entries["license_state"].get().strip(),
            relation_to_vehicle=self.relation_var.get().strip(),
            seat_location=self.seat_var.get().strip(),
            injury_severity=self.entries["injury_severity"].get().strip(),
            injury_description=self.entries["injury_description"].get().strip(),
            died=self.died_var.get() == "Yes",
            death_location=self.entries["death_location"].get().strip(),
            notes=self.entries["notes"].get().strip(),
        )

        if not any([occ.first_name, occ.last_name, occ.relation_to_vehicle, occ.seat_location]):
            messagebox.showwarning("Missing information", "Enter at least name or role/seat info.")
            return

        self.result = occ
        self.destroy()


class VehicleDialog(ctk.CTkToplevel):
    def __init__(self, parent, vehicle: Optional[Vehicle] = None):
        super().__init__(parent)
        self.title("Vehicle")
        self.geometry("700x930")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.result: Optional[Vehicle] = None
        self.vehicle = deepcopy(vehicle) if vehicle else Vehicle()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1)

        self.entries = {}

        fields = [
            ("Year", "year"),
            ("Make", "make"),
            ("Model", "model"),
            ("Color", "color"),
            ("Plate #", "plate"),
            ("VIN", "vin"),
            ("Owner Name", "owner_name"),
            ("Owner Street", "owner_street"),
            ("City", "owner_city"),
            ("State", "owner_state"),
            ("ZIP", "owner_zip"),
            ("Insurance Company", "insurance_company"),
            ("Policy Number", "policy_number"),
            ("Phone Number", "phone_number"),
            ("Notes", "notes"),
        ]

        row = 0
        for label_text, key in fields:
            ctk.CTkLabel(self.scroll, text=label_text, anchor="w").grid(
                row=row, column=0, padx=12, pady=(8, 4), sticky="ew"
            )
            entry = ctk.CTkEntry(self.scroll, height=32)
            entry.grid(row=row, column=1, padx=12, pady=(8, 4), sticky="ew")
            entry.insert(0, getattr(self.vehicle, key))
            self.entries[key] = entry
            row += 1

        ctk.CTkLabel(
            self.scroll,
            text="Impact Area",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w"
        ).grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 6))
        row += 1

        self.impact_diagram = ImpactDiagram(self.scroll)
        self.impact_diagram.grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))
        self.impact_diagram.set(self.vehicle.impact_area)
        row += 1

        ctk.CTkLabel(self.scroll, text="Occupants", font=ctk.CTkFont(size=18, weight="bold"), anchor="w").grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 6)
        )
        row += 1

        self.occupant_listbox = tk.Listbox(self.scroll, height=8, exportselection=False)
        self.occupant_listbox.grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 8))
        row += 1

        btn_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        btn_row.grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 8))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)
        btn_row.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(btn_row, text="Add Occupant", command=self.add_occupant).grid(row=0, column=0, padx=8, sticky="ew")
        ctk.CTkButton(btn_row, text="Edit Occupant", command=self.edit_occupant).grid(row=0, column=1, padx=8, sticky="ew")
        ctk.CTkButton(btn_row, text="Delete Occupant", command=self.delete_occupant).grid(row=0, column=2, padx=8, sticky="ew")
        row += 1

        action_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        action_row.grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=12)
        action_row.grid_columnconfigure(0, weight=1)
        action_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(action_row, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=8, sticky="ew")
        ctk.CTkButton(action_row, text="Save Vehicle", command=self.save_vehicle).grid(row=0, column=1, padx=8, sticky="ew")

        self.refresh_occupants()

    def refresh_occupants(self):
        self.occupant_listbox.delete(0, tk.END)
        for i, occ in enumerate(self.vehicle.occupants, start=1):
            self.occupant_listbox.insert(
                tk.END,
                f"{i}. {occ.first_name} {occ.last_name} | {occ.relation_to_vehicle} | {occ.seat_location}"
            )

    def selected_occupant_index(self) -> Optional[int]:
        sel = self.occupant_listbox.curselection()
        return sel[0] if sel else None

    def add_occupant(self):
        dlg = OccupantDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self.vehicle.occupants.append(dlg.result)
            self.refresh_occupants()

    def edit_occupant(self):
        idx = self.selected_occupant_index()
        if idx is None:
            messagebox.showinfo("No selection", "Select an occupant to edit.")
            return
        dlg = OccupantDialog(self, self.vehicle.occupants[idx])
        self.wait_window(dlg)
        if dlg.result:
            self.vehicle.occupants[idx] = dlg.result
            self.refresh_occupants()

    def delete_occupant(self):
        idx = self.selected_occupant_index()
        if idx is None:
            messagebox.showinfo("No selection", "Select an occupant to delete.")
            return
        del self.vehicle.occupants[idx]
        self.refresh_occupants()

    def save_vehicle(self):
        updated = Vehicle(
            year=self.entries["year"].get().strip(),
            make=self.entries["make"].get().strip(),
            model=self.entries["model"].get().strip(),
            color=self.entries["color"].get().strip(),
            plate=self.entries["plate"].get().strip(),
            vin=self.entries["vin"].get().strip(),
            owner_name=self.entries["owner_name"].get().strip(),
            owner_street=self.entries["owner_street"].get().strip(),
            owner_city=self.entries["owner_city"].get().strip(),
            owner_state=self.entries["owner_state"].get().strip(),
            owner_zip=self.entries["owner_zip"].get().strip(),
            insurance_company=self.entries["insurance_company"].get().strip(),
            policy_number=self.entries["policy_number"].get().strip(),
            phone_number=self.entries["phone_number"].get().strip(),
            notes=self.entries["notes"].get().strip(),
            impact_area=self.impact_diagram.get(),
            occupants=deepcopy(self.vehicle.occupants),
        )

        if not any([updated.year, updated.make, updated.model, updated.plate, updated.vin]):
            messagebox.showwarning("Missing information", "Enter at least year/make/model or plate/VIN.")
            return

        self.result = updated
        self.destroy()


class PersonDialog(ctk.CTkToplevel):
    def __init__(self, parent, person: Optional[InvolvedPerson] = None, vehicle_options: Optional[List[str]] = None):
        super().__init__(parent)
        self.title("Involved Person")
        self.geometry("640x800")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.result: Optional[InvolvedPerson] = None
        data = deepcopy(person) if person else InvolvedPerson()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1)

        self.entries = {}
        row = 0

        ctk.CTkLabel(self.scroll, text="Involvement Type", anchor="w").grid(row=row, column=0, padx=12, pady=(10, 4), sticky="ew")
        self.type_var = tk.StringVar(value=data.involvement_type or "Driver")
        ctk.CTkOptionMenu(self.scroll, values=INVOLVEMENT_TYPES, variable=self.type_var).grid(
            row=row, column=1, padx=12, pady=(10, 4), sticky="ew"
        )
        row += 1

        fields = [
            ("First Name", "first_name"),
            ("Last Name", "last_name"),
            ("Phone Number", "phone"),
            ("Street Address", "street"),
            ("City", "city"),
            ("State", "state"),
            ("ZIP", "zip_code"),
            ("Injury Severity", "injury_severity"),
            ("Injury Description", "injury_description"),
            ("Transported By / Location", "transported_by_location"),
            ("Death Location / Details", "death_location"),
            ("Statement", "statement"),
            ("Notes", "notes"),
        ]

        for label_text, key in fields:
            ctk.CTkLabel(self.scroll, text=label_text, anchor="w").grid(row=row, column=0, padx=12, pady=(8, 4), sticky="ew")
            entry = ctk.CTkEntry(self.scroll, height=32)
            entry.grid(row=row, column=1, padx=12, pady=(8, 4), sticky="ew")
            entry.insert(0, getattr(data, key))
            self.entries[key] = entry
            row += 1

        ctk.CTkLabel(self.scroll, text="Died?", anchor="w").grid(row=row, column=0, padx=12, pady=(8, 4), sticky="ew")
        self.died_var = tk.StringVar(value="Yes" if data.died else "No")
        ctk.CTkOptionMenu(self.scroll, values=["No", "Yes"], variable=self.died_var).grid(
            row=row, column=1, padx=12, pady=(8, 4), sticky="ew"
        )
        row += 1

        ctk.CTkLabel(self.scroll, text="Related Vehicle", anchor="w").grid(row=row, column=0, padx=12, pady=(8, 4), sticky="ew")
        options = ["None"] + (vehicle_options or [])
        if data.related_vehicle and data.related_vehicle not in options:
            options.append(data.related_vehicle)
        self.vehicle_var = tk.StringVar(value=data.related_vehicle or "None")
        ctk.CTkOptionMenu(self.scroll, values=options, variable=self.vehicle_var).grid(
            row=row, column=1, padx=12, pady=(8, 4), sticky="ew"
        )
        row += 1

        btn_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=16)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=8, sticky="ew")
        ctk.CTkButton(btn_frame, text="Save Person", command=self.save_person).grid(row=0, column=1, padx=8, sticky="ew")

    def save_person(self):
        person = InvolvedPerson(
            involvement_type=self.type_var.get().strip() or "Driver",
            first_name=self.entries["first_name"].get().strip(),
            last_name=self.entries["last_name"].get().strip(),
            phone=self.entries["phone"].get().strip(),
            street=self.entries["street"].get().strip(),
            city=self.entries["city"].get().strip(),
            state=self.entries["state"].get().strip(),
            zip_code=self.entries["zip_code"].get().strip(),
            injury_severity=self.entries["injury_severity"].get().strip(),
            injury_description=self.entries["injury_description"].get().strip(),
            transported_by_location=self.entries["transported_by_location"].get().strip(),
            died=self.died_var.get() == "Yes",
            death_location=self.entries["death_location"].get().strip(),
            statement=self.entries["statement"].get().strip(),
            related_vehicle=self.vehicle_var.get().strip() or "None",
            notes=self.entries["notes"].get().strip(),
        )

        if not any([person.first_name, person.last_name, person.phone, person.statement]):
            messagebox.showwarning("Missing information", "Enter at least a name, phone, or statement.")
            return

        self.result = person
        self.destroy()