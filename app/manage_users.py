import getpass
import sys

from app import users


def main() -> int:
    username = input("Username: ")
    role = input("Role (analyst/reviewer): ").strip().lower()
    password = getpass.getpass("Password: ")
    repeated = getpass.getpass("Repeat password: ")

    if password != repeated:
        print("Passwords do not match. No user was created.")
        return 1

    try:
        created = users.create_user(username, password, role)
    except ValueError as error:
        print("Could not create user:", error)
        return 1

    print(f"Created user '{created['username']}' with role '{created['role']}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
