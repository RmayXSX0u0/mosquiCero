import pytest
from app import (
    generar_imagen_caso_prueba,
    evaluar_calidad_optica,
    aplicar_reglas_antifalsos_positivos,
    ResultadoAnalisisCriaderos,
    ObjetoDetectado,
    EvidenciaAgua,
)


def crear_resultado_base(estado_agua: str, confianza: float = 0.9, calidad: bool = True) -> ResultadoAnalisisCriaderos:
    return ResultadoAnalisisCriaderos(
        calidad_imagen_suficiente=calidad,
        clasificacion_riesgo="RIESGO_POTENCIAL_DETECTADO",
        objetos_visibles=[
            ObjetoDetectado(
                nombre="Recipiente de prueba",
                es_contenedor_potencial=True,
                estado_observado="Observado en prueba unitaria",
            )
        ],
        evidencia_agua=EvidenciaAgua(
            estado_agua=estado_agua,
            indicadores_visuales=["Indicador de prueba"],
            confianza_evidencia=confianza,
        ),
        condiciones_potenciales_reproduccion="Condición de prueba.",
        observacion_larvas="No es posible confirmar larvas a esta escala.",
        evidencia_observada_resumen="Resumen de prueba.",
        recomendacion_preventiva="Recomendación de prueba.",
        limitaciones_analisis=["Análisis basado en una sola vista 2D."],
    )


def test_caso_1_recipiente_con_agua_estancada():
    """Verifica que un recipiente con agua estancada visible y buena calidad se clasifique como riesgo potencial."""
    img = generar_imagen_caso_prueba("recipiente_agua")
    metricas = evaluar_calidad_optica(img)
    assert metricas["es_apta"] is True

    resultado_modelo = crear_resultado_base("AGUA_ESTANCADA_VISIBLE", confianza=0.88)
    validado = aplicar_reglas_antifalsos_positivos(resultado_modelo, metricas)
    assert validado.clasificacion_riesgo == "RIESGO_POTENCIAL_DETECTADO"


def test_caso_2_recipiente_vacio_no_es_criadero():
    """Garantiza que un recipiente seco/vacío NUNCA sea clasificado como riesgo potencial (evita falsos positivos)."""
    img = generar_imagen_caso_prueba("recipiente_vacio")
    metricas = evaluar_calidad_optica(img)
    assert metricas["es_apta"] is True

    # Incluso si el LLM clasificara erróneamente 'RIESGO_POTENCIAL_DETECTADO', la regla lo corrige:
    resultado_modelo = crear_resultado_base("SECO_O_VACIO", confianza=0.95)
    validado = aplicar_reglas_antifalsos_positivos(resultado_modelo, metricas)
    assert validado.clasificacion_riesgo == "SIN_EVIDENCIA_DE_AGUA_ESTANCADA"


def test_caso_3_superficie_mojada_sin_estancamiento():
    """Garantiza que un piso mojado sin acumulación volumétrica no dispare alerta de criadero."""
    img = generar_imagen_caso_prueba("superficie_mojada")
    metricas = evaluar_calidad_optica(img)
    assert metricas["es_apta"] is True

    resultado_modelo = crear_resultado_base("HUMEDAD_SUPERFICIAL_SIN_ESTANCAMIENTO", confianza=0.85)
    validado = aplicar_reglas_antifalsos_positivos(resultado_modelo, metricas)
    assert validado.clasificacion_riesgo == "SIN_EVIDENCIA_DE_AGUA_ESTANCADA"


def test_caso_4_imagen_ambigua_baja_calidad_es_no_concluyente():
    """Verifica que una fotografía oscura y borrosa sea bloqueada por el filtro óptico como NO CONCLUYENTE."""
    img = generar_imagen_caso_prueba("imagen_ambigua")
    metricas = evaluar_calidad_optica(img)
    assert metricas["es_apta"] is False
    assert len(metricas["motivos_rechazo"]) >= 1

    resultado_modelo = crear_resultado_base("AGUA_ESTANCADA_VISIBLE", confianza=0.90)
    validado = aplicar_reglas_antifalsos_positivos(resultado_modelo, metricas)
    assert validado.clasificacion_riesgo == "RESULTADO_NO_CONCLUYENTE"
    assert validado.calidad_imagen_suficiente is False