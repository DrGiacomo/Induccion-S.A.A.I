<script setup>
import { onMounted, ref, watch } from 'vue'
import api from '@/api/axios.js'

const props = defineProps({ id: { type: [String, Number], required: true } })

const termino = ref(null)
const cargando = ref(true)
const error = ref('')

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    const { data } = await api.get(`terminos/${props.id}/`)
    termino.value = data
  } catch (e) {
    error.value = e.response?.status === 404
      ? 'Este término no existe, o pertenece a un área que no alcanzas.'
      : e.mensaje
  } finally {
    cargando.value = false
  }
}

onMounted(cargar)
watch(() => props.id, cargar)
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <RouterLink :to="{ name: 'buscar' }"
                class="inline-flex items-center gap-1.5 text-sm text-slate-500
                       hover:text-slate-700 mb-4">
      <i class="pi pi-arrow-left text-xs" /> Volver a buscar
    </RouterLink>

    <div v-if="cargando" class="h-40 rounded-xl bg-slate-200/70 oscuro:bg-slate-800 animate-pulse" />

    <p v-else-if="error"
       class="rounded-xl bg-slate-100 oscuro:bg-slate-800 px-4 py-8 text-center text-slate-500">
      <i class="pi pi-lock text-2xl block mb-2" />{{ error }}
    </p>

    <article v-else-if="termino"
             class="rounded-2xl bg-white oscuro:bg-slate-900 border border-slate-200
                    oscuro:border-slate-800 overflow-hidden">

      <header class="p-6 border-b border-slate-100 oscuro:border-slate-800">
        <div class="flex items-center gap-2 flex-wrap mb-2">
          <span v-for="a in termino.areas_detalle" :key="a.id"
                class="text-[11px] px-2 py-0.5 rounded-full bg-saai-50 oscuro:bg-saai-950
                       text-saai-700 oscuro:text-saai-300 font-medium">{{ a.nombre }}</span>
          <span v-if="termino.es_transversal"
                class="text-[11px] px-2 py-0.5 rounded-full bg-green-100 oscuro:bg-green-950
                       text-green-700 oscuro:text-green-400 font-medium">
            Toda la empresa
          </span>
        </div>
        <h1 class="text-3xl font-bold tracking-tight">{{ termino.nombre }}</h1>

        <div v-if="termino.sinonimos?.length" class="mt-2 flex items-center gap-2 flex-wrap">
          <span class="text-xs text-slate-400">También:</span>
          <span v-for="s in termino.sinonimos" :key="s.id"
                class="text-xs px-2 py-0.5 rounded bg-slate-100 oscuro:bg-slate-800
                       text-slate-600 oscuro:text-slate-300">{{ s.texto }}</span>
        </div>
      </header>

      <div class="p-6 space-y-6">
        <p class="text-lg leading-relaxed">{{ termino.definicion }}</p>

        <!--
          El candado (P4). No es un vacío: dice de quién es y a quién pedirle
          acceso. Sin esta caja, el usuario vuelve a preguntarle a gente al
          azar, que es justo lo que el sistema vino a evitar.
        -->
        <div v-if="termino.acceso_restringido"
             class="rounded-xl bg-amber-50 oscuro:bg-amber-950/30 border border-amber-200
                    oscuro:border-amber-900 p-4">
          <div class="flex gap-3">
            <i class="pi pi-lock text-amber-600 mt-0.5" />
            <div class="text-sm">
              <p class="font-medium text-amber-900 oscuro:text-amber-200">
                Hay más, pero no es para tu área
              </p>
              <p class="text-amber-800 oscuro:text-amber-300 mt-1">
                {{ termino.encargado?.mensaje }}
              </p>
              <a v-if="termino.encargado?.email"
                 :href="`mailto:${termino.encargado.email}?subject=Acceso a «${termino.nombre}»`"
                 class="inline-flex items-center gap-1.5 mt-2 text-amber-900 oscuro:text-amber-200
                        font-medium hover:underline">
                <i class="pi pi-envelope text-xs" /> Escribirle
              </a>
            </div>
          </div>
        </div>

        <template v-else>
          <section v-if="termino.detalle">
            <h2 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Detalle
            </h2>
            <p class="leading-relaxed whitespace-pre-line">{{ termino.detalle }}</p>
          </section>

          <section v-if="termino.ejemplo">
            <h2 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Ejemplo de uso
            </h2>
            <p class="leading-relaxed italic text-slate-600 oscuro:text-slate-400
                      border-l-2 border-saai-300 pl-4">
              {{ termino.ejemplo }}
            </p>
          </section>

          <!-- P3: de dónde sale lo que se afirma -->
          <section v-if="termino.menciones?.length">
            <h2 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Dónde aparece
            </h2>
            <ul class="space-y-2">
              <li v-for="m in termino.menciones" :key="m.id"
                  class="text-sm rounded-lg bg-slate-50 oscuro:bg-slate-800 p-3">
                <span class="font-medium">{{ m.documento_nombre }}</span>
                <span v-if="m.ubicacion" class="text-slate-400"> · {{ m.ubicacion }}</span>
                <p v-if="m.fragmento" class="text-slate-600 oscuro:text-slate-400 mt-1 italic">
                  «{{ m.fragmento }}»
                </p>
              </li>
            </ul>
          </section>
        </template>
      </div>

      <!-- P3: quién lo aprobó y cuándo. Sin fuente, no se muestra. -->
      <footer class="px-6 py-3 bg-slate-50 oscuro:bg-slate-800/50 border-t
                     border-slate-100 oscuro:border-slate-800 text-xs text-slate-400">
        <span v-if="termino.creado_por_nombre">Cargado por {{ termino.creado_por_nombre }} · </span>
        Actualizado el {{ new Date(termino.actualizado_en).toLocaleDateString('es-CO') }}
      </footer>
    </article>
  </div>
</template>
