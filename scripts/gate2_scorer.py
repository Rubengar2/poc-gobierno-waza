import sys
import json
import os

def evaluar_agente(ruta_resultados, ruta_instrucciones):
    score = 100
    hard_gate_fail = False
    
    print(f"--- Evaluando {ruta_resultados} ---")

    # 1. ECONOMÍA: Verificar si Waza Check falló (Metadatos/Tokens)
    # En un entorno real waza check emite un exit code. Aquí simulamos la lectura básica.
    if not os.path.exists(ruta_instrucciones):
        print("[-] Falla: No hay archivo de instrucciones.")
        score -= 20
    else:
        with open(ruta_instrucciones, 'r') as f:
            contenido = f.read()
            if "max_tokens" not in contenido:
                print("[-] Penalización (Economía): Faltan límites de tokens corporativos.")
                score -= 15

    # 2. CALIDAD: Leer resultados de WAZA run (Contratos y Alucinaciones)
    if os.path.exists(ruta_resultados):
        with open(ruta_resultados, 'r') as f:
            waza_data = json.load(f)
            
        for outcome in waza_data.get("outcomes", []):
            if outcome["status"] == "failed":
                print(f"[-] Falla (Calidad): El agente rompió el esquema o alucinó en la tarea {outcome.get('task','')}.")
                score -= 30
                # Si quisieras integrar la lógica de seguridad (ej. intentó usar tool de escritura)
                # podrías verificar el error específico aquí y hacer: hard_gate_fail = True

    print(f"SCORE PARCIAL: {score}/100")
    
    return score, hard_gate_fail

if __name__ == "__main__":
    agentes = ["agentes/agente_bueno", "agentes/agente_malo"]
    estado_final = 0

    for agente in agentes:
        resultados = f"{agente}/results.json"
        instrucciones = f"{agente}/instrucciones.md"
        
        score, hard_gate = evaluar_agente(resultados, instrucciones)
        
        if score < 80 or hard_gate:
            print(f"🚨 VEREDICTO PARA {agente}: BLOCK (Falla el Gate 2)\n")
            estado_final = 1 # Romperá el pipeline
        else:
            print(f"✅ VEREDICTO PARA {agente}: PASS\n")

    sys.exit(estado_final)


