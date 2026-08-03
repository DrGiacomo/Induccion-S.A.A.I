import { ref, watch } from 'vue'

/*
  Modo claro / oscuro.

  Se decide ahora y no después porque cuesta casi nada al empezar y bastante
  cuando ya hay treinta pantallas escritas: habría que revisarlas todas.

  Arranca respetando lo que prefiera el sistema, pero en cuanto el usuario
  elige, manda su elección y se recuerda.
*/

const CLAVE = 'saai:tema'

function preferenciaDelSistema() {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'oscuro' : 'claro'
}

const tema = ref(localStorage.getItem(CLAVE) || preferenciaDelSistema())

function aplicar(valor) {
  document.documentElement.classList.toggle('oscuro', valor === 'oscuro')
}

aplicar(tema.value)
watch(tema, (valor) => {
  aplicar(valor)
  localStorage.setItem(CLAVE, valor)
})

export function useTema() {
  return {
    tema,
    esOscuro: () => tema.value === 'oscuro',
    alternar: () => {
      tema.value = tema.value === 'oscuro' ? 'claro' : 'oscuro'
    },
  }
}
