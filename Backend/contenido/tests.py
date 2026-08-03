"""
Pruebas de la validación de archivos  (P1.9).

La pregunta que responden: **¿se puede colar un ejecutable renombrándolo?**
Porque eso es lo que hace cualquiera que quiera repartir un virus por la
biblioteca de la empresa, y una validación por extensión no lo detiene.
"""

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from comun.archivos import validar_archivo

PDF = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 40
ZIP = b"PK\x03\x04" + b"\x00" * 40
EXE = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 40
ELF = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 40
SH = b"#!/bin/bash\nrm -rf /\n"


def subida(nombre, contenido):
    return SimpleUploadedFile(nombre, contenido)


class ArchivosLegitimos(SimpleTestCase):
    def test_pdf_de_verdad(self):
        validar_archivo(subida("manual.pdf", PDF))

    def test_png_de_verdad(self):
        validar_archivo(subida("organigrama.png", PNG))

    def test_docx_de_verdad(self):
        validar_archivo(subida("procedimiento.docx", ZIP))

    def test_texto_plano_sin_firma(self):
        validar_archivo(subida("notas.txt", b"Merma: producto perdido en el turno."))

    def test_csv(self):
        validar_archivo(subida("datos.csv", b"nombre,area\nmerma,produccion\n"))


class ExtensionesProhibidas(SimpleTestCase):
    def test_exe(self):
        with self.assertRaises(ValidationError):
            validar_archivo(subida("instalador.exe", EXE))

    def test_bat(self):
        with self.assertRaises(ValidationError):
            validar_archivo(subida("script.bat", b"@echo off\ndel /f /q C:\\*"))

    def test_ps1(self):
        with self.assertRaises(ValidationError):
            validar_archivo(subida("cosa.ps1", b"Remove-Item -Recurse"))


class EjecutablesDisfrazados(SimpleTestCase):
    """
    El caso que de verdad importa. La extensión dice una cosa y los bytes
    dicen otra: una validación por extensión los deja pasar a todos.
    """

    def test_exe_renombrado_a_pdf(self):
        with self.assertRaises(ValidationError) as e:
            validar_archivo(subida("manual_de_induccion.pdf", EXE))
        self.assertIn("ejecutable de Windows", str(e.exception))

    def test_binario_de_linux_renombrado_a_docx(self):
        with self.assertRaises(ValidationError) as e:
            validar_archivo(subida("procedimiento.docx", ELF))
        self.assertIn("ejecutable de Linux", str(e.exception))

    def test_script_de_shell_renombrado_a_txt(self):
        with self.assertRaises(ValidationError) as e:
            validar_archivo(subida("notas.txt", SH))
        self.assertIn("script", str(e.exception))

    def test_zip_renombrado_a_pdf_no_pasa(self):
        """No es peligroso, pero miente sobre lo que es."""
        with self.assertRaises(ValidationError):
            validar_archivo(subida("informe.pdf", ZIP))


class Tamano(SimpleTestCase):
    def test_archivo_vacio(self):
        with self.assertRaises(ValidationError):
            validar_archivo(subida("vacio.pdf", b""))

    def test_demasiado_grande(self):
        grande = SimpleUploadedFile("enorme.pdf", PDF)
        grande.size = 60 * 1024 * 1024
        with self.assertRaises(ValidationError) as e:
            validar_archivo(grande)
        self.assertIn("50 MB", str(e.exception))
