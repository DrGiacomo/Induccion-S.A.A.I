<template>
  <div>
    <h1>Asignar Area</h1>
    <button @click="abrirModal()">Crear</button>

    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Perfil</th>
          <th>Area</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="userarea in userarea" :key="userarea.id">
          <td>{{ userarea.id }}</td>
          <td>{{ userarea.perfil_nombre }}</td>
          <td>{{ userarea.area_nombre }}</td>
          <td>
            <button @click="abrirModal(userarea)">Editar</button>
            <button @click="eliminarUserArea(userarea.id)">Eliminar</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Modal -->
    <div v-if="modal">
      <h2>{{ form.id ? 'Editar' : 'Crear' }} Area</h2>

      <select v-model="form.id_user">
        <option v-for=" perfil in perfiles" :key="perfil.id" :value="perfil.id">
          {{ perfil.user.username }}
        </option>
      </select>

      <select v-model="form.id_area">
        <option v-for=" area in areas" :key="area.id" :value="area.id">
          {{ area.nombre }}
        </option>
      </select>

      <button @click="guardarUserArea">Guardar</button>
      <button @click="modal = false">Cancelar</button>
    </div>
  </div>
</template>

<script>
import api from '../api/axios.js'

export default {
  data() {
    return {
      userarea: [],
      perfiles: [],
      areas: [],
      modal: false,
      form: { id: null, id_user: 'null', id_area: 'null' }
    }
  },
  mounted() {
    this.obtenerUserArea()
    this.obtenerPerfiles()
    this.obtenerAreas()
  },
  methods: {
    async obtenerUserArea() {
      const res = await api.get('userarea/')
      this.userarea = res.data
    },
    abrirModal(userarea = null) {
      this.form = userarea ? { ...userarea } : { id: null, id_user: '', id_area: '' }
      this.modal = true
    },
    async guardarUserArea() {
      if (this.form.id) {
        await api.put(`userarea/${this.form.id}/`, this.form)
      } else {
        await api.post('userarea/', this.form)
      }
      this.modal = false
      this.obtenerUserArea()
    },
    async eliminarUserArea(id) {
      await api.delete(`userarea/${id}/`)
      this.obtenerUserArea()
    },

    async obtenerPerfiles() {
      const res = await api.get('perfiles/')
      this.perfiles = res.data
    },  

    async obtenerAreas(){
        const res= await api.get('areas/')
        this.areas = res.data
    }
  }
}
</script>