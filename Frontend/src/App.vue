<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'

const router = useRouter()
const { estado, limpiar } = useAuth()

/*
  Un 401 en cualquier llamada significa que la sesión caducó. El cliente HTTP
  lanza un evento en vez de redirigir él mismo —no tiene por qué conocer el
  router— y aquí se recoge.

  Sin esto, una sesión caducada deja al usuario mirando pantallas vacías sin
  entender por qué: la aplicación parece rota cuando en realidad solo hay que
  volver a entrar (P2, honestidad).
*/
function sesionCaducada() {
  limpiar()
  if (router.currentRoute.value.name !== 'login') {
    router.push({
      name: 'login',
      query: { volverA: router.currentRoute.value.fullPath },
    })
  }
}

onMounted(() => window.addEventListener('saai:sesion-caducada', sesionCaducada))
onUnmounted(() => window.removeEventListener('saai:sesion-caducada', sesionCaducada))
</script>

<template>
  <!-- Mientras se comprueba si hay sesión, ni login ni contenido: un
       parpadeo entre las dos pantallas es feo y confunde. -->
  <div v-if="!estado.iniciado"
       class="min-h-screen grid place-items-center bg-slate-50 oscuro:bg-slate-950">
    <div class="text-center">
      <div class="w-12 h-12 mx-auto rounded-xl bg-saai-600 grid place-items-center
                  text-white font-bold animate-pulse">S</div>
      <p class="mt-3 text-sm text-slate-400">Cargando…</p>
    </div>
  </div>

  <RouterView v-else />
</template>
