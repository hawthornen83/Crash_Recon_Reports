from dataclasses import dataclass, field
from typing import List


@dataclass
class Occupant:
    first_name: str = ""
    last_name: str = ""
    dob: str = ""
    phone: str = ""
    street: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    license_number: str = ""
    license_state: str = ""
    relation_to_vehicle: str = ""
    seat_location: str = "Unknown"
    injury_severity: str = ""
    injury_description: str = ""
    died: bool = False
    death_location: str = ""
    notes: str = ""


@dataclass
class Vehicle:
    year: str = ""
    make: str = ""
    model: str = ""
    color: str = ""
    plate: str = ""
    vin: str = ""
    owner_name: str = ""
    owner_street: str = ""
    owner_city: str = ""
    owner_state: str = ""
    owner_zip: str = ""
    insurance_company: str = ""
    policy_number: str = ""
    phone_number: str = ""
    notes: str = ""
    impact_area: str = "Not specified"
    occupants: List[Occupant] = field(default_factory=list)


@dataclass
class InvolvedPerson:
    involvement_type: str = "Driver"
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    street: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    injury_severity: str = ""
    injury_description: str = ""
    transported_by_location: str = ""   # NEW
    died: bool = False
    death_location: str = ""
    statement: str = ""
    related_vehicle: str = "None"
    notes: str = ""