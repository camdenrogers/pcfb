"""Fails if a Terraform plan (JSON on stdin) would delete anything that holds data."""
import json
import sys

PROTECTED = {
    "google_compute_disk",
    "google_secret_manager_secret",
    "google_artifact_registry_repository",
    "neon_project",
}

plan = json.load(sys.stdin)
blocked = [
    f"{c['address']}: {'/'.join(c['change']['actions'])}"
    for c in plan.get("resource_changes", [])
    if c["type"] in PROTECTED and "delete" in c["change"]["actions"]
]
if blocked:
    sys.exit("Refusing a plan that deletes protected resources:\n  " + "\n  ".join(blocked))
print("No protected resources are deleted.")
