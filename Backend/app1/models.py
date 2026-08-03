from django.db import models
from django.conf import settings

class roldb(models.Model):
    nombre_rol = models.CharField(max_length=20, verbose_name="Nombre del rol", null=False, blank=False)
    
    class Meta:
        db_table = "Roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ['nombre_rol']
    
    def __str__(self):
        return self.nombre_rol

class tipo_id_db(models.Model):
    tipo_id = models.CharField(verbose_name="Tipo de identificacion", null=False, max_length=50)
    
    class Meta:
        db_table = "TipoIdentificacion"  # sin espacios
        verbose_name = "Tipo de identificacion"
    
    def __str__(self):
        return self.tipo_id

class perfildb(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=10, null=False, verbose_name="Numero de telefono", blank=False)
    tipo_id_fk = models.ForeignKey(tipo_id_db, on_delete=models.CASCADE, null=False, blank=False)  # ForeignKey, no OneToOne
    
    class Meta:
        db_table = "Perfiles"
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"
    
    def __str__(self):
        return self.user.username

class areadb(models.Model):
    nombre = models.CharField(max_length=20, null=False, blank=False, verbose_name="Area")
    
    class Meta:
        db_table = "Areas"
        verbose_name = "Area"
        verbose_name_plural = "Areas"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class userarea(models.Model):
    id_user = models.ForeignKey(perfildb, on_delete=models.CASCADE, verbose_name="Usuario")
    id_area = models.ForeignKey(areadb, on_delete=models.CASCADE, verbose_name="Area")
    
    class Meta:
        db_table = "Userarea"
    
    def __str__(self):
        return f"{self.id_user} - {self.id_area}"

class userrol(models.Model):
    id_user = models.ForeignKey(perfildb, on_delete=models.CASCADE, verbose_name="Usuario")
    id_rol = models.ForeignKey(roldb, on_delete=models.CASCADE, verbose_name="Rol")
    
    class Meta:
        db_table = "Userrol"
    
    def __str__(self):
        return f"{self.id_user} - {self.id_rol}"

class trabajadordb(models.Model):
    id_user = models.ForeignKey(perfildb, on_delete=models.CASCADE, verbose_name="Usuario")
    id_userarea = models.ForeignKey(userarea, on_delete=models.CASCADE, verbose_name="Area del usuario")
    id_userrol = models.ForeignKey(userrol, on_delete=models.CASCADE, verbose_name="Rol del usuario")
    
    class Meta:
        db_table = "Trabajador"
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"
    
    def __str__(self):
        return str(self.id_user)

class repodb(models.Model):
    archivo = models.FileField(upload_to='repositorio/', blank=True, null=True) # BinaryField era un error, usa FileField
    nombre = models.CharField(max_length=255)
    tipo = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    id_area = models.ForeignKey(areadb, on_delete=models.CASCADE, verbose_name="Area")
    class Meta:
        db_table = "Repositorio"
        verbose_name = "Repositorio"
        verbose_name_plural = "Repositorios"
    
    def __str__(self):
        return str(self.archivo)

class evaluaciondb(models.Model):
    id_trabajador = models.ForeignKey(trabajadordb, on_delete=models.CASCADE)  # ForeignKey, no OneToOne
    id_repo = models.ForeignKey(repodb, on_delete=models.CASCADE)              # ForeignKey, no OneToOne
    nota = models.DecimalField(max_digits=5, decimal_places=2)                 # DecimalField, no CharField
    
    class Meta:
        db_table = "Evaluacion"
        verbose_name = "Evaluacion"
        verbose_name_plural = "Evaluaciones"
    
    def __str__(self):
        return f"{self.id_trabajador} - {self.nota}"