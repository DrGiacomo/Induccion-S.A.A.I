<template>
  <div>
    <h1>Trabajadores</h1>
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
        <tr v-for="tipoId in tiposId" :key="tipoId.id">
          <td>{{ tipoId.id }}</td>
          <td>{{ tipoId.tipo_id }}</td>
          <td>
            <button @click="abrirModal(tipoId)">Editar</button>
            <button @click="eliminarTipoId(tipoId.id)">Eliminar</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Modal -->
    <div v-if="modal">
      <h2>{{ form.id ? 'Editar' : 'Crear' }} Tipo de Identificación</h2>
      <input v-model="form.tipo_id" placeholder="Tipo de identificación" />
      <button @click="guardarTipoId">Guardar</button>
      <button @click="modal = false">Cancelar</button>
    </div>
  </div>
</template>

<script>
import api from '../api/axios.js'

export default {
  data() {
    return {
      tiposId: [],
      modal: false,
      form: { id: null, tipo_id: '' }
    }
  },
  mounted() {
    this.obtenerTiposId()
  },
  methods: {
    async obtenerTiposId() {
      const res = await api.get('tipos-id/')
      this.tiposId = res.data
    },
    abrirModal(tipoId = null) {
      this.form = tipoId ? { ...tipoId } : { id: null, tipo_id: '' }
      this.modal = true
    },
    async guardarTipoId() {
      if (this.form.id) {
        await api.put(`tipos-id/${this.form.id}/`, this.form)
      } else {
        await api.post('tipos-id/', this.form)
      }
      this.modal = false
      this.obtenerTiposId()
    },
    async eliminarTipoId(id) {
      await api.delete(`tipos-id/${id}/`)
      this.obtenerTiposId()
    }
  }
}
</script>