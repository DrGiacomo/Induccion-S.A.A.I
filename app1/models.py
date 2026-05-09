from django.db import models
from django.conf import settings

# Create your models here.
class roldb(models.Model):
    nombre_rol = models.CharField(max_length=20,verbose_name="Nombre completo",null=False, blank=False)
    class Meta:
        db_table="Roles"
        verbose_name="Rol"
        verbose_name_plural="Roles"
        ordering=['nombre_rol']
    
class tipo_id_db(models.Model):
    tipo_id=models.CharField(verbose_name="Tipo_identificacion", null=False, max_length=11)
    class Meta:
        db_table="Tipo de identifiacion"
        verbose_name="Tipo de identificacion"
        
    
class perfildb(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    telefono=models.CharField(max_length=10, null=False, verbose_name="Numero de telefono", blank=False)
    tipo_id_fk=models.OneToOneField(tipo_id_db, on_delete=models.CASCADE, null=False, blank=False)
    class Meta:
        db_table="Perfiles"
        verbose_name="Perfil"
        verbose_name_plural="Perfiles"
#para tener en cuenta cada basicamente la linea 21  y 2 me conecta con el modelo, no la tabla de user de django
#para asi acceder a toda la informacion de ella, con el import la traigo y con la variable la establezco 
#establezco es con Z? o con S, a ver establesco... no sé no me cuadra
class areadb(models.Model):
    nombre=models.CharField(max_length=20, null=False, blank=False, verbose_name="Area")
    class Meta:
        db_table="Areas"
        verbose_name="Area"
        verbose_name_plural="Areas"
        ordering=['nombre']
        #la perra clase meta ponerle nombre para identificar a que proyecto hace referencia
class userarea(models.Model):
    id_user=models.ForeignKey(perfildb, on_delete=models.CASCADE, verbose_name="Id usuario")
    id_area=models.ForeignKey(areadb, on_delete=models.CASCADE, verbose_name="ID, area")
    class Meta:
        db_table="Userarea"

class userrol(models.Model):
    id_user=models.ForeignKey(perfildb, on_delete=models.CASCADE, verbose_name="ID user")        
    id_rol=models.ForeignKey(roldb, on_delete=models.CASCADE, verbose_name="ID roles")        
    class Meta:
        db_table="Userrol"

class trabajadordb(models.Model):
    id_user=models.ForeignKey(perfildb, on_delete=models.CASCADE, verbose_name="ID user")        
    id_userarea=models.ForeignKey(userarea, on_delete=models.CASCADE, verbose_name="ID user area")        
    id_userrol=models.ForeignKey(userrol, on_delete=models.CASCADE, verbose_name="ID user rol") 
    class Meta:
        db_table="Trabajador"
        verbose_name="Trabajador"
        verbose_name_plural="Trabajadores"

class repodb(models.Model):
    arhivo=models.BinaryField() 
    id_area=models.ForeignKey(areadb, on_delete=models.CASCADE, verbose_name="ID, area")
    class Meta:
        verbose_name = "Repositorio"
        verbose_name_plural = "Repositorios"

class evaluaciondb(models.Model):
    id_trabajador=models.OneToOneField(trabajadordb, on_delete=models.CASCADE)
    id_repo=models.OneToOneField(repodb, on_delete=models.CASCADE)
    nota=models.CharField(max_length=3)
    
#poner el def __str__(self): return self.[nombre de variable]