from django.contrib import admin
from .models import roldb, tipo_id_db, perfildb, areadb, userarea, userrol, trabajadordb,repodb,evaluaciondb

# Register your models here.
@admin.register(roldb)
class rolAdmin(admin.ModelAdmin):
    fields=["nombre_rol"]
    list_display=["nombre_rol"]

@admin.register(tipo_id_db)
class tipo_id_dbAdmin(admin.ModelAdmin):
    fields=["tipo_id"]
    list_display=["tipo_id"]

@admin.register(perfildb)
class perfilAdmin(admin.ModelAdmin):
    fields=["user", "telefono","tipo_id_fk"]
    list_display=["user", "tipo_id_fk"]

@admin.register(areadb)
class areaAdmin(admin.ModelAdmin):
    fields=["nombre"]
    list_display=["nombre"]


@admin.register(userarea)
class userareaAdmin(admin.ModelAdmin):
    fields=["id_user", "id_area"]
    list_display=["id_user", "id_area"]

@admin.register(userrol)
class userrolAdmin(admin.ModelAdmin):
    fields=["id_user","id_rol"]
    list_display=["id_user","id_rol"]

@admin.register(trabajadordb)
class trabajadorAdmin(admin.ModelAdmin):
    fields=["id_user","id_userarea","id_userrol"]
    list_display=["id_user","id_userrol"]

@admin.register(repodb)
class repoAdmin(admin.ModelAdmin):
    fields=["archivo","id_area"]
    list_display=["archivo","id_area"]

@admin.register(evaluaciondb)
class evaluacionAdmin(admin.ModelAdmin):
    fields=["id_trabajador","id_repo","nota"]
    list_display=["id_trabajador","nota"]


