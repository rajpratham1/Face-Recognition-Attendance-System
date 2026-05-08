import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB = BASE_DIR / "instance" / "attendance.db"
DEFAULT_OUT = BASE_DIR / "backups"


def main():
    parser = argparse.ArgumentParser(description="Backup SQLite attendance database")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to source DB")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Backup output directory")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    if not os.path.exists(args.db):
        raise FileNotFoundError(f"Database not found: {args.db}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = os.path.join(args.out, f"attendance_{stamp}.db")
    shutil.copy2(args.db, target)
    print(f"Backup created: {target}")


if __name__ == "__main__":
    main()
