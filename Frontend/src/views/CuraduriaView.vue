<script setup>
import { onMounted, ref } from 'vue'
import api from '@/api/axios.js'
import { useAuth } from '@/composables/useAuth.js'

/*
  Bandeja de curaduría.

  Hoy solo lista los borradores. En la Fase 4 esta pantalla se llena sola con
  lo que proponga la IA al ingerir documentos, y se convierte en el punto por
  el que pasa todo antes de ser visible — que es como P1 se cumple sin que
  nadie tenga que acordarse de cumplirlo.

  Las pantallas completas de carga y edición son `P2.4`. Mientras tanto, el
  panel de administración de Django ya permite hacer el trabajo entero.
*/

const { areaACargo, estado } = useAuth()

const borradores = ref([])
const cargando = ref(true)
const error = ref('')
const publicando = ref(null)

async function cargar() {
  cargando.value = true
  try {
    const { data } = await api.get('terminos/borradores/')
    borradores.value = data.results ?? data
  } catch (e) {
    error.value = e.mensaje
  } finally {
    cargando.value = false
  }
}

async function publicar(t) {
  publicando.value = t.id
  try {
    await api.post(`terminos/${t.id}/publicar/`)
    borradores.value = borradores.value.filter((b) => b.id !== t.id)
  } catch (e) {
    error.value = e.mensaje
  } finally {
    publicando.value = null
  }
}

onMounted(cargar)
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <header>
      <h1 class="text-2xl font-bold tracking-tight">Curaduría</h1>
      <p class="text-slate-500 oscuro:text-slate-400 mt-1">
        <template v-if="areaACargo">
          Lo que espera tu aprobación en <b>{{ areaACargo.nombre }}</b>.
        </template>
        <template v-else-if="estado.esAdmin">
          Todo lo que está en borrador, de cualquier área.
        </template>
      </p>
    </header>

    <div class="rounded-xl bg-saai-50 oscuro:bg-saai-950/40 border border-saai-200
                oscuro:border-saai-900 p-4 text-sm">
      <i class="pi pi-info-circle text-saai-600 mr-1.5" />
      <span class="text-saai-900 oscuro:text-saai-200">
        Nada llega a los demás sin pasar por aquí. Para crear y editar con todos
        los campos, usa
        <a href="http://localhost:8000/admin/contenido/termino/" target="_blank"
           rel="noopener" class="underline font-medium">el panel de administración</a>
        — las pantallas completas llegan en la Fase 2.
      </span>
    </div>

    <div v-if="cargando" class="space-y-2">
      <div v-for="i in 3" :key="i"
           class="h-20 rounded-xl bg-slate-200/70 oscuro:bg-slate-800 animate-pulse" />
    </div>

    <p v-else-if="error" class="text-sm text-red-600">{{ error }}</p>

    <div v-else-if="!borradores.length"
         class="rounded-xl bg-white oscuro:bg-slate-900 border border-slate-200
                oscuro:border-slate-800 p-8 text-center">
      <i class="pi pi-check-circle text-4xl text-green-400" />
      <h2 class="mt-3 font-semibold">No hay nada pendiente</h2>
      <p class="text-sm text-slate-500 mt-1.5">
        Todo lo de tu área está publicado o archivado.
      </p>
    </div>

    <div v-else class="space-y-2">
      <article
        v-for="t in borradores" :key="t.id"
        class="rounded-xl bg-white oscuro:bg-slate-900 border border-amber-200
               oscuro:border-amber-900/50 p-4 flex items-start gap-4">
        <i class="pi pi-pencil text-amber-500 mt-1" />
        <div class="min-w-0 flex-1">
          <h3 class="font-semibold">{{ t.nombre }}</h3>
          <p class="text-sm text-slate-600 oscuro:text-slate-400 mt-0.5">{{ t.definicion }}</p>
          <div class="flex gap-1.5 mt-2 flex-wrap">
            <span v-for="a in t.areas_detalle" :key="a.id"
                  class="text-[11px] px-1.5 py-0.5 rounded bg-slate-100 oscuro:bg-slate-800
                         text-slate-500">{{ a.nombre }}</span>
          </div>
        </div>
        <div class="flex gap-2 shrink-0">
          <RouterLink :to="{ name: 'termino', params: { id: t.id } }"
                      class="px-3 py-1.5 rounded-lg text-sm border border-slate-200
                             oscuro:border-slate-700 hover:bg-slate-50 oscuro:hover:bg-slate-800">
            Ver
          </RouterLink>
          <button :disabled="publicando === t.id"
                  class="px-3 py-1.5 rounded-lg text-sm bg-saai-600 hover:bg-saai-700
                         text-white font-medium disabled:opacity-50"
                  @click="publicar(t)">
            <i v-if="publicando === t.id" class="pi pi-spin pi-spinner mr-1 text-xs" />
            Publicar
          </button>
        </div>
      </article>
    </div>
  </div>
</template>
