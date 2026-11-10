<div align="center">

<img src="image/logopage02.png" alt="Logotipo de Baize 白澤" width="320" />

# Sinan (Sinan-Agent-Team)

**Sistema multiagente de formulación de estrategias**

Doble juego · Aislamiento de contexto · Base de conocimiento compartida · Validación estricta de JSON Schema · Rotación multi-Provider y multi-Key

<p align="center">

  <a href="https://github.com/Xu123-Bob/Sinan-Agent-Team/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Xu123-Bob/Sinan-Agent-Team?style=flat-square" alt="License">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  </a>
</p>

<p align="center">
  <a href="README.cn.md">简体中文</a> |
  <a href="README.en.md">English</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.es.md">Español</a> |
  <a href="README.fr.md">Français</a> |
  <a href="README.ru.md">Русский язык</a> |
</p>

</div>

----------
## Descripción general
**Este proyecto es un marco de formulación de estrategias y evaluación de efectos de estrategias multiagente**
- El producto construye conjuntamente un sistema de formulación y evaluación de estrategias mediante **Rule\Rubric\LLM-to-judge**
- Este proyecto cuenta con **6 agentes** en total: 2 agentes de generación de preguntas, 2 agentes de dictamen, 1 agente de reconocimiento y 1 agente de juicio
- La capa Rule incluye restricciones sobre el contenido del negocio y también restricciones sobre la **estructura de salida de los agentes** (para garantizar que los agentes generen salidas correctas)
- El Rubric se elabora mediante el **juego de 2 agentes de generación de preguntas**, cada uno expone sus puntos de vista, y finalmente el **agente de dictamen realiza la confirmación final**
- La formulación y evaluación de estrategias se realiza mediante la **discusión de 2 agentes de formulación de estrategias**, y finalmente el **agente de dictamen también realiza la confirmación final**
- El escaneo y la obtención de datos y conocimiento profesional los realiza **1 agente de reconocimiento**, que escanea principalmente `knowledge/`, `data/`, `output/`
- Los productos generados incluyen: **plan de estrategia, tabla de preguntas Rubric y manuscrito de discusión**, que se guardan finalmente en `knowledge/`. Al iterar nuevas estrategias, el **agente de reconocimiento escanea automáticamente**
- Este proyecto es mi obra participante en el Hackathon de Jóvenes de IA de Pekín 2026, obtuvo el 4.º puesto en la calificación de Alipay y fue recomendado al Concurso de Agentes Inteligentes de Alipay

### Diagrama de estructura multiagente

<div align="center">
Diagrama de estructura multiagente
</div>

<p align="center">
  <img src="image/infra.png" alt="Diagrama de estructura multiagente" width="800" />
</p>

### Presentación del producto  
Dirección web estática: https://sinan-website.pages.dev/

---

## Características principales

- **Arquitectura de 6 agentes**: Reconocimiento / Grupo de generación de preguntas (A+B) / Grupo de estrategia (A+B) / Juicio, cada uno con sus funciones |
- **Aislamiento estricto de contexto**: Grupo de generación de preguntas ↔ Grupo de estrategia completamente aislados; la memoria privada del Judge nunca se filtra |
- **Base de conocimiento compartida de solo lectura**: `knowledge/` es legible por todos los agentes, pero ningún agente puede escribir en ella |
- **Doble juego de tres rondas**: Grupo Rubric A ⇄ B, grupo de estrategia A ⇄ B, cada uno con tres rondas de juego |
- **Dictamen independiente del Judge**: El único agente que puede ver todo el contexto, solo emite productos de decisión |
- **Validación estricta de JSON Schema**: La salida de cada agente debe pasar por Pydantic; en caso de fallo, se reintenta automáticamente 2 veces |
- **Doble validación de reglas duras antes y después**: Se inyecta en el Prompt antes de la generación y se revisa de forma independiente después de la generación; el usuario puede personalizar la línea base |
- **Multi-Provider y multi-Key**: El mismo Provider admite rotación de múltiples Keys; cada agente puede especificar un modelo de forma independiente |
- **Entrada de cualquier ruta**: Relativa / absoluta / Windows / Linux / archivo único / carpeta; Enter para escanear automáticamente |
- **Cualquier dominio de negocio**: E-commerce / GitHub / AtomGit / Douyin / TikTok integrados; ampliable y personalizable |
- **CLI totalmente en chino**: Renderizado con Typer + Rich, paneles en color, impresión en tiempo real del proceso de debate |

---
## Interfaz de inicio de sesión
<div align="center">
Interfaz de inicio de sesión
</div>

<p align="center">
  <img src="image/sinancli-01.jpg" alt="Interfaz de inicio de sesión" width="800" />
</p>


## Requisitos del entorno (leer primero)
```
| Elemento | Recomendado | Descripción |
|---|---|---|
| **Python** | **3.10 / 3.11 / 3.12** | ⭐ Muy recomendado |
| Python 3.13 | Disponible | Algunas dependencias pueden tener pequeños problemas |
| Python 3.14+ | ❌ **No recomendado** | Problemas de compatibilidad conocidos con editable install |
| Sistema operativo | Windows / macOS / Linux | Soporte multiplataforma |
| Red | Requiere acceso a la API del LLM | DeepSeek / Kimi / Qwen, etc. |
```
> **Si encuentra algún problema de instalación o inicio, ejecute primero el diagnóstico**:
> ```bash
> python -m agent.doctor
> ```
> Verificará de una vez la versión de Python, las dependencias, la integridad del paquete agent, el método de instalación y la prueba de inicio, y le dará sugerencias de reparación.

---

## Instalación (elija 1 de 3 métodos)

### Método 1: Script de un clic (recomendado para principiantes)

```bash
# Windows
scripts\install.bat

# Linux / macOS
bash scripts/install.sh
```

El script verificará automáticamente Python, creará el venv, instalará las dependencias y ejecutará doctor para validar.

### Método 2: Instalación manual (para desarrolladores familiarizados con Python)

```bash
# Se recomienda encarecidamente usar un entorno virtual
python -m venv .venv

# Activar (elija 1 de 3)
source .venv/bin/activate         # Linux / macOS
.venv\Scripts\activate            # Windows CMD
.venv\Scripts\Activate.ps1        # Windows PowerShell

# Instalar
pip install -e .
```

> **Aviso para usuarios de Python 3.13+**: Si después de `pip install -e .` el comando `sinan` reporta `ModuleNotFoundError: agent.core.xxx`, cambie a:
> ```bash
> pip install .
> ```
> O inicie directamente con `python -m agent` (consulte la sección «Inicio» más abajo).

### Método 3: Docker (para evitar complicaciones de entorno)

```bash
docker build -t sinan .

docker run -it --rm \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/knowledge:/app/knowledge \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  sinan
```

Evita por completo los problemas de versión de Python, compilación de dependencias y diferencias del sistema.

---

## Inicio (3 formas equivalentes)

```bash
sinan                  # Comando instalado por pip (el más cómodo)
python -m agent        # Alternativa (usar cuando el comando sinan falle)
python -m agent.cli    # Alternativa adicional
```

**Los tres comandos son completamente equivalentes**; basta con que funcione cualquiera de ellos.

Si `sinan` reporta un error, cambie directamente a `python -m agent`; **no es necesario investigar el problema**.

---

## Inicio rápido

### 1. Configurar el backend

```bash
cp .env.example .env
```

Edite `.env` e introduzca **al menos una** API Key (configuración mínima):

```env
SINAN_DEEPSEEK_API_KEY=sk-tu-clave
SINAN_DEFAULT_PROVIDER=deepseek
```

Elimine todos los demás campos; basta con estas dos líneas.

> Para configuraciones avanzadas de múltiples modelos, pools de múltiples Keys y asignación por agente, consulte [`USAGE.md`](USAGE.md).

### 2. Preparar la base de conocimiento (opcional)

```bash
mkdir -p knowledge
echo "# Normas de lenguaje corporativo\nEvitar expresiones absolutas..." > knowledge/company_style.md
```

Se cargará automáticamente al iniciar y estará disponible como referencia para todos los agentes, pero ningún agente **puede escribir en ella**.

### 3. Verificar la configuración

```bash
python -c "from agent.core.agent_config import summarize_configs; print(summarize_configs())"
```

Debería ver el estado de Provider y Key de los 6 agentes todos en ✅.

### 4. Ejecutar

```bash
sinan
# o
python -m agent
```

O generar directamente desde la línea de comandos:

```bash
sinan generate ./data/ecommerce_v1 -d ecommerce
# o
python -m agent generate ./data/ecommerce_v1 -d ecommerce
```

### 5. Ver los productos

```bash
ls outputs/
# strategy_<domain>_<folder>_<ts>.md   ← Estrategia final
# rubric_<domain>_<folder>_<ts>.json   ← Rubric final
# debate_<domain>_<folder>_<ts>.json   ← Registro completo del debate
```

### 6. Los 6 agentes
```
| Icono | Agente | Responsabilidad | Configuración de modelo independiente |
|------|-------|------|----------------|
| 🔍 | `SCOUT` | Reconocimiento de archivos, identificación del contenido de datos | ✅ |
| 🧩 | `RUBRIC_A` | Editor principal de preguntas (borrador del Rubric) | ✅ |
| 🧩 | `RUBRIC_B` | Revisor de preguntas (revisión del Rubric) | ✅ |
| 🎯 | `STRATEGY_A` | Redactor de estrategias | ✅ |
| 🎯 | `STRATEGY_B` | Refutador de estrategias | ✅ |
| ⚖️ | `JUDGE` | Agente de juicio (dictamen final + puntuación) | ✅ |
```

---

## Comandos CLI

```bash
# Chat interactivo (recomendado para principiantes)
sinan

# Generación de un clic
sinan generate <cualquier ruta> -d <dominio> [-o directorio de salida] [-k directorio de base de conocimiento]

# Evolución iterativa (V1 → V2)
sinan evolve <estrategia_antigua.md> <nueva_ruta_de_datos> -d <dominio>

# Comparar dos estrategias
sinan compare <estrategiaA.md> <estrategiaB.md> -d <dominio>

# Diagnóstico del entorno
python -m agent.doctor
```

> Si el comando `sinan` no está disponible, reemplace todo por `python -m agent <subcomando>`.

### Dominios compatibles

Dominios predeterminados del sistema: `ecommerce` · `github` · `atomgit` · `douyin` · `tiktok` · `finance`

> El usuario puede añadir datos y objetivos de tarea relacionados en la carpeta `data/`.

> El usuario puede personalizar nuevas reglas de dominio en `configs/rules.yaml`.

### Rutas compatibles

- ✅ Ruta relativa (`./data/foo`)
- ✅ Ruta absoluta (`/home/user/foo`, `D:\data\foo`)
- ✅ Archivo único (`./goal.md`)
- ✅ Carpeta completa (cualquier ubicación)
- ✅ Enter directamente → escaneo inteligente del directorio actual

---

## Base de conocimiento

`knowledge/` es una **base de conocimiento compartida de solo lectura**, disponible como referencia para los 6 agentes inteligentes.

### Características
- **Lectura compartida**: Todos los agentes leen el contenido de la base de conocimiento como referencia antes de generar
- **Sin escritura**: La capa de código `safe_io.safe_write` lo bloquea obligatoriamente |
- **Refuerzo físico**: Se recomienda ejecutar `chmod -R a-w knowledge/` (Linux/macOS) |
- **No rompe el aislamiento**: La base de conocimiento es una referencia pública estática, completamente ajena al historial de juego |
- **Tamaño controlable**: Truncado a 8k caracteres por archivo y 20k caracteres en total, ajustable mediante `.env` |
- **Multi-formato**: md / txt / docx / xlsx / csv / pptx / yaml / json |

### Contenido adecuado

- Marca corporativa / normas de lenguaje
- Estándares del sector / líneas rojas políticas
- SOP internos / documentos de procesos
- Plantillas de estrategia reutilizables
- Casos de éxito históricos (anonimizados)
- Conocimiento financiero

### Contenido no adecuado

- Claves secretas / contraseñas en texto plano
- Datos privados de clientes
- Binarios grandes (imágenes/vídeos)

---

## Configuración

### Configuración por capas (recomendada)

Cada agente puede especificar modelo y key de forma independiente:

```env
SINAN_DEFAULT_PROVIDER=kimi/deepseek/GLM/Qwen

SINAN_RUBRIC_A_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_RUBRIC_B_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_STRATEGY_A_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_STRATEGY_B_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_JUDGE_PROVIDER=kimi/deepseek/GLM/Qwen
```

### Pool de múltiples Keys (límite de velocidad / múltiples cuentas)

```env
# Separadas por comas
SINAN_DEEPSEEK_API_KEYS=sk-1,sk-2,sk-3

# O numeradas por línea
SINAN_DEEPSEEK_API_KEY_1=sk-1
SINAN_DEEPSEEK_API_KEY_2=sk-2
SINAN_DEEPSEEK_API_KEY_3=sk-3
```

El banner de inicio mostrará `✅ x3 rotación`, y todas las llamadas se distribuirán automáticamente mediante round-robin.

### Nombre de la variable de key de cada Provider
- DeepSeek: `SINAN_DEEPSEEK_API_KEY`
- Kimi / Moonshot: `SINAN_MOONSHOT_API_KEY`
- Qwen / Tongyi Qianwen: `SINAN_DASHSCOPE_API_KEY`
- GLM / Zhipu: `SINAN_ZHIPUAI_API_KEY`
- Ollama local: no requiere key

### Personalización de reglas duras

Edite `configs/rules.yaml`:

```yaml
global:
  rules:
    - name: "Prohibido el lenguaje absoluto"
      type: "forbidden"
      value: "mejor|primero|absoluto"
      score: 20
      description: "La estrategia no debe contener expresiones absolutas"

healthcare:
  rules:
    - name: "No incluir nombres comerciales de medicamentos con receta"
      type: "forbidden"
      value: "aspirina|ibuprofeno"
      score: 20
```

Tipos de reglas compatibles: `keyword` / `forbidden` / `regex` / `min_length` / `schema_field`.

---

## Puntos clave de la arquitectura

### Garantía de aislamiento de contexto
```
| Agente | Ver juego Rubric | Ver juego Strategy | Ver memoria del Judge | Ver base de conocimiento | Escribir base de conocimiento |
|---|:---:|:---:|:---:|:---:|:---:|
| 🔍 ScoutAgent | ✗ | ✗ | ✗ | ✓ | ✗ |
| 🧩 RubricAgentA / B | ✓ (solo su grupo) | ✗ | ✗ | ✓ | ✗ |
| 🎯 StrategyAgentA / B | ✗ (solo recibe final_rubric) | ✓ (solo su grupo) | ✗ | ✓ | ✗ |
| ⚖️ JudgeAgent | ✓ | ✓ | ✓ (propia privada) | ✓ | ✗ |
```
### Validación estricta del Schema de salida
```
| Agente | Schema de salida |
|---|---|
| Scout | `ScoutReport` |
| RubricA / B | `RubricSchema` |
| StrategyA / B | `StrategySchema` |
| Judge | `RubricDecision` / `StrategyDecision` |
```
En caso de fallo, el mensaje de error se devuelve automáticamente al LLM para que se autocorrija, con un máximo de 2 reintentos.

### Defensa en tres capas de reglas duras

```
Antes de generar: rule_constraints se inyecta en el Prompt → el agente lo cumple activamente
Después de generar: RuleEngine.evaluate(final_strategy) → revisión y puntuación independientes
Al escribir: safe_io.safe_write → bloquea la escritura en la base de conocimiento
```

---

## Solución de problemas

### Diagnóstico de un clic (ejecutar primero)

```bash
python -m agent.doctor
```

Verifica:
- Versión de Python
- Dependencias de terceros
- Integridad del paquete agent (24 módulos)
- Método de instalación (editable / normal / directorio fuente)
- Prueba de inicio

Y proporciona **comandos de reparación concretos** para los problemas.

### Consulta rápida de problemas comunes

#### `sinan` reporta `ModuleNotFoundError: No module named 'agent.core.xxx'`

**Causa**: En Python 3.13+ el mapeo del finder de editable install es incompleto.

**Solución (elija 1 de 3)**:

```bash
# Opción A: cambiar a instalación normal
pip uninstall -y sinan-agent
pip install .

# Opción B: usar directamente el método de inicio alternativo
python -m agent

# Opción C: crear un wrapper sinan.cmd en Windows
# Ver TROUBLESHOOTING.md
```

#### No se encuentra el comando `sinan`

```bash
# Usar inicio alternativo
python -m agent
```

O añada `Scripts\` de Python a la variable de entorno PATH.

#### Las dependencias no se instalan / se quedan colgadas

**Causa**: La versión de Python es demasiado nueva y algunos paquetes aún no se han adaptado.

**Solución**:
1. Cambiar a Python 3.12
2. O usar Docker: `docker build -t sinan . && docker run -it sinan`

#### `⚠ Los siguientes agentes no tienen API Key`

**Causa**: El nombre de la variable de key del provider correspondiente en `.env` está mal escrito.

**Errores comunes**:

| Lo que escribiste | Debería ser |
|---|---|
| `SINAN_KIMI_API_KEY` | `SINAN_MOONSHOT_API_KEY` |
| `SINAN_QWEN_API_KEY` | `SINAN_DASHSCOPE_API_KEY` |
| `SINAN_GLM_API_KEY` | `SINAN_ZHIPUAI_API_KEY` |

#### `Fallo de validación del Schema (tras 2 reintentos)`

**Causa**: El formato JSON de salida del LLM es inestable (modelo pequeño / temperatura alta).

**Solución**: Asignar un modelo más potente a los agentes clave

```env
SINAN_RUBRIC_A_PROVIDER=deepseek
SINAN_JUDGE_PROVIDER=deepseek
```

> Para más elementos de solución de problemas, consulte [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

---

## Ejemplo de productos

`outputs/strategy_ecommerce_ecommerce_v1_20251104_141500.md`:

```markdown
# Estrategia de operaciones Q4 de e-commerce

> Dominio: ecommerce | Puntuación del Judge: 85/100 | Reglas duras: 100/100 | Generado el 2025-11-04 14:15:00

## Objetivo
Aumentar el GMV un 30%, nuevos clientes 40%, tasa de recompra 25%, ROI ≥ 3.0

## Promociones de productos
...

- **Oferta flash del producto estrella A001** — Todos los miércoles, 2 horas limitadas, difusión en el sitio + dominio privado
  (Responsable: equipo de operaciones | Horario: todos los miércoles 20:00-22:00 | KPI: GMV por sesión ≥ 80 000)
```

`outputs/debate_ecommerce_ecommerce_v1_20251104_141500.json`:

```json
{
  "rubric_history": [...],   // Proceso completo de las tres rondas de juego del grupo de preguntas
  "strategy_history": [...], // Proceso completo de las tres rondas de juego del grupo de estrategia
  "judge_reasoning": "..."   // Explicación del dictamen del Judge
}
```

---

## Navegación de documentación

| Documento | Contenido |
|---|---|
| [`USAGE.md`](USAGE.md) | Manual de uso completo (10 escenarios + solución de problemas) |
| [`STRUCTURE.md`](STRUCTURE.md) | Estructura del proyecto, responsabilidades de archivos, flujo de datos |
| [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) | Manual de solución de problemas (buscar por mensaje de error) |
| [`knowledge/README.md`](knowledge/README.md) | Instrucciones de uso de la base de conocimiento |

---

## Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -e ".[all]"

# Ejecutar pruebas
pytest

# Lint
ruff check agent/

# Formateo
ruff format agent/

# Diagnóstico del entorno
python -m agent.doctor
```

---

## License

[Apache-2.0](apach-2.0)

---

## 🙏 Agradecimientos

- [OpenAI Python SDK](https://github.com/openai/openai-python) — Conexión unificada a LLM
- [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) — CLI atractiva
- [Pydantic](https://docs.pydantic.dev/) — Validación estricta de Schema
- [DeepSeek](https://deepseek.com/) / [Kimi](https://kimi.moonshot.cn/) / [Qwen](https://dashscope.aliyun.com/) / [GLM](https://open.bigmodel.cn/) — Capacidad de modelos backend
- [baize](https://github.com/Xu123-Bob/Baize) — Agente de desarrollo propio
- **También agradezco a Beijing News y Shell Finance; esta obra obtuvo el 4/26 en la calificación de Alipay y el 6/26 en el concurso durante el Hackathon de Jóvenes de IA 2026 celebrado, y fue recomendada al Concurso de Agentes Inteligentes de Alipay**