<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import { useTema } from '@/composables/useTema.js'

const router = useRouter()
const route = useRoute()
const { entrar } = useAuth()
const { tema, alternar } = useTema()

const usuario = ref('')
const password = ref('')
const verPassword = ref(false)
const error = ref('')
const enviando = ref(false)
const campoUsuario = ref(null)

onMounted(() => campoUsuario.value?.focus())

async function enviar() {
  error.value = ''
  enviando.value = true
  try {
    const datos = await entrar(usuario.value, password.value)
    // Si la contraseña la entregó otra persona, lo primero es cambiarla.
    if (datos.debe_cambiar_password) {
      router.push({ name: 'cambiar-password' })
      return
    }
    router.push(route.query.volverA || { name: 'inicio' })
  } catch (e) {
    error.value = e.mensaje || 'No se pudo iniciar sesión.'
    password.value = ''
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4
              bg-gradient-to-br from-slate-100 via-white to-saai-50
              oscuro:from-slate-950 oscuro:via-slate-900 oscuro:to-slate-900">

    <button
      class="fixed top-4 right-4 w-10 h-10 rounded-full grid place-items-center
             text-slate-500 hover:bg-slate-200 oscuro:hover:bg-slate-800 transition"
      :title="tema === 'oscuro' ? 'Modo claro' : 'Modo oscuro'"
      @click="alternar">
      <i :class="tema === 'oscuro' ? 'pi pi-sun' : 'pi pi-moon'" />
    </button>

    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-saai-600 grid place-items-center
                    text-white text-2xl font-bold shadow-lg shadow-saai-600/25">
          S
        </div>
        <h1 class="text-2xl font-bold tracking-tight">S.A.A.I</h1>
        <p class="text-sm text-slate-500 oscuro:text-slate-400 mt-1">
          Sistema de Ayuda Automatizado para la Inducción
        </p>
      </div>

      <form
        class="bg-white oscuro:bg-slate-800 rounded-2xl shadow-xl shadow-slate-900/5
               oscuro:shadow-black/20 p-6 space-y-4 border border-slate-200/60
               oscuro:border-slate-700"
        @submit.prevent="enviar">

        <div>
          <label for="usuario" class="block text-sm font-medium mb-1.5">Usuario</label>
          <input
            id="usuario" ref="campoUsuario" v-model="usuario" type="text"
            autocomplete="username" required
            class="w-full px-3 py-2.5 rounded-lg border border-slate-300 oscuro:border-slate-600
                   bg-white oscuro:bg-slate-900 focus:border-saai-500 outline-none transition"
            placeholder="tu.usuario" />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium mb-1.5">Contraseña</label>
          <div class="relative">
            <input
              id="password" v-model="password"
              :type="verPassword ? 'text' : 'password'"
              autocomplete="current-password" required
              class="w-full px-3 py-2.5 pr-10 rounded-lg border border-slate-300
                     oscuro:border-slate-600 bg-white oscuro:bg-slate-900
                     focus:border-saai-500 outline-none transition"
              placeholder="••••••••" />
            <button
              type="button" tabindex="-1"
              class="absolute right-2 top-1/2 -translate-y-1/2 w-7 h-7 grid place-items-center
                     text-slate-400 hover:text-slate-600 oscuro:hover:text-slate-200"
              :aria-label="verPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              @click="verPassword = !verPassword">
              <i :class="verPassword ? 'pi pi-eye-slash' : 'pi pi-eye'" class="text-sm" />
            </button>
          </div>
        </div>

        <!--
          El mensaje de error es deliberadamente vago: "usuario o contraseña
          incorrectos", nunca "ese usuario no existe". Distinguirlos le
          confirma a quien prueba al azar qué cuentas hay, que es media
          faena hecha para él. El backend ya devuelve el mismo texto en los
          dos casos; aquí solo se pinta.
        -->
        <p v-if="error"
           class="text-sm text-red-600 oscuro:text-red-400 bg-red-50 oscuro:bg-red-950/40
                  border border-red-200 oscuro:border-red-900 rounded-lg px-3 py-2"
           role="alert">
          <i class="pi pi-exclamation-circle mr-1" />{{ error }}
        </p>

        <button
          type="submit" :disabled="enviando"
          class="w-full py-2.5 rounded-lg bg-saai-600 hover:bg-saai-700 active:bg-saai-800
                 disabled:opacity-60 disabled:cursor-not-allowed text-white font-medium
                 transition shadow-lg shadow-saai-600/20">
          <i v-if="enviando" class="pi pi-spin pi-spinner mr-2" />
          {{ enviando ? 'Entrando…' : 'Entrar' }}
        </button>
      </form>

      <p class="text-center text-xs text-slate-400 mt-6">
        ¿No tienes cuenta? Aquí nadie se registra solo:
        pídesela a tu jefe de área.
      </p>
    </div>
  </div>
</template>
