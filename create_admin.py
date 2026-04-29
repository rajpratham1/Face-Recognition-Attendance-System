import argparse
import getpass
import sys

from werkzeug.security import generate_password_hash

from app import app
from models import User, db


def prompt_if_missing(value, label, secret=False):
    if value:
        return value
    if secret:
        return getpass.getpass(f"{label}: ").strip()
    return input(f"{label}: ").strip()


def validate_password(password):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not any(ch.isdigit() for ch in password):
        raise ValueError("Password must contain at least one number.")
    if not any(ch.isupper() for ch in password):
        raise ValueError("Password must contain at least one uppercase letter.")


def build_parser():
    parser = argparse.ArgumentParser(description="Create a privileged attendance-system account.")
    parser.add_argument("--role", choices=["teacher", "admin"], default="admin")
    parser.add_argument("--name")
    parser.add_argument("--email")
    parser.add_argument("--department")
    parser.add_argument("--password")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    name = prompt_if_missing(args.name, "Full name")
    email = prompt_if_missing(args.email, "Email").lower()
    department = prompt_if_missing(args.department, "Department")
    password = prompt_if_missing(args.password, "Password", secret=True)

    if not name or not email or "@" not in email or "." not in email:
        raise ValueError("A valid name and email are required.")
    if not department:
        raise ValueError("Department is required.")
    validate_password(password)

    with app.app_context():
        existing = User.query.filter_by(email=email).first()
        if existing:
            raise ValueError(f"An account with {email} already exists.")

        user = User(
            name=name,
            email=email,
            department=department,
            role=args.role,
            password_hash=generate_password_hash(password, method="scrypt"),
        )
        db.session.add(user)
        db.session.commit()

    print(f"Created {args.role} account for {email}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
