# importación de la librería hashpara el cifrado
import hashlib;

#variable que contiene el mensaje hello world
mensaje= "hello world"

#creación del objeto hash 256
obj_ash = hashlib.sha256()

#se agrega el mensaje al objeto hash
obj_ash.update(mensaje.encode('utf-8'))

#variable con la versión encriptada del mensaje
mensaje_encriptado= obj_ash.hexdigest()

#impresión por consola del mensaje original y el mensaje encriptado

print(mensaje)

print(mensaje_encriptado)

