"""Organizer & Cleanup Utility.

Sorts files in a cluttered directory (e.g. Downloads) into category
subfolders based on file extension. Handles name collisions and
permission errors, and prints an execution summary.

Usage:
    python organizer.py                 # organizes ~/Downloads
    python organizer.py /path/to/folder # organizes the given folder
    python organizer.py /path --dry-run # preview only, nothing is moved
"""

import os
import shutil
import sys
from collections import Counter

CATEGORIES = {
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls",
                  ".xlsx", ".csv", ".ppt", ".pptx", ".md"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
               ".tiff", ".ico", ".heic"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp",
             ".h", ".cs", ".go", ".rs", ".php", ".rb", ".json", ".xml",
             ".sh", ".sql", ".ipynb"},
}
OTHER = "Others"

# Build reverse lookup: extension -> category
EXT_MAP = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}


def get_category(filename):
    ext = os.path.splitext(filename)[1].lower()
    return EXT_MAP.get(ext, OTHER)


def unique_destination(dest_dir, filename):
    """Return a path in dest_dir that doesn't exist, adding _1, _2... if needed."""
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(dest_dir, filename)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(dest_dir, f"{base}_{counter}{ext}")
        counter += 1
    return candidate


def organize(folder, dry_run=False):
    moved = Counter()
    renamed = 0
    errors = []
    skipped = 0

    try:
        entries = list(os.scandir(folder))
    except PermissionError:
        print(f"Permission denied: cannot read '{folder}'.")
        return moved, renamed, errors, skipped

    script_name = os.path.basename(__file__)

    for entry in entries:
        # Skip folders, symlinks and this script itself
        if not entry.is_file(follow_symlinks=False) or entry.name == script_name:
            skipped += 1
            continue

        category = get_category(entry.name)
        dest_dir = os.path.join(folder, category)

        try:
            if not dry_run:
                os.makedirs(dest_dir, exist_ok=True)
            dest = unique_destination(dest_dir, entry.name)
            if os.path.basename(dest) != entry.name:
                renamed += 1
            if dry_run:
                print(f"[dry-run] {entry.name} -> {category}/{os.path.basename(dest)}")
            else:
                shutil.move(entry.path, dest)
                print(f"Moved: {entry.name} -> {category}/{os.path.basename(dest)}")
            moved[category] += 1
        except PermissionError:
            errors.append((entry.name, "Permission denied"))
        except FileExistsError:
            errors.append((entry.name, "File already exists"))
        except OSError as e:
            errors.append((entry.name, str(e)))

    return moved, renamed, errors, skipped


def print_summary(moved, renamed, errors, skipped, dry_run):
    line = "=" * 40
    total = sum(moved.values())
    print(f"\n{line}")
    print(" EXECUTION SUMMARY" + (" (DRY RUN)" if dry_run else ""))
    print(line)
    for category, count in sorted(moved.items()):
        print(f" {category:<12} {count:>5} file(s)")
    print("-" * 40)
    print(f" Total {'to move' if dry_run else 'relocated'}: {total}")
    print(f" Renamed (collisions): {renamed}")
    print(f" Skipped (folders etc.): {skipped}")
    print(f" Errors: {len(errors)}")
    for name, reason in errors:
        print(f"   - {name}: {reason}")
    print(line)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv

    folder = os.path.abspath(args[0]) if args else os.path.join(
        os.path.expanduser("~"), "Downloads")

    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.")
        sys.exit(1)

    print(f"Organizing: {folder}\n")
    results = organize(folder, dry_run)
    print_summary(*results, dry_run)


if __name__ == "__main__":
    main()
