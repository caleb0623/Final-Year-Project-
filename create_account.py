import argparse
from getpass import getpass

from postgres_store import ACCOUNT_FIELDS, init_store, save_record


def main():
    parser = argparse.ArgumentParser(description="Create a PostgreSQL-backed application account.")
    parser.add_argument("--role", required=True, choices=sorted(ACCOUNT_FIELDS))
    parser.add_argument("--id", required=True, dest="account_id")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", default="")
    parser.add_argument("--phone", default="")
    parser.add_argument("--admin-id", default="")
    args = parser.parse_args()

    password = getpass("New password: ")
    if len(password) < 12:
        parser.error("Use a password with at least 12 characters.")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        parser.error("The passwords do not match.")

    init_store()
    if args.role == "admin":
        resource, id_field, password_field = "admin", "adminID", "adminPassword"
        payload = {"adminName": args.name, "adminEmail": args.email, "adminPhoneNo": args.phone}
    elif args.role == "security":
        resource, id_field, password_field = "security", "guardID", "guardPassword"
        payload = {"guardName": args.name, "guardPhoneNo": args.phone, "adminID": args.admin_id}
    else:
        resource, id_field, password_field = "lecturer", "lecturerID", "lecturerPw"
        payload = {"lecturerName": args.name, "lecturerEmail": args.email, "lecturerPhoneNo": args.phone}

    payload[id_field] = args.account_id.strip().upper()
    payload[password_field] = password
    save_record(resource, payload)
    print(f"Created {args.role} account {payload[id_field]}.")


if __name__ == "__main__":
    main()
