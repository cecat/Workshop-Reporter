#!/usr/bin/env python3
"""Create Track-1 bundle from Google Drive data (test_downloads/)."""

import json
import csv
from pathlib import Path

def parse_lightning_talks():
    """Parse lightning talks CSV and extract Track-1 talks."""
    talks = []
    with open("test_downloads/sheet1.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("Track") == "Track-1":
                # Extract talk data
                talk = {
                    "title": row.get("Title of your proposed lightning talk", ""),
                    "authors": [
                        {
                            "name": row.get("Your full name", ""),
                            "affiliation": row.get("Your institution", "")
                        }
                    ],
                    "abstract": row.get("Abstract of your proposed lightning talk (80-100 words)", "")
                }
                talks.append(talk)
    return talks

def parse_attendees():
    """Parse attendees CSV."""
    attendees = []
    with open("test_downloads/sheet2.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            attendees.append({
                "name": f"{row.get('First', '')} {row.get('Last', '')}".strip(),
                "organization": row.get("Organization", "")
            })
    return attendees

def read_notes():
    """Read notes from text file."""
    with open("test_downloads/doc1.txt", "r") as f:
        return f.read().strip()

def create_bundle():
    """Create track bundle from Google Drive data."""
    
    lightning_talks = parse_lightning_talks()
    attendees = parse_attendees()
    notes = read_notes()
    
    # Add lightning talk authors to attendees list
    attendee_names = {a["name"] for a in attendees}
    for talk in lightning_talks:
        for author in talk["authors"]:
            if author["name"] and author["name"] not in attendee_names:
                attendees.append({
                    "name": author["name"],
                    "organization": author["affiliation"]
                })
                attendee_names.add(author["name"])
    
    bundle = {
        "track": {
            "id": "track-1",
            "name": "Track 1 - Data from Google Drive",
            "room": "TBD"
        },
        "sessions": [
            {
                "id": "track-1-session",
                "title": "Track 1 Session",
                "slot": "2025-07-30T09:00",
                "leaders": [],
                "lightning_talks": lightning_talks,
                "attendees": attendees,
                "notes": notes
            }
        ],
        "sources": [
            "test_downloads/sheet1.csv (Lightning talks)",
            "test_downloads/sheet2.csv (Attendees)",
            "test_downloads/doc1.txt (Notes)"
        ]
    }
    
    # Create output directory
    Path("data/bundles").mkdir(parents=True, exist_ok=True)
    
    # Write bundle
    output_path = "data/bundles/track1_google_bundle.json"
    with open(output_path, "w") as f:
        json.dump(bundle, f, indent=2)
    
    print(f"✓ Created bundle: {output_path}")
    print(f"  - {len(lightning_talks)} lightning talks from Track-1")
    print(f"  - {len(attendees)} attendees")
    print(f"  - Notes: {len(notes)} characters")
    
    return output_path

if __name__ == "__main__":
    create_bundle()
