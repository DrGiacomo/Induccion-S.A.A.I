<script setup>
import { ref, watch } from 'vue'
import api from '@/api/axios.js'

/*
  Buscador — versión provisional.

  ⚠️ Esto NO es el buscador del proyecto. Es lo mínimo para que el cascarón
  de la Fase 1 sea navegable: una búsqueda por texto contra el filtro que
  DRF ya trae, sin ranking, sin stemming en español, sin tolerancia a
  erratas y sin sugerencias mientras escribes.

  El buscador de verdad es la Fase 3 completa (`P3.1`–`P3.9`), y es donde el
  proyecto se juega su razón de ser (P5). Se deja esto para no dejar una
  pantalla muerta, y para poder comprobar que los permisos funcionan de
  punta a punta desde la interfaz.
*/

const consulta = ref('')
const resultados = ref([])
const buscando = ref(false)
const buscado = ref(false)
const error = ref('')

let temporizador = null

watch(consulta, () => {
  clearTimeout(temporizador)
  if (consulta.value.trim().length < 2) {
    resultados.value = []
    buscado.value = false
    return
  }
  temporizador = setTimeout(buscar, 350)
})

async function buscar() {
  buscando.value = true
  error.value = ''
  try {
    const { data } = await api.get('terminos/', { params: { search: consulta.value } })
    resultados.value = data.results ?? data
    buscado.value = true
  } catch (e) {
    error.value = e.mensaje
  } finally {
    buscando.value = false
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <header>
      <h1 class="text-2xl font-bold tracking-tight">Buscar</h1>
      <p class="text-slate-500 oscuro:text-slate-400 mt-1">
        Escribe una palabra y mira qué significa en esta empresa.
      </p>
    </header>

    <div class="relative">
      <i class="pi pi-search absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
      <input
        v-model="consulta" type="search" autofocus
        placeholder="merma, PQR, la 47…"
        class="w-full pl-11 pr-4 py-3.5 rounded-xl text-lg
               bg-white oscuro:bg-slate-900 border border-slate-200 oscuro:border-slate-700
               focus:border-saai-500 outline-none shadow-sm transition" />
      <i v-if="buscando"
         class="pi pi-spin pi-spinner absolute right-4 top-1/2 -translate-y-1/2 text-saai-500" />
    </div>

    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

    <!-- P2: cuando no hay nada, se dice. No se rellena con algo parecido. -->
    <div v-if="buscado && !resultados.length && !buscando"
         class="rounded-xl bg-white oscuro:bg-slate-900 border border-slate-200
                oscuro:border-slate-800 p-8 text-center">
      <i class="pi pi-inbox text-4xl text-slate-300 oscuro:text-slate-600" />
      <h2 class="mt-3 font-semibold">No encontré «{{ consulta }}»</h2>
      <p class="text-sm text-slate-500 mt-1.5 max-w-md mx-auto">
        Puede que todavía nadie lo haya documentado, o que pertenezca a un área
        cuyo contenido no alcanzas. Díselo a tu jefe de área: lo que la gente
        busca y no encuentra es justamente lo que falta escribir.
      </p>
    </div>

    <div v-else-if="resultados.length" class="space-y-2">
      <p class="text-xs text-slate-400 uppercase tracking-wider font-semibold">
        {{ resultados.length }} resultado(s)
      </p>
      <RouterLink
        v-for="t in resultados" :key="t.id"
        :to="{ name: 'termino', params: { id: t.id } }"
        class="block rounded-xl bg-white oscuro:bg-slate-900 border border-slate-200
               oscuro:border-slate-800 p-4 hover:border-saai-400 hover:shadow-md transition">
        <div class="flex items-start gap-3">
          <i :class="t.acceso_restringido ? 'pi pi-lock text-amber-500' : 'pi pi-bookmark text-saai-500'"
             class="mt-1" />
          <div class="min-w-0 flex-1">
            <div class="flex items-baseline gap-2 flex-wrap">
              <h3 class="font-semibold">{{ t.nombre }}</h3>
              <span v-for="a in t.areas_detalle" :key="a.id"
                    class="text-[11px] px-1.5 py-0.5 rounded bg-slate-100 oscuro:bg-slate-800
                           text-slate-500">{{ a.nombre }}</span>
              <span v-if="t.es_transversal"
                    class="text-[11px] px-1.5 py-0.5 rounded bg-green-100 oscuro:bg-green-950
                           text-green-700 oscuro:text-green-400">todos</span>
            </div>
            <p class="text-sm text-slate-600 oscuro:text-slate-400 mt-1">
              {{ t.definicion }}
            </p>
            <p v-if="t.acceso_restringido"
               class="text-xs text-amber-700 oscuro:text-amber-400 mt-1.5">
              <i class="pi pi-lock text-[10px] mr-1" />{{ t.encargado?.mensaje }}
            </p>
          </div>
        </div>
      </RouterLink>
    </div>

    <p class="text-xs text-slate-400 text-center pt-4">
      Buscador provisional. El de verdad —con ranking, tolerancia a erratas y
      búsqueda dentro de los documentos— llega en la Fase 3.
    </p>
  </div>
</template>
