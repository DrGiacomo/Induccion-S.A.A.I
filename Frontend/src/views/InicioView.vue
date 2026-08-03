<script setup>
import { onMounted, ref } from 'vue'
import api from '@/api/axios.js'
import { useAuth } from '@/composables/useAuth.js'

const { nombre, estado } = useAuth()

const cargando = ref(true)
const error = ref('')
const induccion = ref({ cargo: null, terminos: [], documentos: [], mensaje: '' })

/*
  Esta pantalla es la inducción, y no existe ningún módulo que la construya.

  Sale de una sola relación: la persona tiene un cargo, y el cargo tiene
  términos y documentos enganchados. El sistema deduce el resto. Por eso
  S.A.A.I no necesita ser una plataforma de cursos y aun así cubre lo que
  una haría aquí.
*/
onMounted(async () => {
  try {
    const { data } = await api.get('cargos/mi_induccion/')
    induccion.value = data
  } catch (e) {
    error.value = e.mensaje
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">

    <header>
      <h1 class="text-2xl font-bold tracking-tight">
        Hola, {{ nombre.split(' ')[0] }}
      </h1>
      <p class="text-slate-500 oscuro:text-slate-400 mt-1">
        <template v-if="induccion.cargo">
          Esto es lo que conviene que conozcas como
          <b class="text-slate-700 oscuro:text-slate-200">{{ induccion.cargo.nombre }}</b>.
        </template>
        <template v-else>Bienvenido a S.A.A.I.</template>
      </p>
    </header>

    <div v-if="cargando" class="grid gap-3 sm:grid-cols-2">
      <div v-for="i in 4" :key="i"
           class="h-24 rounded-xl bg-slate-200/70 oscuro:bg-slate-800 animate-pulse" />
    </div>

    <p v-else-if="error"
       class="rounded-xl bg-red-50 oscuro:bg-red-950/40 border border-red-200
              oscuro:border-red-900 px-4 py-3 text-sm text-red-700 oscuro:text-red-300">
      <i class="pi pi-exclamation-triangle mr-1.5" />{{ error }}
    </p>

    <!-- Sin cargo: se dice claramente qué falta y a quién pedírselo (P2, P4) -->
    <div v-else-if="!induccion.cargo"
         class="rounded-xl bg-white oscuro:bg-slate-900 border border-slate-200
                oscuro:border-slate-800 p-8 text-center">
      <i class="pi pi-id-card text-4xl text-slate-300 oscuro:text-slate-600" />
      <h2 class="mt-3 font-semibold">Todavía no tienes un cargo asignado</h2>
      <p class="text-sm text-slate-500 oscuro:text-slate-400 mt-1.5 max-w-md mx-auto">
        {{ induccion.mensaje }}
        Mientras tanto puedes usar el buscador para consultar lo que esté a tu alcance.
      </p>
      <RouterLink :to="{ name: 'buscar' }"
                  class="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-lg
                         bg-saai-600 hover:bg-saai-700 text-white text-sm font-medium">
        <i class="pi pi-search" /> Ir al buscador
      </RouterLink>
    </div>

    <template v-else>
      <!-- ── Términos: píldoras ──────────────────────────────── -->
      <section>
        <h2 class="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3">
          Vocabulario · {{ induccion.terminos.length }}
        </h2>
        <p v-if="!induccion.terminos.length" class="text-sm text-slate-400 italic">
          Tu jefe de área todavía no ha enganchado términos a este cargo.
        </p>
        <div v-else class="flex flex-wrap gap-2">
          <RouterLink
            v-for="t in induccion.terminos" :key="t.id"
            :to="{ name: 'termino', params: { id: t.id } }"
            class="group inline-flex items-center gap-2 pl-3 pr-3.5 py-2 rounded-full
                   border text-sm transition
                   bg-white oscuro:bg-slate-900 border-slate-200 oscuro:border-slate-700
                   hover:border-saai-400 hover:shadow-sm">
            <i v-if="t.acceso_restringido" class="pi pi-lock text-xs text-amber-500" />
            <i v-else class="pi pi-bookmark text-xs text-saai-500" />
            <span class="font-medium">{{ t.nombre }}</span>
            <span v-if="t.es_transversal"
                  class="text-[10px] uppercase tracking-wide text-green-600
                         oscuro:text-green-400">todos</span>
          </RouterLink>
        </div>
      </section>

      <!-- ── Documentos: tarjetas ────────────────────────────── -->
      <section>
        <h2 class="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3">
          Documentos · {{ induccion.documentos.length }}
        </h2>
        <p v-if="!induccion.documentos.length" class="text-sm text-slate-400 italic">
          Todavía no hay documentos para este cargo.
        </p>
        <div v-else class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <article
            v-for="d in induccion.documentos" :key="d.id"
            class="rounded-xl bg-white oscuro:bg-slate-900 border border-slate-200
                   oscuro:border-slate-800 p-4 hover:shadow-md transition">
            <div class="flex items-start gap-3">
              <div class="w-9 h-9 shrink-0 rounded-lg grid place-items-center"
                   :class="d.acceso_restringido
                            ? 'bg-amber-100 oscuro:bg-amber-950/50 text-amber-600'
                            : 'bg-saai-50 oscuro:bg-saai-950 text-saai-600'">
                <i :class="d.acceso_restringido ? 'pi pi-lock' : 'pi pi-file'" />
              </div>
              <div class="min-w-0">
                <h3 class="font-medium text-sm truncate">{{ d.nombre }}</h3>
                <p class="text-xs text-slate-500 mt-0.5 line-clamp-2">
                  {{ d.descripcion || 'Sin descripción' }}
                </p>
              </div>
            </div>

            <!-- El candado de P4: no un vacío mudo, sino a quién pedirle acceso -->
            <p v-if="d.acceso_restringido"
               class="mt-3 text-xs text-amber-700 oscuro:text-amber-300 bg-amber-50
                      oscuro:bg-amber-950/30 rounded-lg px-2.5 py-2">
              {{ d.encargado?.mensaje }}
            </p>
            <a v-else-if="d.archivo" :href="d.archivo" target="_blank" rel="noopener"
               class="mt-3 inline-flex items-center gap-1.5 text-xs font-medium
                      text-saai-600 hover:text-saai-700">
              <i class="pi pi-download text-[10px]" /> Abrir · {{ d.tamano_legible }}
            </a>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>
