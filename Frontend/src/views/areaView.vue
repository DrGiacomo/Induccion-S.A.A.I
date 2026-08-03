<template>
  <div>
    <h1>Areas</h1>
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
        <tr v-for="area in areas" :key="area.id">
          <td>{{ area.id }}</td>
          <td>{{ area.nombre }}</td>
          <td>
            <button @click="abrirModal(area)">Editar</button>
            <button @click="eliminarArea(area.id)">Eliminar</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Modal -->
    <div v-if="modal">
      <h2>{{ form.id ? 'Editar' : 'Crear' }} Area</h2>
      <input v-model="form.nombre" placeholder="Nombre del area" />
      <button @click="guardarArea">Guardar</button>
      <button @click="modal = false">Cancelar</button>
    </div>
  </div>
</template>

<script>
import api from '../api/axios.js'

export default {
  data() {
    return {
      areas: [],
      modal: false,
      form: { id: null, nombre: '' }
    }
  },
  mounted() {
    this.obtenerAreas()
  },
  methods: {
    async obtenerAreas() {
      const res = await api.get('areas/')
      this.areas = res.data
    },
    abrirModal(area = null) {
      this.form = area ? { ...area } : { id: null, nombre: '' }
      this.modal = true
    },
    async guardarArea() {
      if (this.form.id) {
        await api.put(`areas/${this.form.id}/`, this.form)
      } else {
        await api.post('areas/', this.form)
      }
      this.modal = false
      this.obtenerAreas()
    },
    async eliminarArea(id) {
      await api.delete(`areas/${id}/`)
      this.obtenerAreas()
    }
  }
}
</script>