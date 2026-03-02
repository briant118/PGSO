import os
import sys

import django


def setup_django():
    # Ensure project root is on sys.path (same behavior as manage.py)
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(here))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
    django.setup()


def format_resident_id(seq: int) -> str:
    """
    Generate resident_id based on sequential number.

    - 1..99,999  -> zero-padded 5 digits: 00001..99999
    - 100,000+   -> letter + 4 digits per 100k block:
        100,000..199,999 -> A0001, A0002, ...
        200,000..299,999 -> B0001, B0002, ...
    """
    if seq <= 99999:
        return f"{seq:05d}"

    block_index = (seq - 100000) // 100000  # 0-based: 0=A, 1=B, ...
    letter = chr(ord("A") + block_index)
    within_block = (seq - 100000) % 100000 + 1  # 1..100000
    within_block = min(within_block, 9999)  # keep 4 digits for safety
    return f"{letter}{within_block:04d}"


def main():
    setup_django()
    from operations.models import Resident

    count = 0
    for idx, resident in enumerate(Resident.objects.order_by("id"), start=1):
        resident.resident_id = format_resident_id(idx)
        resident.save(update_fields=["resident_id"])
        count += 1

    print(f"Updated resident_ids for {count} residents.")


if __name__ == "__main__":
    main()

