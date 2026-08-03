<template>
  <div>
    <h1>Asignar Rol</h1>
    <button @click="abrirModal()">Crear</button>

    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Perfil</th>
          <th>Rol</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ur in userrol" :key="ur.id">
          <td>{{ ur.id }}</td>
          <td>{{ ur.perfil_nombre }}</td>
          <td>{{ ur.rol_nombre }}</td>
          <td>
            <button @click="abrirModal(ur)">Editar</button>
            <button @click="eliminarUserRol(ur.id)">Eliminar</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Modal -->
    <div v-if="modal">
      <h2>{{ form.id ? 'Editar' : 'Crear' }} Rol</h2>

      <select v-model="form.id_user">
        <option v-for=" perfil in perfiles" :key="perfil.id" :value="perfil.id">
          {{ perfil.user.username }}
        </option>
      </select>

      <select v-model="form.id_rol">
        <option v-for=" rol in roles" :key="rol.id" :value="rol.id">
          {{ rol.nombre_rol }}
        </option>
      </select>

      <button @click="guardarUserRol">Guardar</button>
      <button @click="modal = false">Cancelar</button>
    </div>
  </div>
</template>

<script>
import api from '../api/axios.js'

export default {
  data() {
    return {
      userrol: [],
      perfiles: [],
      roles: [],
      modal: false,
      form: { id: null, id_user: 'null', id_rol: 'null' }
    }
  },
  mounted() {
    this.obtenerUserRol()
    this.obtenerPerfiles()
    this.obtenerRoles()
  },
  methods: {
    async obtenerUserRol() {
      const res = await api.get('userrol/')
      this.userrol = res.data
    },
    abrirModal(userrol = null) {
      this.form = userrol ? { ...userrol } : { id: null, id_user: '', id_rol: '' }
      this.modal = true
    },
    async guardarUserRol() {
      if (this.form.id) {
        await api.put(`userrol/${this.form.id}/`, this.form)
      } else {
        await api.post('userrol/', this.form)
      }
      this.modal = false
      this.obtenerUserRol()
    },
    async eliminarUserRol(id) {
      await api.delete(`userrol/${id}/`)
      this.obtenerUserRol()
    },

    async obtenerPerfiles() {
      const res = await api.get('perfiles/')
      this.perfiles = res.data
    },  

    async obtenerRoles(){
        const res= await api.get('roles/')
        this.roles = res.data
    }
  }
}
</script>