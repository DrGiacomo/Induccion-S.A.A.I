import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'

/*
  Rutas y guardas.

  ⚠️ Estas guardas son **comodidad, no seguridad**. Sirven para que nadie
  aterrice en una pantalla vacía o vea un menú que no le corresponde. La
  barrera de verdad está en el backend: aunque alguien esquivara todo esto,
  la API le devolvería 403 igual. Confiar en el router para proteger datos
  es el error clásico — el JavaScript del navegador lo controla el usuario.
*/

const rutas = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { publica: true, sinLayout: true },
  },
  {
    path: '/cambiar-password',
    name: 'cambiar-password',
    component: () => import('@/views/auth/CambiarPasswordView.vue'),
    meta: { sinLayout: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/LayoutPrincipal.vue'),
    children: [
      { path: '', name: 'inicio', component: () => import('@/views/InicioView.vue') },
      { path: 'buscar', name: 'buscar', component: () => import('@/views/BuscarView.vue') },
      {
        path: 'termino/:id',
        name: 'termino',
        component: () => import('@/views/TerminoView.vue'),
        props: true,
      },
      {
        path: 'curaduria',
        name: 'curaduria',
        component: () => import('@/views/CuraduriaView.vue'),
        meta: { soloCuradores: true },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: { name: 'inicio' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes: rutas,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (destino) => {
  const { estado, autenticado, cargarSesion } = useAuth()

  // Al primer arranque hay que preguntarle al backend si ya hay sesión.
  // Sin esto, recargar la página con F5 expulsaría al usuario al login.
  if (!estado.iniciado) {
    await cargarSesion()
  }

  if (destino.meta.publica) {
    return autenticado.value ? { name: 'inicio' } : true
  }

  if (!autenticado.value) {
    return { name: 'login', query: { volverA: destino.fullPath } }
  }

  // Con la contraseña sin cambiar no se llega a ninguna otra pantalla.
  // Si se pudiera saltar, el paso obligatorio sería decorativo.
  if (estado.debeCambiarPassword && destino.name !== 'cambiar-password') {
    return { name: 'cambiar-password' }
  }

  if (destino.meta.soloCuradores && !estado.esAdmin && !estado.esJefeDeArea) {
    return { name: 'inicio' }
  }

  return true
})

export default router
