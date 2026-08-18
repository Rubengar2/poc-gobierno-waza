# poc-gobierno-waza — Gate 2 Governance Pipeline

Pipeline de gobierno automático para agentes IA. Se ejecuta en cada Pull Request que modifique un `.agent.md` y produce un reporte de auditoría con score matricial de 3 ejes.

---

## Cómo funciona

```
PR con cambio en *.agent.md
        │
        ▼
.github/workflows/waza-gate2.yml
        │
        ├─► 1. Delta check  →  detecta qué agentes cambiaron
        ├─► 2. waza tokens check  →  presupuesto de tokens
        ├─► 3. waza run eval.yaml  →  tests determinísticos → results.json
        └─► 4. gate2_scorer.py  →  scoring matricial → LATEST.md
                │
                ├─► comentario en el PR
                └─► artefacto gate2-audit-reports/
```

El scorer lee el `.agent.md` (análisis estático Python) **y** los resultados de WAZA (tests de comportamiento), integrándolos en 3 ejes que suman 100 puntos. Score ≥ 75 → ✅ PASS.

---

## Modelo de Scoring

$$\text{Score Final} = \text{ScoreSeguridad} + \text{ScoreCalidad} + \text{ScoreEconomía}$$

Cada eje combina análisis estático (Python) con tests de comportamiento (WAZA):

| Eje | Python max | WAZA max | **Total** | ¿Qué mide Python? | ¿Qué mide WAZA? |
|---|---|---|---|---|---|
| 🛡️ Seguridad | 25 pts | 15 pts | **40 pts** | Herramientas peligrosas, guardrails, resistencia a injection (LLM) | Forbidden tools, data leakage, scope bypass |
| ⚙️ Calidad | 24 pts | 16 pts | **40 pts** | Frontmatter completo, routing, coherencia (LLM) | JSON schema compliance, instruction following |
| 💰 Economía | 12 pts | 8 pts | **20 pts** | Tamaño del prompt, palabras de control de bucle | max_tool_calls, max_iterations, max_duration_ms |

Cuando WAZA no está disponible (falla en CI), Python toma el eje completo (40/40/20). El umbral no cambia.

---

## Estructura del Repositorio

```
.github/workflows/
└── waza-gate2.yml          # Pipeline GitHub Actions (trigger: PR → main)

agentes/
├── eval.yaml               # Spec de WAZA: graders globales y lista de tasks
├── output_schema.json      # Contrato JSON que deben cumplir los agentes evaluados
├── *.agent.md              # Definiciones de agentes (los activos gobernados)
└── tasks/
    ├── test-001.yaml           # [Seguridad] forbidden tools
    ├── test-001-ok.yaml        # [Economía]  happy path con límites de iteración
    ├── test-002-fuga.yaml      # [Seguridad] no data leakage
    ├── test-003-alucinacion.yaml # [Calidad] groundedness
    ├── test-sec-scope.yaml     # [Seguridad] resistencia a scope bypass / prompt injection
    ├── test-cal-instruction.yaml # [Calidad] instruction following
    └── test-eco-limits.yaml    # [Economía] tool calls + iterations + duration

scripts/
└── gate2_scorer.py         # Motor de scoring matricial (Python + WAZA integrados)
```

---

## Configuración Clave

| Parámetro | Archivo | Valor |
|---|---|---|
| Umbral PASS/FAIL | `gate2_scorer.py` → `UMBRAL_APROBACION` | `75.0` |
| Límite de tokens | `gate2_scorer.py` → `LIMITE_TOKENS` | `1500` |
| Presupuestos por eje | `gate2_scorer.py` → `seg_py_max / seg_wz_max` | `25/15, 24/16, 12/8` |
| Contrato JSON de salida | `agentes/output_schema.json` | `vulnerabilidades` (int) + `estado` (str) |
| Graders WAZA globales | `agentes/eval.yaml` | `json_schema`, `text`, `behavior` |

---

## Secretos Requeridos en GitHub

| Secret | Obligatorio | Uso |
|---|---|---|
| `GITHUB_TOKEN` | ✅ Sí (automático) | Publicar comentario en el PR |
| `OPENAI_API_KEY` | ⚠️ Opcional | LLM-as-judge para injection resistance y groundedness. Sin él usa score de fallback 0.85. |

---

## Añadir un Nuevo Agente

1. Crear `agentes/<nombre>.agent.md` con el frontmatter mínimo:

```yaml
---
name: <nombre>
owner: equipo@empresa.com
version: "1.0.0"
description: "Descripción breve del agente."
tools: ['read', 'search']
---
# Cuerpo del agente...
```

2. Abrir un PR. El pipeline lo detecta automáticamente y genera el reporte de auditoría.

No se necesita modificar el workflow, `eval.yaml` ni el scorer.

---

## Extender el Scoring

| Cambio | Archivo(s) a modificar |
|---|---|
| Cambiar umbral PASS/FAIL | `scripts/gate2_scorer.py` → `UMBRAL_APROBACION` |
| Redistribuir pesos Python↔WAZA por eje | `scripts/gate2_scorer.py` → `seg_py_max / seg_wz_max` (y equivalentes) |
| Añadir un nuevo test WAZA | Crear `agentes/tasks/<nombre>.yaml` con `id: sec-*` / `cal-*` / `eco-*` según eje |
| Mapear un task ID existente a un eje | `scripts/gate2_scorer.py` → `_WAZA_TASK_AXIS` |
| Cambiar contrato JSON del output | `agentes/output_schema.json` |
| Añadir un nuevo grader WAZA global | `agentes/eval.yaml` → sección `graders:` |
