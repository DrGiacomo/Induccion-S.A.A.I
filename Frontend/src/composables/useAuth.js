import { computed, reactive, readonly } from 'vue'
import api, { prepararCsrf } from '@/api/axios.js'

/*
  Estado de sesión, compartido por toda la aplicación.

  Es un objeto reactivo a nivel de módulo, no un gestor de estado. Para lo
  que hace falta —quién soy y qué puedo ver— basta y sobra, y ahorra una
  dependencia más que instalar y mantener.

  ⚠️ Lo que hay aquí es para **pintar la interfaz**, no para proteger nada.
  Ocultar un botón no es seguridad: quien quiera saltárselo llama a la API
  directamente. La barrera de verdad está en el backend, y estas mismas
  reglas se prueban allí en la suite de permisos.
*/

const estado = reactive({
  usuario: null,
  esAdmin: false,
  esJefeDeArea: false,
  debeCambiarPassword: false,
  cargando: true,          // arranca en true: aún no sabemos si hay sesión
  iniciado: false,
})

export function useAuth() {
  const autenticado = computed(() => estado.usuario !== null)

  const misAreas = computed(() => estado.usuario?.areas ?? [])

  const areaACargo = computed(() => estado.usuario?.area_a_cargo ?? null)

  const nombre = computed(
    () => estado.usuario?.nombre_completo || estado.usuario?.username || '',
  )

  const iniciales = computed(() => {
    const partes = nombre.value.trim().split(/\s+/)
    if (!partes[0]) return '?'
    return (partes[0][0] + (partes[1]?.[0] ?? '')).toUpperCase()
  })

  /** Comprueba si ya hay sesión abierta. Se llama una vez al arrancar. */
  async function cargarSesion() {
    estado.cargando = true
    await prepararCsrf()
    try {
      const { data } = await api.get('auth/yo/')
      aplicar(data)
    } catch {
      limpiar()
    } finally {
      estado.cargando = false
      estado.iniciado = true
    }
    return autenticado.value
  }

  async function entrar(username, password) {
    const { data } = await api.post('auth/login/', { username, password })
    aplicar(data)
    return data
  }

  async function salir() {
    try {
      await api.post('auth/logout/')
    } finally {
      limpiar()
    }
  }

  async function cambiarPassword(actual, nueva) {
    await api.post('auth/cambiar-password/', {
      password_actual: actual,
      password_nueva: nueva,
    })
    estado.debeCambiarPassword = false
  }

  function aplicar(data) {
    estado.usuario = data.usuario
    estado.esAdmin = data.es_admin ?? false
    estado.esJefeDeArea = data.es_jefe_de_area ?? false
    estado.debeCambiarPassword = data.debe_cambiar_password ?? false
  }

  function limpiar() {
    estado.usuario = null
    estado.esAdmin = false
    estado.esJefeDeArea = false
    estado.debeCambiarPassword = false
  }

  return {
    estado: readonly(estado),
    autenticado,
    misAreas,
    areaACargo,
    nombre,
    iniciales,
    cargarSesion,
    entrar,
    salir,
    cambiarPassword,
    limpiar,
  }
}
