#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Aquí había esto:
#     import pymysql
#     pymysql.install_as_MySQLdb()
#
# Hacía que PyMySQL suplantara a MySQLdb. Pero `mysqlclient` —el MySQLdb
# real— también estaba instalado, así que por `manage.py` corría un driver
# y por WSGI corría otro. Driver distinto en desarrollo y en producción es
# una fuente clásica de fallos que solo aparecen el día del despliegue.
# Retirado en P0.4; con PostgreSQL no pinta nada.


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'induccion.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
