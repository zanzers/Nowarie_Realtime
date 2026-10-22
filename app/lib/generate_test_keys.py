from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Generate an RSA private key.
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Export the private key.
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

# Export the public key.
public_pem = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

with open("test_private.pem", "wb") as file:
    file.write(private_pem)

with open("test_public.pem", "wb") as file:
    file.write(public_pem)

print("Test RSA key pair generated successfully!")