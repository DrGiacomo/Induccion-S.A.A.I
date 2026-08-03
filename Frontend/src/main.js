import './assets/main.css'

import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'

import App from './App.vue'
import router from './router/index.js'

const app = createApp(App)

/*
  PrimeVue montado encima de Tailwind.

  `darkModeSelector: '.oscuro'` engancha su modo oscuro a la misma clase que
  usa Tailwind, para que no haya dos sistemas de tema peleándose.

  El reparto es: PrimeVue pone lo aburrido y difícil —selectores con
  búsqueda, subida de archivos con barra de progreso, accesibilidad de
  teclado— y Tailwind pone el aspecto. Así no hay que reescribir un
  desplegable desde cero, pero tampoco acaba pareciendo la web de
  demostración de una librería (decisión D8).

  ⚠️ **Fijado en PrimeVue 4.x, y no es un descuido.** A partir de la 5,
  PrimeVue y PrimeIcons dejaron de ser MIT y pasaron a licencia comercial:
  la versión gratuita exige que la organización tenga menos de 10 empleados
  y menos de un millón de dólares de ingresos, con clave de licencia y
  renovación anual. Sin clave, la aplicación pinta un aviso rojo encima.

  S.A.A.I está pensado para instalarse EN EMPRESAS, así que la 5 le pondría
  una factura —o un aviso rojo— a cada instalación. La 4.5.4 es MIT y hace
  lo mismo. **No subir de versión sin volver a leer la licencia.**
*/
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      darkModeSelector: '.oscuro',
      cssLayer: { name: 'primevue', order: 'theme, base, primevue' },
    },
  },
  locale: {
    accept: 'Sí',
    reject: 'No',
    choose: 'Elegir',
    upload: 'Subir',
    cancel: 'Cancelar',
    emptySearchMessage: 'No se encontraron resultados',
    emptyMessage: 'No hay opciones',
  },
})

app.use(router)
app.mount('#app')
