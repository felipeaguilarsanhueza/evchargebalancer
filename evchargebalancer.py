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

# Variables globales para los límites, cantidad de cargadores VIP y cantidad de cargadores controlados
limites = [500] * 24  # Límites predeterminados
cant_cargadores_vip = 2  # Cantidad de cargadores VIP predeterminada
cant_cargadores_controlados = 4  # Cantidad de cargadores controlados predeterminada

@app.route('/update_limits', methods=['GET', 'POST'])
def update_limits():
    global limites, cant_cargadores_vip, cant_cargadores_controlados

    if request.method == 'POST':
        # Procesar los límites ingresados
        new_limits = request.form.getlist('limits[]')
        if len(new_limits) != 24:
            return jsonify({"error": "La cantidad de límites proporcionados no es válida"}), 400

        # Procesar la cantidad de cargadores VIP y cargadores controlados ingresados
        new_cant_cargadores_vip = request.form.get('cant_cargadores_vip')
        new_cant_cargadores_controlados = request.form.get('cant_cargadores_controlados')

        if new_cant_cargadores_vip and new_cant_cargadores_controlados:
            cant_cargadores_vip = int(new_cant_cargadores_vip)
            cant_cargadores_controlados = int(new_cant_cargadores_controlados)
        else:
            return jsonify({"error": "La cantidad de cargadores VIP y/o cargadores controlados no es válida"}), 400

        # Calcular la corriente mínima total (6A por cada cargador)
        min_current_vip = 32 * cant_cargadores_vip
        min_current_controlados = 6 * cant_cargadores_controlados
        min_current = min_current_vip + min_current_controlados

        # Verificar que cada uno de los nuevos límites es mayor que la corriente mínima
        for lim in new_limits:
            if int(lim) < min_current:
                return jsonify({"error": "Algunos de los límites ingresados son inferiores a la corriente mínima total necesaria"}), 400

        limites = [int(lim) for lim in new_limits]

        # Redirigir a la página de resultado
        return redirect(url_for('mostrar_resultado'))

    else:
        # Pasar los límites y la cantidad de cargadores a la plantilla
        return render_template('update_limits.html', limits=limites,
                               cant_cargadores_vip=cant_cargadores_vip,
                               cant_cargadores_controlados=cant_cargadores_controlados)


@app.route('/restart', methods=['GET'])
def restart():
    global limites, cant_cargadores_vip, cant_cargadores_controlados
    limites = [500] * 24
    cant_cargadores_vip = 2
    cant_cargadores_controlados = 4

    # Intenta eliminar la gráfica si existe
    try:
        os.remove('static/graph.png')
    except FileNotFoundError:
        pass

    return redirect(url_for('update_limits'))



@app.route('/resultado', methods=['GET'])
def mostrar_resultado():
    # Obtener la solución de los límites y las cantidades de cargadores
    solucion_controlados, solucion_vip = solve_problem()

    # Renderizar la plantilla con la solución y la cantidad de cargadores controlados
    return render_template('resultado.html', solucion_controlados=solucion_controlados, solucion_vip=solucion_vip, cant_cargadores_controlados=cant_cargadores_controlados, cant_cargadores_vip=cant_cargadores_vip)


@app.route('/solve', methods=['GET'])
def solve_problem():
    global limites, cant_cargadores_vip, cant_cargadores_controlados

    # Crear el problema de maximización
    prob = LpProblem("Maximizacion_de_Corriente", LpMaximize)

    # Variables para los cargadores controlados en cada hora con límite inferior de 6A
    cargadores_controlados = [[LpVariable(f"Cargador_Controlado_{i+1}_Hora_{h}", 6, 32) for h in range(24)] for i in range(cant_cargadores_controlados)]

    # Los cargadores VIP siempre entregan su corriente máxima de 32A para las 24 horas del día
    cargadores_vip = np.full((cant_cargadores_vip, 24), 32)

    # Objetivo: Maximizar la corriente total de los cargadores controlados
    prob += lpSum(cargadores_controlados)

    # Restricciones: La corriente total en cada hora no debe superar el límite
    # Nota: Ahora debemos tener en cuenta la corriente de los cargadores VIP en las restricciones
    for h in range(24):
        prob += lpSum(cargador[h] for cargador in cargadores_controlados) + np.sum(cargadores_vip[:, h]) <= limites[h]

    # Resolver el problema
    prob.solve()

    solucion_controlados = [[0] * 24 for _ in range(cant_cargadores_controlados)]
    solucion_vip = cargadores_vip.tolist()

    if LpStatus[prob.status] == 'Optimal':
        # Imprimir la corriente máxima para cada cargador en cada hora y guardarla en solucion
        for i, cargador in enumerate(cargadores_controlados):
            for h in range(24):
                print(f"Cargador Controlado {i+1} Hora {h}: {cargador[h].varValue}A")
                solucion_controlados[i][h] = cargador[h].varValue
    else:
        return jsonify({'error': 'El problema no tiene una solución óptima.'}), 400

    # Calcular la corriente acumulada para todos los cargadores
    solucion_total = np.concatenate((solucion_controlados, solucion_vip), axis=0)
    solucion_acumulada_total = np.cumsum(solucion_total, axis=0)

    # Crear un gráfico de la corriente de todos los cargadores y los límites
    for i, cargador in enumerate(solucion_acumulada_total):
        if i < len(solucion_controlados):
            plt.plot(range(24), cargador, label=f"Cargador Controlado {i+1}")
            if i == 0:
                plt.fill_between(range(24), 0, cargador, color=f'C{i}', alpha=0.3)
            else:
                plt.fill_between(range(24), solucion_acumulada_total[i-1], cargador, color=f'C{i}', alpha=0.3)
        else:
            plt.plot(range(24), cargador, label=f"Cargador VIP {i+1-len(solucion_controlados)}")

    # Rellenar el área desde el último cargador controlado hasta los cargadores VIP con color amarillo
    plt.fill_between(range(24), solucion_acumulada_total[len(solucion_controlados)-1], solucion_acumulada_total[-1],
                     color='yellow', alpha=0.3)

    plt.plot(range(24), limites, label="Límite", color="red", linestyle='--')
    plt.xlabel('Hora')
    plt.ylabel('Corriente Acumulada (A)')
    plt.title('Distribución de corriente acumulada para cada cargador')

    # Mejorar la apariencia del gráfico utilizando seaborn
    sns.despine()  # Remover los bordes del gráfico
    plt.tight_layout()  # Ajustar los márgenes del gráfico

    # Ubicación personalizada de la leyenda fuera del gráfico principal
    plt.legend(bbox_to_anchor=(1.04, 0.5), loc="center left", borderaxespad=0.)

    # Guardar el gráfico como archivo
    plt.savefig('static/graph.png')

    #   Limpiar la figura después de guardarla
    plt.clf()

    # Retorna la solución como JSON
    return solucion_controlados, solucion_vip


if __name__ == '__main__':
    app.run(debug=True)