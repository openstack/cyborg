import hashlib

mcodigo = "Hola World"
codificado = hashlib.sha256(mcodigo.encode()).hexdigest()

print(f"Saludo con SHA256: {codificado}")
