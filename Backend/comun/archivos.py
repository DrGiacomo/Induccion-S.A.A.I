"""
Validación de archivos subidos  (P1.9).

**El problema con validar por extensión:** renombrar `virus.exe` a
`manual.pdf` la burla entera. La extensión es un dato que escribe quien sube
el archivo, y confiar en un dato que controla el atacante nunca es una
validación — es una sugerencia.

Lo que sí funciona es mirar los primeros bytes. Casi todo formato empieza por
una firma fija (`%PDF-`, `PK` para los ZIP y los Office modernos, `\\x89PNG`).
Se comprueba que la firma real **coincida con lo que la extensión promete**.

No se usa `python-magic`: necesita `libmagic`, que en Windows es una odisea
de instalar y complicaría el despliegue en cada empresa. Para lo que hace
falta aquí, treinta líneas propias bastan.
"""

import os

from django.core.exceptions import ValidationError

# Firma → familia de formatos que la comparten.
FIRMAS = {
    b"%PDF-": "pdf",
    b"\x89PNG\r\n\x1a\n": "imagen",
    b"\xff\xd8\xff": "imagen",              # JPEG
    b"GIF87a": "imagen",
    b"GIF89a": "imagen",
    b"PK\x03\x04": "zip",                   # docx, xlsx, pptx, odt y zip a secas
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": "ole",   # doc, xls, ppt antiguos
    b"RIFF": "riff",                        # webp, wav, avi
    b"\x1a\x45\xdf\xa3": "video",           # mkv, webm
    b"ID3": "audio",
    b"OggS": "audio",
    b"%!PS": "postscript",
}

# Qué firma se espera según la extensión declarada.
ESPERADO = {
    "pdf": {"pdf"},
    "png": {"imagen"}, "jpg": {"imagen"}, "jpeg": {"imagen"},
    "gif": {"imagen"}, "webp": {"riff"}, "bmp": {"texto_o_binario"},
    "docx": {"zip"}, "xlsx": {"zip"}, "pptx": {"zip"},
    "odt": {"zip"}, "ods": {"zip"}, "zip": {"zip"},
    "doc": {"ole"}, "xls": {"ole"}, "ppt": {"ole"},
    "mp3": {"audio", "riff"}, "ogg": {"audio"}, "wav": {"riff"},
    "mp4": {"riff", "video", "texto_o_binario"},
    "mkv": {"video"}, "webm": {"video"},
    # Los de texto plano no tienen firma. Se aceptan tal cual.
    "txt": None, "csv": None, "md": None, "log": None, "json": None,
}

# Nunca, pase lo que pase. Una biblioteca de empresa que reparte ejecutables
# deja de ser una biblioteca y pasa a ser un vector de contagio.
EXTENSIONES_PROHIBIDAS = {
    "exe", "bat", "cmd", "com", "cpl", "scr", "pif", "msi", "msp",
    "jar", "js", "jse", "vbs", "vbe", "wsf", "wsh", "ps1", "psm1",
    "sh", "bash", "reg", "dll", "sys", "hta", "lnk", "gadget", "app",
    "deb", "rpm", "apk", "iso", "img", "vbscript", "php", "asp", "aspx",
    "jsp", "cgi", "pl", "py", "rb",
}

# Firmas que jamás deben aparecer, mienta lo que mienta la extensión.
FIRMAS_EJECUTABLES = {
    b"MZ": "ejecutable de Windows",
    b"\x7fELF": "ejecutable de Linux",
    b"\xca\xfe\xba\xbe": "clase de Java o binario de macOS",
    b"\xfe\xed\xfa": "binario de macOS",
    b"#!": "script con intérprete",
}

TAMANO_MAXIMO = 50 * 1024 * 1024   # 50 MB


def extension_de(nombre: str) -> str:
    return os.path.splitext(nombre or "")[1].lower().lstrip(".")


def _leer_cabecera(archivo, n=16) -> bytes:
    posicion = archivo.tell() if hasattr(archivo, "tell") else 0
    archivo.seek(0)
    cabecera = archivo.read(n)
    archivo.seek(posicion)
    return cabecera or b""


def familia_real(cabecera: bytes) -> str:
    for firma, familia in FIRMAS.items():
        if cabecera.startswith(firma):
            return familia
    return "texto_o_binario"


def validar_archivo(archivo):
    """
    Las cuatro comprobaciones, en orden de lo barato a lo caro.

    Se llama desde el campo del modelo, así que vale tanto para la API como
    para el panel de administración. Una validación que solo vive en la vista
    se salta entrando por el otro lado.
    """
    nombre = getattr(archivo, "name", "")
    extension = extension_de(nombre)

    # 1 · Extensión prohibida
    if extension in EXTENSIONES_PROHIBIDAS:
        raise ValidationError(
            f"No se aceptan archivos «.{extension}»: podrían ejecutar código "
            f"en el equipo de quien los descargue."
        )

    # 2 · Tamaño
    tamano = getattr(archivo, "size", 0) or 0
    if tamano > TAMANO_MAXIMO:
        raise ValidationError(
            f"El archivo pesa {tamano / 1048576:.1f} MB y el máximo son "
            f"{TAMANO_MAXIMO // 1048576} MB. Si es un video, enlázalo en vez de subirlo."
        )
    if tamano == 0:
        raise ValidationError("El archivo está vacío.")

    cabecera = _leer_cabecera(archivo)

    # 3 · Firma de ejecutable, diga lo que diga la extensión.
    #     Esto es lo que caza a `virus.exe` renombrado a `manual.pdf`.
    for firma, que_es in FIRMAS_EJECUTABLES.items():
        if cabecera.startswith(firma):
            raise ValidationError(
                f"El archivo dice ser «.{extension}» pero por dentro es un {que_es}. "
                f"No se acepta."
            )

    # 4 · Que el contenido case con lo que promete la extensión
    esperado = ESPERADO.get(extension, "desconocido")
    if esperado is None:            # texto plano, sin firma
        return
    if esperado == "desconocido":   # formato que no conocemos: pasan 1-3 y basta
        return
    real = familia_real(cabecera)
    if real not in esperado:
        raise ValidationError(
            f"El contenido del archivo no corresponde con la extensión «.{extension}». "
            f"Puede estar dañado o renombrado."
        )
