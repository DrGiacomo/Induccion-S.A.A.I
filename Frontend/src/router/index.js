import { createRouter, createWebHistory } from 'vue-router'
import RolesView from '../views/RolesView.vue'
import tipoDeIdView from '../views/tipoDeIdView.vue'
import perfilView from '../views/perfilView.vue'
import areaView from '../views/areaView.vue'
import userareaView from '../views/userareaView.vue'
import userrolView from '../views/userrolView.vue'
import repoView from '../views/repoView.vue'


const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/roles', component: RolesView },
    { path: '/tipos-id', component: tipoDeIdView },
    { path: '/perfiles', component: perfilView },
    { path: '/areas', component: areaView },
    { path: '/userareas', component: userareaView },
    { path: '/userrol', component: userrolView },
    { path: '/repos', component: repoView },
  ]
})

export default router