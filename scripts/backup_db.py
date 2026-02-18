import argparse
import os
import shutil
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Backup SQLite attendance database")
    parser.add_argument("--db", default=os.path.join("instance", "attendance.db"), help="Path to source DB")
    parser.add_argument("--out", default="backups", help="Backup output directory")
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
