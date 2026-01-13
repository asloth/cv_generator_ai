from openai import OpenAI
from pydantic import BaseModel, Field
import json


validation_instructions = """
Eres un asistente que ayuda a recopilar información para crear un Curriculim Vitae.
Analiza la conversación y determina qué información falta del usuario.

Información requerida:
1. Información de contacto:
   - Nombre completo
   - Dirección de correo electrónico
   - Número de teléfono
2. Información académica: Puede tener múltiples entradas!
   - Título académico obtenido
   - Nombre de la institución educativa
   - Año de graduación
3. Información laboral: Puede tener múltiples entradas!
   - Nombre de la empresa
   - Puesto de trabajo
   - Responsabilidades del puesto
   - Año de inicio del empleo
   - Año de fin del empleo (si aplica)
4. Agrega una pregunta adicional: ¿Deseas que el modelo sugiera habilidades, motivaciones e intereses adicionales basados en la información proporcionada?

Si falta información, establece datos_completos en false y haz una pregunta específica.
En la pregunta 4. Si se desea agregar habilidades, motivaciones e intereses adicionales, establece add_extra_sections en true.
Si tienes toda la información, establece datos_completos en true.
"""

cv_instructions = """Eres un experto en la creación de CVs profesionales. Tu tarea es generar un CV completo en formato Markdown utilizando EXCLUSIVAMENTE la información estructurada proporcionada a continuación.

INFORMACIÓN ESTRUCTURADA DEL CANDIDATO:
{json.dumps(informacion_estructurada, indent=2, ensure_ascii=False)}

INSTRUCCIONES:
1. Utiliza toda la información estructurada proporcionada como base para el CV
2. Formatea el resultado como un CV profesional y legible en Markdown
3. Organiza las secciones de manera lógica y profesional (Datos personales, Resumen profesional, Experiencia laboral, Educación, Habilidades, etc.)
4. Mantén un tono profesional y conciso
5. NO inventes ni agregues información que no esté en los datos estructurados

SECCIONES OPCIONALES EXTRA (si el usuario lo solicita add_extra_sections):
- Habilidades adicionales que podrían ser relevantes según su experiencia
- Posibles motivaciones profesionales basadas en su trayectoria
- Intereses profesionales que complementen su perfil

SECCIONES OBLIGATORIAS:
- Encabezado con nombre y datos de contacto
- Experiencia laboral (ordenada de más reciente a más antigua)
- Educación académica (ordenada de más reciente a más antigua)

FORMATO DE SALIDA:
- Usa Markdown válido
- Utiliza encabezados apropiados (##, ###)
- Usa listas con viñetas o numeradas donde sea apropiado
- Mantén el formato limpio y profesional
- La sección de sugerencias debe estar claramente separada y marcada como opcional

Genera el CV ahora:
"""
client = OpenAI()

class InformacionContacto(BaseModel):
    nombre: str = Field(..., description="Nombre completo de la persona")
    email: str = Field(..., description="Dirección de correo electrónico")
    telefono: str = Field(..., description="Número de teléfono de contacto")

class InformmacionAcademica(BaseModel):
    titulo: str = Field(..., description="Título académico obtenido")
    institucion: str = Field(..., description="Nombre de la institución educativa")
    anio_graduacion: str = Field(..., description="Año de graduación")

class InformacionLaboral(BaseModel):
    empresa: str = Field(..., description="Nombre de la empresa")
    puesto: str = Field(..., description="Puesto de trabajo")
    responsabilidades: str = Field(..., description="Responsabilidades del puesto")
    anio_inicio: int = Field(..., description="Año de inicio del empleo")
    anio_fin: str = Field(..., description="Año de fin del empleo, si aplica (usar 'Presente' si aún trabaja allí)")

class CurriculumVitae(BaseModel):
    contacto: InformacionContacto
    academica: list[InformmacionAcademica]
    laboral: list[InformacionLaboral]
    add_extra_sections: bool = Field(description="Habilidades, motivaciones e intereses adicionales")

class ValidateData(BaseModel):
    datos_completos: bool = Field(description="True si todos los datos necesarios han sido recopilados")
    pregunta_siguiente: str = Field(description="Pregunta a hacer al usuario si faltan datos")
    cv_datos: CurriculumVitae = Field(description="Datos recopilados para el CV")

messages = []
cost_usage = {'total_tokens': 0, 'total_cost': 0.0, 'details': []}
cost_per_1M_tokens = {
    "gpt-5": 1.25,
    "gpt-5-nano": 0.05,
    "omni-moderation-latest": 0.0
}

print("""
¡Hola! Soy tu asistente para crear un Currículum Vitae.
Para continuar, necesito que me des la siguiente información:
- Información de contacto (nombre completo, correo electrónico, número de teléfono)
- Académica (los títulos obtenidos, instituciones y años de graduación)
- Laboral (empresas, puestos, responsabilidades y años de empleo)
Por favor, proporciona la información solicitada.
      """)

while True:
    input_text = input('Tu: ')

    data_moderation = client.moderations.create(input=input_text, model="omni-moderation-latest")

    if data_moderation.results[0].flagged:
        print("Lo siento, tu mensaje ha sido marcado por contenido inapropiado. Por favor, intenta de nuevo.")
        continue
    # Usar primer modelo para validar datos con JSON schema
    messages.append({"content": input_text, "role": "user"})
    validation_response = client.responses.parse(
        model="gpt-5-nano",
        input=messages,
        instructions=validation_instructions,
        text_format=ValidateData,
        reasoning={"effort": "minimal"}
    )
    #Usage tracking
    cost_usage['total_tokens'] += validation_response.usage.total_tokens # type: ignore
    cost_usage['total_cost'] += (validation_response.usage.total_tokens / 1_000_000) * cost_per_1M_tokens['gpt-5-nano'] # type: ignore
    cost_usage['details'].append({
        'model': 'gpt-5-nano',
        'total_tokens': validation_response.usage.total_tokens, # type: ignore
        'cost': (validation_response.usage.total_tokens / 1_000_000) * cost_per_1M_tokens['gpt-5-nano'] # type: ignore
    })
    
    validation_data = validation_response.output_parsed
    
    messages.append(
        {"content": validation_response.output_text, "role": "assistant"})

    if validation_data.datos_completos: # type: ignore
        print("Asistente: ¡Gracias! He recopilado toda la información necesaria para tu Currículum Vitae.")
        # Guardar datos en un archivo JSON
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(validation_data.model_dump(), f, ensure_ascii=False, indent=4) # type: ignore

        cv_response = client.responses.parse(
            model="gpt-5",
            input=[
                {"content": f"Información para el cv: {validation_data.cv_datos.model_dump_json(indent=2)}", "role": "user"}], # type: ignore
            instructions=cv_instructions,
            reasoning={"effort": "minimal"},
        )
        #Usage tracking
        cost_usage['total_tokens'] += cv_response.usage.total_tokens # type: ignore
        cost_usage['total_cost'] += (cv_response.usage.total_tokens / 1_000_000) * cost_per_1M_tokens['gpt-5'] # type: ignore
        cost_usage['details'].append({
            'model': 'gpt-5',
            'total_tokens': cv_response.usage.total_tokens, # type: ignore
            'cost': (validation_response.usage.total_tokens / 1_000_000) * cost_per_1M_tokens['gpt-5'] # type: ignore
        })

        try:
            with open("tokens.json", "w", encoding="utf-8") as jf:
                json.dump(cost_usage, jf, ensure_ascii=False, indent=4) # type: ignore
            with open("curriculum.md", "w", encoding="utf-8") as f:
                f.write(cv_response.output_text)
            print("✅ CV guardado exitosamente en 'cv_generado.md'")
        except Exception as e:
            print(f"❌ Error al guardar el archivo: {e}")

        break
    else:
        # Mostrar pregunta siguiente
        print("Asistente: ", validation_data.pregunta_siguiente) # type: ignore

