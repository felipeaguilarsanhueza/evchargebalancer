from flask import Flask, request, render_template, jsonify, redirect, url_for
from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

# Variables globales
limites = [200] * 24  
cant_cargadores_vip = 2  
cant_cargadores_controlados = 4  

@app.route('/update_limits', methods=['GET', 'POST'])
def update_limits():
    global limites, cant_cargadores_vip, cant_cargadores_controlados

    if request.method == 'POST':
        # Procesar límites
        new_limits = request.form.getlist('limits[]')
        if len(new_limits) != 24:
            return jsonify({"error": "La cantidad de límites proporcionados no es válida"}), 400

        # Procesar cantidad de cargadores
        new_cant_cargadores_vip = request.form.get('cant_cargadores_vip')
        new_cant_cargadores_controlados = request.form.get('cant_cargadores_controlados')
        
        if new_cant_cargadores_vip and new_cant_cargadores_controlados:
            cant_cargadores_vip = int(new_cant_cargadores_vip)
            cant_cargadores_controlados = int(new_cant_cargadores_controlados)
        else:
            return jsonify({"error": "La cantidad de cargadores no es válida"}), 400

        # Calcular corriente mínima
        min_current_vip = 32 * cant_cargadores_vip if cant_cargadores_vip > 0 else 0
        min_current_controlados = 6 * cant_cargadores_controlados
        min_current = min_current_vip + min_current_controlados

        for lim in new_limits:
            if int(lim) < min_current:
                return jsonify({"error": "Algunos de los límites ingresados son inferiores a la corriente mínima total necesaria"}), 400

        limites = [int(lim) for lim in new_limits]

        return redirect(url_for('mostrar_resultado'))
    else:
        return render_template('update_limits.html', limits=limites, cant_cargadores_vip=cant_cargadores_vip, cant_cargadores_controlados=cant_cargadores_controlados)

@app.route('/restart', methods=['GET'])
def restart():
    global limites, cant_cargadores_vip, cant_cargadores_controlados
    limites = [200] * 24
    cant_cargadores_vip = 2
    cant_cargadores_controlados = 4
    try:
        os.remove('static/graph.png')
    except FileNotFoundError:
        pass
    return redirect(url_for('update_limits'))

@app.route('/resultado', methods=['GET'])
def mostrar_resultado():
    solucion_controlados, solucion_vip = solve_problem()
    return render_template('resultado.html', solucion_controlados=solucion_controlados, solucion_vip=solucion_vip, cant_cargadores_controlados=cant_cargadores_controlados, cant_cargadores_vip=cant_cargadores_vip)

@app.route('/solve', methods=['GET'])
def solve_problem():
    global limites, cant_cargadores_vip, cant_cargadores_controlados

    prob = LpProblem("Maximizacion_de_Corriente", LpMaximize)
    cargadores_controlados = [[LpVariable(f"Cargador_Controlado_{i+1}_Hora_{h}", 6, 32) for h in range(24)] for i in range(cant_cargadores_controlados)]

    cargadores_vip = np.full((cant_cargadores_vip, 24), 32) if cant_cargadores_vip > 0 else np.array([])

    prob += lpSum(cargadores_controlados)

    for h in range(24):
        total_current_vip = np.sum(cargadores_vip[:, h]) if cant_cargadores_vip > 0 else 0
        prob += lpSum(cargador[h] for cargador in cargadores_controlados) + total_current_vip <= limites[h]

    prob.solve()

    solucion_controlados = [[0] * 24 for _ in range(cant_cargadores_controlados)]
    solucion_vip = cargadores_vip.tolist() if cant_cargadores_vip > 0 else []

    if LpStatus[prob.status] == 'Optimal':
        for i, cargador in enumerate(cargadores_controlados):
            for h in range(24):
                solucion_controlados[i][h] = cargador[h].varValue
    else:
        return jsonify({'error': 'El problema no tiene solución.'}), 400

    solucion_total = np.concatenate((solucion_controlados, solucion_vip), axis=0) if cant_cargadores_vip > 0 else solucion_controlados
    solucion_acumulada_total = np.cumsum(solucion_total, axis=0)
    
    sns.set()
    
    for i, cargador in enumerate(solucion_acumulada_total):
        if i < len(solucion_controlados):
            plt.plot(range(24), cargador, label=f"Cargador Controlado {i+1}")
            if i == 0:
                plt.fill_between(range(24), 0, cargador, color=f'C{i}', alpha=0.3)
            else:
                plt.fill_between(range(24), solucion_acumulada_total[i-1], cargador, color=f'C{i}', alpha=0.3)
        elif cant_cargadores_vip > 0:  
            plt.plot(range(24), cargador, label=f"Cargador VIP {i+1-len(solucion_controlados)}")

    if cant_cargadores_vip > 0:  
        plt.fill_between(range(24), solucion_acumulada_total[len(solucion_controlados)-1], solucion_acumulada_total[-1], color='yellow', alpha=0.3)

    plt.plot(range(24), limites, label="Límite", color="red", linestyle='--')
    plt.legend(loc="upper left")
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.title('Optimización de Carga de Vehículos Eléctricos')
    plt.xlabel('Horas')
    plt.ylabel('Corriente (A)')
    plt.tight_layout()
    plt.savefig('static/graph.png', dpi=300)
    plt.close()

    return solucion_controlados, solucion_vip

if __name__ == '__main__':
    app.run(debug=True)