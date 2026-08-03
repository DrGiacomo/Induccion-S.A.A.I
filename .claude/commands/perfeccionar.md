Busca oportunidades de mejora REAL en el proyecto **Reqora**: gestor de requerimientos tipo Jira con IA. Stack: **NestJS 11 + TypeORM + PostgreSQL 17** (backend) y **Angular 21 + Tailwind 4 + Socket.io + GSAP** (frontend). Código en `reqora/backend/` y `reqora/frontend/`.

$ARGUMENTS

Si `$ARGUMENTS` nombra un área o ruta, enfoca ahí. Si está vacío, recorre las áreas de abajo.

**Dos direcciones.** Por defecto vas **de abajo hacia arriba**: escaneas el código que YA existe y propones mejoras. Si `$ARGUMENTS` empieza con **`idea`** seguido de una descripción (`/perfeccionar idea "notificaciones por WhatsApp"`), cambias a **`Modo idea`** (al final): vas **de arriba hacia abajo**, cuestionando la premisa de esa idea NUEVA antes de que nadie la construya. Un modo descubre qué mejorar; el otro valida si vale la pena algo que aún no existe.

**Norte (estrella polar):** Reqora = Jira (gestión) + Canva (creación) + Trello (flujo) + métricas + UX visible; el listón es "excelente". Cada propuesta debe **escalar hacia ese norte**, no ser una mejora suelta.

---

## Paso 0 — Contexto (obligatorio, evita proponer lo ya hecho)
Lee `docs/recorrido/PLAN-PASO-A-PASO.md` y los `docs/recorrido/bloque-*.md`. **No propongas nada que ya esté hecho o ya planeado como próximo paso** — eso es ruido. Si algo ya está en el PLAN pero sin hacer, puedes priorizarlo, pero dilo ("ya en PLAN, lo subiría de prioridad por X").

Estado a fecha: motor de 19 estados (F2), gating por rol (F4) y nota/evidencias por transición (F3) HECHOS; RAG léxico+semántico HECHO. Pendientes conocidos: contador de tiempo de desarrollo (T. Des), IA con contexto RAG (Casos #2/#3, requiere rotar keys), reportes con estados intermedios, seed, E2E. No los "descubras" como si fueran nuevos.

---

## Criterio (las 3 condiciones, todas a la vez)
1. Mejora **medible** en calidad de gestión, exactitud de datos, velocidad o UX (no cosmética).
2. **No sacrifica** funcionalidad ni rompe el contrato backend↔frontend.
3. **Implementable sin dependencias nuevas** (solo las de los `package.json`) y sin romper `synchronize:false` (esquema → SQL idempotente en `reqora/database/`).

## Áreas y archivos
- **Motor de estados y flujo del manual** — `common/workflow/issue-status.ts`, `issues/issues.service.ts`, `backlog/backlog.service.ts`. Coherencia del grafo, pantallas por fase (comité/QA/DevOps), contador T. Des + bloqueo con motivo, unificar `backlog` con el motor.
- **RAG (duplicados + semántico)** — `issues.service.ts` (`hybridSimilar`/`hybridScore`/`parseEmbedding`), `common/rag/embedding.service.ts`, `database/02-*.sql`/`03-*.sql`. Umbral, re-rank, "sin coincidencias" honesto, citar #issue, coste del embedding local, índices.
- **IA** — `ai/ai.service.ts`. Top-k similares en el prompt (Caso #2), validación anclada a `module_validation_rules` + manual (Caso #3), guardrails anti-alucinación, modelo (Gemini vs Claude) y caché de prompt. Ojo: rotar API keys antes de reconectar.
- **Reportes y KPIs** — `reports/reports.service.ts`, `features/metrics/`. Contar los estados intermedios nuevos; export PDF/Excel del flujo completo.
- **Tiempo real y notificaciones** — `notifications/*`, `mail/mail.service.ts`. Destinatario correcto por transición; timeline visual del `issue_history` (tabla + trigger ya existen).
- **Frontend y UX** — `features/issues/issue-detail/`, `features/sprint-board/`, `core/models/issue.model.ts`, `features/dashboard/`. Fluidez (señales/GSAP), feedback visible, coherencia con la paleta Reqora (azul foco + grafito + semáforo), estados de carga/error, accesibilidad. Modernizar el Dashboard viejo.
- **Datos e infraestructura** — soft-delete, índices para consultas calientes (workflow, RAG, KPIs), seed reproducible por rol/estado, `.env.example`, `users.email` sin UNIQUE.

## Por cada hallazgo
- **Hoy:** qué hace el código (con `archivo:línea`).
- **Propuesta:** el cambio, en una frase, y **por qué escala hacia el norte** (qué gana la gestión/UX/exactitud).
- **Antes → Después:** el efecto observable concreto.
- **Impacto:** alto/medio/bajo · **Esfuerzo:** alto/medio/bajo (aprox. archivos/líneas) · **Riesgo de romper algo:** alto/medio/bajo.

## Salida
Agrupa por área; dentro, ordena por relación impacto/esfuerzo (primero lo de más impacto y menos esfuerzo). Termina con **las 3 que haría primero** (con una línea de por qué) y **pregunta cuáles implementar antes de tocar código**. No implementes nada en este comando.

---

## Modo `idea` (validar una idea nueva antes de construirla)
Solo cuando `$ARGUMENTS` empieza con `idea`. Aquí NO escaneas el código en busca de mejoras: agarras la idea que trae el usuario y **cuestionas la premisa** al estilo "horas de oficina". Sigue produciendo cero código; el resultado es una **decisión**, no una implementación.

**1 · Contexto.** Igual que el Paso 0: lee `docs/recorrido/PLAN-PASO-A-PASO.md` y los `bloque-*.md`. Encaja la idea en el flujo real de Reqora (10 pasos, roles/permisos, comité, backlog). Si la idea ya está hecha o ya en el PLAN, dilo y no sigas como si fuera nueva.

**2 · Preguntas de diagnóstico (1–6).** Preguntas que **fuerzan evidencia concreta**, no hipótesis. Por ejemplo: ¿qué rol y en qué paso del flujo sufre hoy esto, y cuántas veces pasa? ¿qué hace ese usuario ahora sin la feature — es dolor o molestia? ¿cómo sabrás que funcionó (métrica observable)? ¿por qué ahora? Haz pocas y buenas; **espera respuestas** antes de seguir.

**3 · Cuestiona la premisa.** Valida el problema antes de diseñar la solución. Si la premisa no se sostiene, dilo sin suavizar y propón parar o reformular. No diseñes sobre un supuesto falso.

**4 · Alternativas.** Genera **2–3 enfoques distintos** (no variaciones del mismo), cada uno con: qué implica en el stack real (NestJS/Angular/Postgres), esfuerzo aprox., riesgo y qué se sacrifica. Respeta las 3 condiciones de arriba (medible · no rompe contrato · sin dependencias nuevas ni romper `synchronize:false`). Marca una recomendación y por qué **escala hacia el norte**.

**5 · Cierre.** Sintetiza: **premisa validada · alternativas · recomendación · siguiente paso concreto**. Preséntalo en el chat; si el usuario quiere conservarlo, guárdalo en `docs/diseno/{slug}.md`. **Pregunta cuál enfoque antes de tocar código.**

**Handoff:** este modo termina en decisión. Cuando el enfoque esté aprobado, la ejecución pasa a la skill **`sparc-methodology`** (Specification → Pseudocode → Architecture → Refinement → Completion). No empieces a codear desde aquí.
