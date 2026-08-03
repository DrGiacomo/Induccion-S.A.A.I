<template>
  <div>
    <h1>Roles</h1>
    <button @click="abrirModal()">Crear</button>

    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Nombre</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rol in roles" :key="rol.id">
          <td>{{ rol.id }}</td>
          <td>{{ rol.nombre_rol }}</td>
          <td>
            <button @click="abrirModal(rol)">Editar</button>
            <button @click="eliminarRol(rol.id)">Eliminar</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Modal -->
    <div v-if="modal">
      <h2>{{ form.id ? 'Editar' : 'Crear' }} Rol</h2>
      <input v-model="form.nombre_rol" placeholder="Nombre del rol" />
      <button @click="guardarRol">Guardar</button>
      <button @click="modal = false">Cancelar</button>
    </div>
  </div>
</template>

<script>
import api from '../api/axios.js'

export default {
  data() {
    return {
      roles: [],
      modal: false,
      form: { id: null, nombre_rol: '' }
    }
  },
  mounted() {
    this.obtenerRoles()
  },
  methods: {
    async obtenerRoles() {
      const res = await api.get('roles/')
      this.roles = res.data
    },
    abrirModal(rol = null) {
      this.form = rol ? { ...rol } : { id: null, nombre_rol: '' }
      this.modal = true
    },
    async guardarRol() {
      if (this.form.id) {
        await api.put(`roles/${this.form.id}/`, this.form)
      } else {
        await api.post('roles/', this.form)
      }
      this.modal = false
      this.obtenerRoles()
    },
    async eliminarRol(id) {
      await api.delete(`roles/${id}/`)
      this.obtenerRoles()
    }
  }
}
</script>