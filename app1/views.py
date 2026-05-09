from django.shortcuts import render, get_object_or_404, redirect
from .models import roldb, tipo_id_db, perfildb, areadb, userarea, userrol, trabajadordb,repodb,evaluaciondb

# Create your views here.

def indexView(request):
    
    objeto = roldb.objects.all().order_by("-id")
    
    return render(request, 'rol/index.html', {"objeto": objeto} )
#Django llora cuando las comas estar muy cerca de las comillas
#para tener en cuenta: la palabra antes de los 2 puntos es la que va a la plantilla, la que se va a usar en el for

def crearrol(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre_rol")
        roldb.objects.create(nombre_rol=nombre)
        return redirect("/")
    
    return render(request, "rol/create.html")

def updaterol(request, id):
    rol = get_object_or_404(roldb, id=id)

    if request.method == "POST":
        rol.nombre_rol = request.POST.get("nombre_rol")
        rol.save()
        return redirect("/")

    return render(request, "rol/update.html", {"rol": rol})
#recuerda gran imbecil si estan dentro de una carpeta debes ponerle nombre de carpeta/nombre de la plantilla
#al menos no usamos chatgpt para este error

def deleterol(request, id):
    rol = get_object_or_404(roldb, id=id)
    rol.delete()
    return redirect("/")
