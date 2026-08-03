<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import { useTema } from '@/composables/useTema.js'

const router = useRouter()
const { estado, misAreas, areaACargo, nombre, iniciales, salir } = useAuth()
const { tema, alternar } = useTema()

const menuAbierto = ref(false)
const sidebarAbierto = ref(false)

/*
  El sidebar es la biblioteca: cada área es un pasillo.

  Se marcan visualmente los que son propios. Los demás no se ocultan a
  propósito — que exista un pasillo cerrado y sepas a quién pedir la llave
  es justamente P4. Ocultarlos dejaría a la gente sin saber ni qué preguntar.
*/
const areasPropias = computed(() => {
  const ids = new Set(misAreas.value.map((a) => a.id))
  if (areaACargo.value) ids.add(areaACargo.value.id)
  return ids
})

const enlaces = computed(() => {
  const base = [
    { nombre: 'inicio', texto: 'Mi inducción', icono: 'pi-home' },
    { nombre: 'buscar', texto: 'Buscar', icono: 'pi-search' },
  ]
  if (estado.esAdmin || estado.esJefeDeArea) {
    base.push({ nombre: 'curaduria', texto: 'Curaduría', icono: 'pi-pencil' })
  }
  return base
})

async function cerrarSesion() {
  await salir()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-screen flex bg-slate-50 oscuro:bg-slate-950">

    <!-- ── Sidebar ─────────────────────────────────────────────── -->
    <aside
      class="fixed lg:static inset-y-0 left-0 z-40 w-64 shrink-0 flex flex-col
             bg-white oscuro:bg-slate-900 border-r border-slate-200 oscuro:border-slate-800
             transition-transform lg:translate-x-0"
      :class="sidebarAbierto ? 'translate-x-0' : '-translate-x-full'">

      <div class="h-16 flex items-center gap-2.5 px-5 border-b border-slate-200
                  oscuro:border-slate-800">
        <div class="w-8 h-8 rounded-lg bg-saai-600 grid place-items-center
                    text-white font-bold text-sm">S</div>
        <span class="font-bold tracking-tight">S.A.A.I</span>
      </div>

      <nav class="flex-1 overflow-y-auto p-3 space-y-1">
        <RouterLink
          v-for="e in enlaces" :key="e.nombre"
          :to="{ name: e.nombre }"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition
                 text-slate-600 oscuro:text-slate-300
                 hover:bg-slate-100 oscuro:hover:bg-slate-800"
          active-class="!bg-saai-50 !text-saai-700 oscuro:!bg-saai-950 oscuro:!text-saai-300"
          @click="sidebarAbierto = false">
          <i :class="['pi', e.icono, 'text-base']" />
          {{ e.texto }}
        </RouterLink>

        <div class="pt-5">
          <p class="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider
                    text-slate-400">
            Áreas
          </p>
          <div v-if="misAreas.length === 0"
               class="px-3 py-2 text-xs text-slate-400 italic">
            Todavía no perteneces a ninguna área.
          </div>
          <div
            v-for="a in misAreas" :key="a.id"
            class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm
                   text-slate-600 oscuro:text-slate-300">
            <i class="pi pi-folder text-saai-500 text-sm" />
            <span class="truncate">{{ a.nombre }}</span>
          </div>
          <div v-if="areaACargo"
               class="mt-1 flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm
                      bg-amber-50 oscuro:bg-amber-950/30 text-amber-800 oscuro:text-amber-200">
            <i class="pi pi-key text-sm" />
            <span class="truncate">Diriges {{ areaACargo.nombre }}</span>
          </div>
        </div>
      </nav>

      <div class="p-3 border-t border-slate-200 oscuro:border-slate-800">
        <a v-if="estado.esAdmin || estado.esJefeDeArea"
           href="http://localhost:8000/admin/" target="_blank" rel="noopener"
           class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-500
                  hover:bg-slate-100 oscuro:hover:bg-slate-800">
          <i class="pi pi-cog text-base" />
          Administración
          <i class="pi pi-external-link text-xs ml-auto opacity-50" />
        </a>
      </div>
    </aside>

    <div v-if="sidebarAbierto"
         class="fixed inset-0 z-30 bg-black/40 lg:hidden"
         @click="sidebarAbierto = false" />

    <!-- ── Contenido ───────────────────────────────────────────── -->
    <div class="flex-1 flex flex-col min-w-0">
      <header class="h-16 shrink-0 flex items-center gap-3 px-4 lg:px-6
                     bg-white oscuro:bg-slate-900 border-b border-slate-200
                     oscuro:border-slate-800">
        <button class="lg:hidden w-9 h-9 grid place-items-center rounded-lg
                       hover:bg-slate-100 oscuro:hover:bg-slate-800"
                aria-label="Abrir menú"
                @click="sidebarAbierto = true">
          <i class="pi pi-bars" />
        </button>

        <div class="flex-1" />

        <button
          class="w-9 h-9 grid place-items-center rounded-lg text-slate-500
                 hover:bg-slate-100 oscuro:hover:bg-slate-800"
          :title="tema === 'oscuro' ? 'Modo claro' : 'Modo oscuro'"
          @click="alternar">
          <i :class="tema === 'oscuro' ? 'pi pi-sun' : 'pi pi-moon'" />
        </button>

        <div class="relative">
          <button
            class="flex items-center gap-2 pl-1 pr-2 py-1 rounded-lg
                   hover:bg-slate-100 oscuro:hover:bg-slate-800"
            @click="menuAbierto = !menuAbierto">
            <span class="w-8 h-8 rounded-full bg-saai-600 text-white grid place-items-center
                         text-xs font-semibold">{{ iniciales }}</span>
            <span class="hidden sm:block text-sm font-medium max-w-[10rem] truncate">
              {{ nombre }}
            </span>
            <i class="pi pi-angle-down text-xs text-slate-400" />
          </button>

          <div v-if="menuAbierto"
               class="absolute right-0 mt-2 w-56 rounded-xl bg-white oscuro:bg-slate-800
                      border border-slate-200 oscuro:border-slate-700 shadow-xl py-1 z-50"
               @click="menuAbierto = false">
            <div class="px-4 py-2.5 border-b border-slate-100 oscuro:border-slate-700">
              <p class="text-sm font-medium truncate">{{ nombre }}</p>
              <p class="text-xs text-slate-500 truncate">
                {{ estado.usuario?.cargo_nombre || 'Sin cargo asignado' }}
              </p>
            </div>
            <RouterLink :to="{ name: 'cambiar-password' }"
                        class="flex items-center gap-2.5 px-4 py-2 text-sm
                               hover:bg-slate-50 oscuro:hover:bg-slate-700">
              <i class="pi pi-key text-sm" /> Cambiar contraseña
            </RouterLink>
            <button
              class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-red-600
                     hover:bg-red-50 oscuro:hover:bg-red-950/30"
              @click="cerrarSesion">
              <i class="pi pi-sign-out text-sm" /> Cerrar sesión
            </button>
          </div>
        </div>
      </header>

      <main class="flex-1 overflow-y-auto p-4 lg:p-6">
        <RouterView />
      </main>
    </div>
  </div>
</template>
