# CV Generator AI

Uso de la API de OpenAI para generar Currículums Vitae (CV) en formato Markdown. El script interactúa en español con el usuario para recopilar información, valida los datos mediante un modelo pequeño, modera entradas, y finalmente genera un CV completo usando un modelo de mayor capacidad. También registra el uso de tokens y el coste estimado.

## Contenido del repositorio
- `main.py` — Script principal. Interactivo; recopila información del usuario, valida con un esquema JSON, usa moderación y genera el CV en Markdown.
- `curriculum.md` — Ejemplo de salida de CV generado.
- `data.json` — (generado en ejecución) Datos estructurados recopilados del usuario.
- `tokens.json` — (generado en ejecución) Registro de tokens usados y coste estimado.
- `curriculum.md` — (generado en ejecución) CV final en formato Markdown.

## Requisitos
- Python 3.10+
- Paquetes Python:
  - `openai` (SDK oficial de OpenAI que provee `OpenAI()` y métodos `responses`, `moderations`, etc.)
  - `pydantic`

Instalación rápida :
```bash
uv init
uv sync
source .venv/bin/activate

```

## Configuración
Define tu clave de API de OpenAI como variable de entorno:
```bash
export OPENAI_API_KEY="tu_api_key"   # macOS / Linux
setx OPENAI_API_KEY "tu_api_key"     # Windows (PowerShell / cmd según corresponda)
```
El script utiliza el cliente `OpenAI()` (desde el paquete `openai`) que por defecto lee la variable de entorno.

Nota: `main.py` usa modelos nombrados en el código como `gpt-5-nano`, `gpt-5` y `omni-moderation-latest`. Asegúrate de tener acceso a los modelos que el script intenta usar o ajusta los nombres de modelo según tu disponibilidad y permisos.

## Uso
Ejecuta el script y sigue las instrucciones interactivas (en español):
```bash
python main.py
```
Flujo típico:
1. El asistente solicita datos de contacto, formación académica y experiencia laboral.
2. Cada entrada del usuario es moderada (modelo de moderación).
3. Se valida la estructura de los datos usando un modelo pequeño (`gpt-5-nano`) y un esquema Pydantic.
4. Si falta información, el asistente pregunta específicamente por los campos faltantes.
5. Cuando los datos están completos, se genera el CV con un modelo más grande (`gpt-5`).
6. El CV se guarda en `curriculum.md`. Los datos crudos se guardan en `data.json` y el registro de tokens/costos en `tokens.json`.

## Salida
- `curriculum.md` — CV en Markdown con secciones: Datos personales, Resumen profesional, Experiencia laboral, Educación, Habilidades y secciones opcionales sugeridas.
- `data.json` — Representación JSON del objeto `CurriculumVitae` (estructura definida por `pydantic` en `main.py`).
- `tokens.json` — Registro con `total_tokens`, `total_cost` y `details` por modelo usado (estimación basada en tarifas definidas en el script).

## Cómo funciona (resumen técnico)
- Validación de datos: se define un esquema con Pydantic (`InformacionContacto`, `InformmacionAcademica`, `InformacionLaboral`, `CurriculumVitae`, `ValidateData`). El script envía la conversación al modelo `gpt-5-nano` para parsear y validar conforme al esquema.
- Moderación: antes de validar cada mensaje del usuario, el texto se manda a `client.moderations.create(..., model="omni-moderation-latest")` y se descartan entradas marcadas.
- Generación final: cuando los datos están completos, se construyen instrucciones detalladas (prompt) para que un modelo de capacidad mayor genere el CV en Markdown.
- Seguimiento de costos: el script suma tokens usados por cada llamada y calcula un coste estimado con tarifas por 1M tokens definidas en `main.py`.
