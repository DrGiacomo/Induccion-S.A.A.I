import axios from 'axios'

/*
  Cliente HTTP de S.A.A.I.

  Dos cosas de aquí no son opcionales, y sin ellas el login "no funciona"
  sin decir por qué:

  1. `withCredentials: true` — hace que el navegador mande la cookie de
     sesión en cada petición. Sin esto, cada llamada llega como si fuera de
     un desconocido, aunque el login haya ido bien.

  2. La cabecera `X-CSRFToken` — Django rechaza cualquier POST, PUT o DELETE
     que no la traiga. El token se lee de una cookie que **no** es HttpOnly,
     justamente para que este archivo pueda leerla. La de sesión sí lo es, y
     este código no la ve nunca: esa es toda la protección contra el robo de
     sesión por un script inyectado.
*/

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

function leerCookie(nombre) {
  const encontrada = document.cookie
    .split('; ')
    .find((c) => c.startsWith(nombre + '='))
  return encontrada ? decodeURIComponent(encontrada.split('=')[1]) : null
}

/** Pide la cookie CSRF. Se llama una vez al arrancar, antes del login. */
export async function prepararCsrf() {
  try {
    await api.get('auth/csrf/')
  } catch {
    // Si el backend no responde, el login dará un error claro más adelante.
    // No se rompe el arranque de la aplicación por esto.
  }
}

api.interceptors.request.use((config) => {
  const metodo = (config.method || 'get').toUpperCase()
  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(metodo)) {
    const token = leerCookie('csrftoken')
    if (token) config.headers['X-CSRFToken'] = token
  }
  // Con FormData hay que dejar que el navegador ponga el Content-Type él
  // solo, con el `boundary` que corresponda. Fijarlo a mano rompe las
  // subidas de archivos, y el fallo no dice nada útil.
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }
  return config
})

/*
  Manejo central de errores.

  Un 401 significa que la sesión caducó o nunca existió. Se avisa al resto de
  la aplicación con un evento en vez de redirigir desde aquí: este archivo no
  tiene por qué saber que existe un router, y así el layout reacciona sin
  depender de axios.
*/
api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      window.dispatchEvent(new CustomEvent('saai:sesion-caducada'))
    }
    error.mensaje = extraerMensaje(error)
    return Promise.reject(error)
  },
)

/** Saca un mensaje legible de la respuesta de DRF, cuya forma varía. */
function extraerMensaje(error) {
  const d = error.response?.data
  if (!d) return 'No se pudo conectar con el servidor. ¿Está encendido el backend?'
  if (typeof d === 'string') return d
  if (d.detail) return d.detail
  const primera = Object.entries(d)[0]
  if (!primera) return 'Ocurrió un error.'
  const [campo, valor] = primera
  const texto = Array.isArray(valor) ? valor[0] : valor
  return campo === 'non_field_errors' ? texto : `${campo}: ${texto}`
}

export default api
