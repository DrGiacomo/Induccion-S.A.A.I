<template>
  <div>
    <h1>Perfiles</h1>
    <button @click="abrirModal()">Crear</button>

    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Username</th>
          <th>Nombre</th>
          <th>Apellido</th>
          <th>Email</th>
          <th>Teléfono</th>
          <th>Tipo ID</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="perfil in perfiles" :key="perfil.id">
          <td>{{ perfil.id }}</td>
          <td>{{ perfil.user.username }}</td>
          <td>{{ perfil.user.first_name }}</td>
          <td>{{ perfil.user.last_name }}</td>
          <td>{{ perfil.user.email }}</td>
          <td>{{ perfil.telefono }}</td>
          <td>{{ perfil.tipo_id_fk }}</td>
          <td>
            <button @click="abrirModal(perfil)">Editar</button>
            <button @click="eliminarPerfil(perfil.id)">Eliminar</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="modal">
      <h2>{{ form.id ? 'Editar' : 'Crear' }} Perfil</h2>
      <input v-model="form.username" placeholder="Username" />
      <input v-model="form.first_name" placeholder="Nombre" />
      <input v-model="form.last_name" placeholder="Apellido" />
      <input v-model="form.email" placeholder="Email" />
      <input v-model="form.password" placeholder="Password" type="password" />
      <input v-model="form.telefono" placeholder="Teléfono" />
      <select v-model="form.tipo_id_fk">
        <option v-for="tipo in tiposId" :key="tipo.id" :value="tipo.id">
          {{ tipo.tipo_id }}
        </option>
      </select>
      <button @click="guardarPerfil">Guardar</button>
      <button @click="modal = false">Cancelar</button>
    </div>
  </div>
</template>

<script>
import api from '../api/axios.js'

export default {
  data() {
    return {
      perfiles: [],
      tiposId: [],
      modal: false,
      form: {
        id: null,
        username: '',
        first_name: '',
        last_name: '',
        email: '',
        password: '',
        telefono: '',
        tipo_id_fk: null
      }
    }
  },
  mounted() {
    this.obtenerPerfiles()
    this.obtenerTiposId()
  },
  methods: {
    async obtenerPerfiles() {
      const res = await api.get('perfiles/')
      this.perfiles = res.data
    },
    async obtenerTiposId() {
      const res = await api.get('tipos-id/')
      this.tiposId = res.data
    },
    abrirModal(perfil = null) {
      if (perfil) {
        this.form = {
          id: perfil.id,
          username: perfil.user.username,
          first_name: perfil.user.first_name,
          last_name: perfil.user.last_name,
          email: perfil.user.email,
          password: '',
          telefono: perfil.telefono,
          tipo_id_fk: perfil.tipo_id_fk
        }
      } else {
        this.form = { id: null, username: '', first_name: '', last_name: '', email: '', password: '', telefono: '', tipo_id_fk: null }
      }
      this.modal = true
    },
   async guardarPerfil() {
    const payload = {
        user: {
        username: this.form.username,
        first_name: this.form.first_name,
        last_name: this.form.last_name,
        email: this.form.email,
        password: this.form.password
        },
        telefono: this.form.telefono,
        tipo_id_fk: this.form.tipo_id_fk
    }
    if (this.form.id) {
        await api.put(`perfiles/${this.form.id}/`, payload)
    } else {
        await api.post('perfiles/', payload)
    }
    this.modal = false
    this.obtenerPerfiles()
    },
    async eliminarPerfil(id) {
      await api.delete(`perfiles/${id}/`)
      this.obtenerPerfiles()
    }
  }
}
</script>