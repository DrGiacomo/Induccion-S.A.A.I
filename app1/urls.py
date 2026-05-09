from django.urls import path
from .views import indexView, crearrol,updaterol, deleterol #poner el nombre de todas las funciones que se hagan en urls


urlpatterns = [
    path('',indexView),
    path('crearrol',crearrol),
    path('edit/<int:id>/}',updaterol, name="editarrol"),
    path('delete/<int:id>/}',deleterol, name="borrar")
]