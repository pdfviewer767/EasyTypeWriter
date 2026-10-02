import binascii
import getpass
import hashlib
import secrets


def encrypt_password(password, salt_hex):
    salt_bytes = binascii.unhexlify(salt_hex)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt_bytes, 100000, dklen=32
    )
    return binascii.hexlify(key).decode("ascii")


def generate_password_hash(password):
    salt = secrets.token_hex(16)
    return encrypt_password(password, salt), salt


def main():
    password = getpass.getpass("Admin password to hash: ")
    if not password:
        raise SystemExit("Password cannot be empty")

    password_hash, salt = generate_password_hash(password)
    print(f"salt: {salt}")
    print(f"hashed_password: {password_hash}")


if __name__ == "__main__":
    main()