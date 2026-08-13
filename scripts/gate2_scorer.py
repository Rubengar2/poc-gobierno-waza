import sys
import json
import os

def evaluar_resultados(ruta_resultados):
    score = 100
    hard_gate_fail = False

    print(f"\n--- Evaluando resultados de WAZA en: {ruta_resultados} ---")

    if os.path.exists(ruta_resultados):
        with open(ruta_resultados, 'r') as f:
            waza_data = json.load(f)
            
        outcomes = waza_data.get("outcomes", [])
        if not outcomes:
            print("[-] Falla: WAZA no generó 'outcomes' válidos. Revisa el eval.yaml.")
            score -= 20
            
        for outcome in outcomes:
            if outcome.get("status") == "failed":
                print(f"[-] Falla (Calidad/Seguridad): La tarea '{outcome.get('task', 'desconocida')}' falló.")
                score -= 30
                hard_gate_fail = True
    else:
        print("[-] Falla CRÍTICA: No se encontró results.json. WAZA falló estructuralmente.")
        score -= 50
        hard_gate_fail = True

    print(f"SCORE FINAL: {score}/100")
    return score, hard_gate_fail

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python gate2_scorer.py <ruta_al_results.json>")
        sys.exit(1)

    ruta_archivo = sys.argv[1]
    score, hard_gate = evaluar_resultados(ruta_archivo)
    
    if score < 80 or hard_gate:
        print(f"🚨 VEREDICTO FINAL: BLOCK (Falla el Gate 2)\n")
        sys.exit(1) # Código 1 bloquea la PR en GitHub Actions
    else:
        print(f"✅ VEREDICTO FINAL: PASS\n")
        sys.exit(0) # Código 0 permite la PR

