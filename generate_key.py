import secrets
import string

def generate_secret_key(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(characters) for _ in range(length))
    return secret_key

secret_key = generate_secret_key(64)
print(secret_key)
