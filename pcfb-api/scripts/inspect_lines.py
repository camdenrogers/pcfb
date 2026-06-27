import sys
sys.path.insert(0, ".")
from app.core.cfbd_client import fetch_lines
import json

lines = fetch_lines(2023)
# Look at the first row's lines field
print(type(lines["lines"][0]))
print(json.dumps(lines["lines"][0], indent=2) if isinstance(lines["lines"][0], (list, dict)) else lines["lines"][0])
