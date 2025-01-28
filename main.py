from reactpy import component, html, run, use_state
import datetime
import json
import os
import subprocess
from tkinter import Tk, filedialog

# Verificar e instalar librerías necesarias
def verificar_instalacion():
    try:
        import reactpy
    except ImportError:
        subprocess.check_call(["pip", "install", "reactpy"])

    try:
        import datetime
    except ImportError:
        subprocess.check_call(["pip", "install", "datetime"])

    try:
        import json
    except ImportError:
        subprocess.check_call(["pip", "install", "json"])

verificar_instalacion()

# Función de cálculo principal
def calcular_penalidades(monto_contrato, plazos_entregables, fechas_notificacion_entregables, fechas_presentacion_entregables, plazos_observaciones, fechas_notificacion_observaciones, fechas_presentacion_observaciones):
    total_plazos_entregables = sum(plazos_entregables)
    F = 0.25 if total_plazos_entregables > 60 else 0.40
    penalidad_diaria = (0.10 * monto_contrato) / (F * total_plazos_entregables)
    resultados_entregables = []
    resultados_observaciones = []

    dias_totales_retraso_entregables = 0
    for i, (plazo, fecha_notificacion, fecha_presentacion) in enumerate(zip(plazos_entregables, fechas_notificacion_entregables, fechas_presentacion_entregables)):
        try:
            fecha_notificacion_dt = datetime.datetime.strptime(fecha_notificacion, '%d/%m/%Y')
            fecha_inicio_plazo = fecha_notificacion_dt + datetime.timedelta(days=1)
            fecha_presentacion_dt = datetime.datetime.strptime(fecha_presentacion, '%d/%m/%Y')
            fecha_cumplimiento_plazo = fecha_inicio_plazo + datetime.timedelta(days=plazo - 1)
            dias_retraso = max(0, (fecha_presentacion_dt - fecha_cumplimiento_plazo).days)

            dias_totales_retraso_entregables += dias_retraso
            resultados_entregables.append({
                "Tipo": f"Entregable {i + 1}",
                "Plazo": plazo,
                "Fecha de notificación": fecha_notificacion,
                "Fecha inicio del plazo": fecha_inicio_plazo.strftime('%d/%m/%Y'),
                "Fecha cumplimiento del plazo": fecha_cumplimiento_plazo.strftime('%d/%m/%Y'),
                "Fecha de presentación": fecha_presentacion,
                "Días de retraso": dias_retraso,
            })
        except ValueError as e:
            resultados_entregables.append({
                "Tipo": f"Entregable {i + 1}",
                "Error": f"Fecha inválida: {str(e)}"
            })

    dias_totales_retraso_observaciones = 0
    for i, (plazo, fecha_notificacion, fecha_presentacion) in enumerate(zip(plazos_observaciones, fechas_notificacion_observaciones, fechas_presentacion_observaciones)):
        try:
            fecha_notificacion_dt = datetime.datetime.strptime(fecha_notificacion, '%d/%m/%Y')
            fecha_inicio_plazo = fecha_notificacion_dt + datetime.timedelta(days=1)
            fecha_presentacion_dt = datetime.datetime.strptime(fecha_presentacion, '%d/%m/%Y')
            fecha_cumplimiento_plazo = fecha_inicio_plazo + datetime.timedelta(days=plazo - 1)
            dias_retraso = max(0, (fecha_presentacion_dt - fecha_cumplimiento_plazo).days)

            dias_totales_retraso_observaciones += dias_retraso
            resultados_observaciones.append({
                "Tipo": f"Observación {i + 1}",
                "Plazo": plazo,
                "Fecha de notificación": fecha_notificacion,
                "Fecha inicio del plazo": fecha_inicio_plazo.strftime('%d/%m/%Y'),
                "Fecha cumplimiento del plazo": fecha_cumplimiento_plazo.strftime('%d/%m/%Y'),
                "Fecha de presentación": fecha_presentacion,
                "Días de retraso": dias_retraso,
            })
        except ValueError as e:
            resultados_observaciones.append({
                "Tipo": f"Observación {i + 1}",
                "Error": f"Fecha inválida: {str(e)}"
            })

    dias_totales_retraso = dias_totales_retraso_entregables + dias_totales_retraso_observaciones
    penalidad_total = penalidad_diaria * dias_totales_retraso
    penalidad_maxima = monto_contrato * 0.10
    monto_a_pagar = min(penalidad_total, penalidad_maxima)

    return {
        "Resultados entregables": resultados_entregables,
        "Resultados observaciones": resultados_observaciones,
        "Penalidad diaria": round(penalidad_diaria, 2),
        "Penalidad total": round(penalidad_total, 2),
        "Penalidad máxima": round(penalidad_maxima, 2),
        "Monto a pagar por penalidad": round(monto_a_pagar, 2),
        "Total días de retraso": dias_totales_retraso,
    }

# Componente principal
@component
def App():
    monto_contrato, set_monto_contrato = use_state("")
    num_entregables, set_num_entregables = use_state(1)
    num_observaciones, set_num_observaciones = use_state(1)
    entregables, set_entregables = use_state([])
    observaciones, set_observaciones = use_state([])
    resultados, set_resultados = use_state(None)

    # Manejo de cambios en los datos dinámicos
    def handle_change(lista, set_lista, index, key, value):
        while len(lista) <= index:
            lista.append({"plazo": "", "fecha_notificacion": "", "fecha_presentacion": ""})
        lista[index][key] = value
        set_lista(lista.copy())

    # Calcular resultados
    async def calcular(event=None):
        try:
            plazos_entregables = [int(e["plazo"]) for e in entregables]
            fechas_notificacion_entregables = [e["fecha_notificacion"] for e in entregables]
            fechas_presentacion_entregables = [e["fecha_presentacion"] for e in entregables]

            plazos_observaciones = [int(o["plazo"]) for o in observaciones]
            fechas_notificacion_observaciones = [o["fecha_notificacion"] for o in observaciones]
            fechas_presentacion_observaciones = [o["fecha_presentacion"] for o in observaciones]

            result = calcular_penalidades(
                float(monto_contrato),
                plazos_entregables,
                fechas_notificacion_entregables,
                fechas_presentacion_entregables,
                plazos_observaciones,
                fechas_notificacion_observaciones,
                fechas_presentacion_observaciones,
            )
            set_resultados(result)
        except ValueError:
            set_resultados({"Error": "Por favor verifica que todos los campos sean válidos."})

    # Descargar resultados como PDF o Excel
    async def descargar_resultados(event=None):
        if resultados:
            root = Tk()
            root.withdraw()
            file_path = filedialog.asksaveasfilename(
                title="Guardar archivo",
                filetypes=[
                    ("Archivos PDF", "*.pdf"),
                    ("Archivos Excel", "*.xlsx")
                ],
                defaultextension=".pdf"
            )

            if file_path.endswith(".pdf"):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(resultados, ensure_ascii=False, indent=4))
                print(f"Resultados descargados en: {file_path}")

            elif file_path.endswith(".xlsx"):
                print(f"Resultados descargados en: {file_path}")

    return html.div(
        {
            "style": {
                "fontFamily": "Arial, sans-serif",
                "margin": "20px",
                "padding": "20px",
                "border": "1px solid #ddd",
                "borderRadius": "8px",
                "maxWidth": "600px",
            }
        },
        [
            html.h1("Cálculo de Penalidades"),
            html.div(
                {
                    "style": {
                        "marginBottom": "20px",
                        "paddingBottom": "10px",
                        "borderBottom": "1px solid #ddd",
                    }
                },
                [
                    html.div(
                        {
                            "style": {"marginBottom": "10px"}
                        },
                        [
                            html.label("Monto del contrato: "),
                            html.input(
                                {
                                    "type": "number",
                                    "value": monto_contrato,
                                    "onChange": lambda event: set_monto_contrato(event["target"]["value"]),
                                    "style": {"marginLeft": "5px"},
                                }
                            ),
                        ]
                    ),
                    html.div(
                        {
                            "style": {"marginBottom": "10px"}
                        },
                        [
                            html.label("Número de entregables: "),
                            html.input(
                                {
                                    "type": "number",
                                    "value": num_entregables,
                                    "onChange": lambda event: set_num_entregables(int(event["target"]["value"])),
                                    "style": {"marginLeft": "5px"},
                                }
                            ),
                        ]
                    ),
                    html.div(
                        {
                            "style": {"marginBottom": "10px"}
                        },
                        [
                            html.label("Número de observaciones: "),
                            html.input(
                                {
                                    "type": "number",
                                    "value": num_observaciones,
                                    "onChange": lambda event: set_num_observaciones(int(event["target"]["value"])),
                                    "style": {"marginLeft": "5px"},
                                }
                            ),
                        ]
                    ),
                ]
            ),
            *[
                html.div(
                    {
                        "style": {
                            "padding": "10px",
                            "marginBottom": "10px",
                            "border": "1px solid #ccc",
                            "borderRadius": "5px",
                        }
                    },
                    [
                        html.h3(f"Entregable {i + 1}"),
                        html.br(),
                        html.label("Plazo (en días): "),
                        html.input(
                            {
                                "type": "number",
                                "value": entregables[i]["plazo"] if i < len(entregables) else "",
                                "onChange": lambda event, idx=i: handle_change(entregables, set_entregables, idx, "plazo", event["target"]["value"]),
                            }
                        ),
                        html.br(),
                        html.label("Fecha de notificación (dd/mm/aaaa): "),
                        html.input(
                            {
                                "type": "text",
                                "value": entregables[i]["fecha_notificacion"] if i < len(entregables) else "",
                                "onChange": lambda event, idx=i: handle_change(entregables, set_entregables, idx, "fecha_notificacion", event["target"]["value"]),
                            }
                        ),
                        html.br(),
                        html.label("Fecha de presentación (dd/mm/aaaa): "),
                        html.input(
                            {
                                "type": "text",
                                "value": entregables[i]["fecha_presentacion"] if i < len(entregables) else "",
                                "onChange": lambda event, idx=i: handle_change(entregables, set_entregables, idx, "fecha_presentacion", event["target"]["value"]),
                            }
                        ),
                    ]
                )
                for i in range(num_entregables)
            ],
           *[
                html.div(
                    {
                        "style": {
                            "padding": "10px",
                            "marginBottom": "10px",
                            "border": "1px solid #ccc",
                            "borderRadius": "5px",
                        }
                    },
                    [
                        html.h3(f"Observación {i + 1}"),
                        html.br(),
                        html.label("Plazo (en días): "),
                        html.input(
                            {
                                "type": "number",
                                "value": observaciones[i]["plazo"] if i < len(observaciones) else "",
                                "onChange": lambda event, idx=i: handle_change(observaciones, set_observaciones, idx, "plazo", event["target"]["value"]),
                            }
                        ),
                        html.br(),
                        html.label("Fecha de notificación (dd/mm/aaaa): "),
                        html.input(
                            {
                                "type": "text",
                                "value": observaciones[i]["fecha_notificacion"] if i < len(observaciones) else "",
                                "onChange": lambda event, idx=i: handle_change(observaciones, set_observaciones, idx, "fecha_notificacion", event["target"]["value"]),
                        }
                        ),
                        html.br(),
                        html.label("Fecha de presentación (dd/mm/aaaa): "),
                        html.input(
                            {
                                "type": "text",
                                "value": observaciones[i]["fecha_presentacion"] if i < len(observaciones) else "",
                                "onChange": lambda event, idx=i: handle_change(observaciones, set_observaciones, idx, "fecha_presentacion", event["target"]["value"]),
                            }
                        ),
                    ]
                )
                for i in range(num_observaciones)
            ],
            html.button({"onClick": calcular, "style": {"marginTop": "10px"}}, "Calcular"),
            html.button(
                {
                    "onClick": descargar_resultados,
                    "style": {"marginTop": "10px", "marginLeft": "10px"},
                },
                "Descargar Resultados",
            ),
            html.div(
                {
                    "style": {
                        "marginTop": "20px",
                        "padding": "10px",
                        "border": "1px solid #ddd",
                        "borderRadius": "8px",
                        "backgroundColor": "#f9f9f9",
                    }
                },
                [
                    html.h2("Resultados"),
                    html.table(
                        [
                            html.thead(
                                html.tr(
                                    [
                                        html.th("Tipo"),
                                        html.th("Plazo"),
                                        html.th("Fecha de notificación"),
                                        html.th("Fecha de inicio"),
                                        html.th("Fecha de cumplimiento"),
                                        html.th("Fecha de presentación"),
                                        html.th("Días de retraso"),
                                    ]
                                )
                            ),
                            html.tbody(
                                [
                                    *[
                                        html.tr(
                                            [
                                                html.td(e["Tipo"]),
                                                html.td(e["Plazo"]),
                                                html.td(e["Fecha de notificación"]),
                                                html.td(e["Fecha inicio del plazo"]),
                                                html.td(e["Fecha cumplimiento del plazo"]),
                                                html.td(e["Fecha de presentación"]),
                                                html.td(e["Días de retraso"]),
                                            ]
                                        )
                                        for e in resultados.get("Resultados entregables", [])
                                    ],
                                    *[
                                        html.tr(
                                            [
                                                html.td(o["Tipo"]),
                                                html.td(o["Plazo"]),
                                                html.td(o["Fecha de notificación"]),
                                                html.td(o["Fecha inicio del plazo"]),
                                                html.td(o["Fecha cumplimiento del plazo"]),
                                                html.td(o["Fecha de presentación"]),
                                                html.td(o["Días de retraso"]),
                                            ]
                                        )
                                        for o in resultados.get("Resultados observaciones", [])
                                    ],
                                    html.tr(
                                        [
                                            html.td({"colSpan": 6}, "Total días de retraso"),
                                            html.td(resultados.get("Total días de retraso", 0)),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ) if resultados else "",
                ]
            ),
            html.div(
                {
                    "style": {
                        "marginTop": "20px",
                        "padding": "10px",
                        "border": "1px solid #ddd",
                        "borderRadius": "8px",
                        "backgroundColor": "#f9f9f9",
                    }
                },
                [
                    html.h2("Cálculos Generales"),
                    html.table(
                        [
                            html.tbody(
                                [
                                    html.tr([html.td("Penalidad diaria"), html.td(resultados.get("Penalidad diaria", 0))]),
                                    html.tr([html.td("Penalidad total"), html.td(resultados.get("Penalidad total", 0))]),
                                    html.tr([html.td("Penalidad máxima"), html.td(resultados.get("Penalidad máxima", 0))]),
                                    html.tr([html.td("Monto a pagar por penalidad"), html.td(resultados.get("Monto a pagar por penalidad", 0))]),
                                ]
                            ),
                        ]
                    ) if resultados else "",
                ]
            ),
        ]
    )

# Ejecutar la aplicación
run(App)










