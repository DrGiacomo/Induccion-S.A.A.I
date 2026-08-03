<template>
  <div>
    <h1>Repositorio</h1>
    <button @click="abrirModal()">Crear</button>

    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Area</th>
          <th>Nombre</th>
          <th>Archivo</th>
          <th>Descripción</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="repos in repo" :key="repos.id">
          <td>{{ repos.id }}</td>
          <td>{{ repos.id_area.nombre }}</td>
          <td>{{ repos.nombre }}</td>
          <td>{{ repos.archivo ? repos.archivo.split('/').pop() : 'Sin archivo' }}</td>
          <td>{{ repos.descripcion }}</td>
          <td>
            <button @click="abrirModal(repos)">Editar</button>
            <button @click="eliminarRepo(repos.id)">Eliminar</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Modal -->
    <div v-if="modal">
      <h2>{{ form.id ? 'Editar' : 'Crear' }} Repositorio</h2>
      <select v-model="form.id_area">
        <option v-for=" area in areas" :key="area.id" :value="area.id">
          {{ area.nombre }}
        </option>
      </select>
        <input v-model="form.nombre" placeholder="Nombre del archivo" />
        <input v-model="form.descripcion" placeholder="Descripción del archivo" />
        <input type="file" @change="handleFileUpload" />
      <button @click="guardarRepo">Guardar</button>
      <button @click="modal = false">Cancelar</button>
    </div>
  </div>
</template>

<script>
import api from '../api/axios.js'

export default {
  data() {
    return {
      repo: [],
      areas: [],
      modal: false,
      form: { id: null, id_area: 'null' }
    }
  },
  mounted() {
    this.obtenerRepo()
    this.obtenerAreas()
    this.obtenerAreas()
  },
  methods: {
    async obtenerRepo() {
      const res = await api.get('repo/')
      this.repo = res.data
    },
    abrirModal(repo = null) {
    this.form = repo ? { ...repo, archivo: null } : { id: null, id_area: '', archivo: null }
    this.modal = true
    },
    handleFileUpload(event) {
  this.form.archivo = event.target.files[0]
    },

    async guardarRepo() {
  try {
    const formData = new FormData()
    formData.append('id_area', this.form.id_area)
    formData.append('nombre', this.form.nombre)
    formData.append('descripcion', this.form.descripcion || '')
    if (this.form.archivo) {
      formData.append('archivo', this.form.archivo)
    }

    if (this.form.id) {
      await api.put(`repo/${this.form.id}/`, formData)
    } else {
     await api.post('repo/', formData, {
  headers: {
    'Content-Type': 'multipart/form-data'
  }
})
    }
    this.modal = false
    this.obtenerRepo()
  } catch (error) {
    console.log(error.response.data)
  }
},
    async eliminarRepo(id) {
      await api.delete(`repo/${id}/`)
      this.obtenerRepo()
    },
    async obtenerAreas(){
        const res= await api.get('areas/')
        this.areas = res.data
    }
  }
}
</script>