import numpy as np
from scipy.optimize import minimize
from rocket_module import rocket

# Definir una función que valida y ajusta los parámetros
def validate_parameters(parameters):
    """
    Valida y ajusta los parámetros para cumplir con las restricciones físicas.

    Args:
        parameters (list): Lista con los valores de R, R0, Rg, Rs, L, t_chamber, t_cone, alpha, Mpl.

    Returns:
        list: Lista de parámetros válidos.
    """
    R, R0, Rg, Rs, L, t_chamber, t_cone, alpha, Mpl = parameters

    # Garantizar restricciones físicas
    R = max(R, 1e-6)
    R0 = max(R0, 1e-6)
    Rg = max(Rg, 1e-6)
    Rs = max(Rs, Rg + 1e-6)  # Rs debe ser mayor que Rg
    L = max(L, 1e-6)
    t_chamber = max(t_chamber, 1e-6)
    t_cone = max(t_cone, 1e-6)
    alpha = max(alpha, 1e-6)
    Mpl = max(Mpl, 1e-6)

    return [R, R0, Rg, Rs, L, t_chamber, t_cone, alpha, Mpl]

# Definir una función que llama al simulador y devuelve h_max
def evaluate_hmax(parameters):
    """
    Evalúa el h_max para un conjunto dado de parámetros.

    Args:
        parameters (list): Lista con los valores de R, R0, Rg, Rs, L, t_chamber, t_cone, alpha, Mpl.

    Returns:
        float: El valor negativo de h_max (para minimizar).
    """
    parameters = validate_parameters(parameters)
    simulation_params = {
        'R': parameters[0],
        'R0': parameters[1],
        'Rg': parameters[2],
        'Rs': parameters[3],
        'L': parameters[4],
        't_chamber': parameters[5],
        't_cone': parameters[6],
        'alpha': parameters[7],
        'Mpl': parameters[8],
        # Constantes
        'Tc': 1000,
        'M_molar': 41.98e-3,
        'M_molar_air': 28.97e-3,
        'gamma': 1.3,
        'gamma_air': 1.4,
        'viscosity_air': 1.82e-05,
        'rho_pr': 1800,
        'rho_cone': 2700,
        'rho_c': 2700,
        'Rend': 1 - 0.4237,
        'a': 6e-5,
        'n': 0.32,
        'Re': 6.37e6,
        'g0': 9.80665,
        'Ra': 287,
        # Condiciones iniciales
        'h0': 0,
        'v0': 0,
        't0': 0,
        'solver_engine': 'RK4',
        'solver_trayectory': 'Euler',
        'dt_engine': 5e-5,
        'dt_trayectory': 1e-3,
        'stop_condition': 'max_height'
    }

    # Crear la instancia del cohete y simular
    try:
        r = rocket(simulation_params)
        r.simulation()
        result = r.results()
        return -result['h_max']  # Negativo porque estamos minimizando
    except Exception as e:
        print(f"Error en la simulación: {e}")
        return 1e6  # Penalización alta pero finita

# Definir los límites para los parámetros y calcular el gradiente
def optimize_hmax():
    """
    Optimiza los parámetros para maximizar h_max usando un método basado en gradiente.

    Returns:
        dict: Resultados de la optimización con los parámetros óptimos y h_max.
    """
    bounds = [
        (0.01, 0.1),    # R (m)
        (0.001, 0.05),  # R0 (m)
        (0.001, 0.05),  # Rg (m)
        (0.001, 0.05),  # Rs (m)
        (0.05, 0.5),    # L (m)
        (0.001, 0.01),  # t_chamber (m)
        (0.001, 0.01),  # t_cone (m)
        (5, 30),        # alpha (grados)
        (0.1, 5.0)      # Mpl (kg)
    ]

    initial_guess = [
        0.05,  # R
        0.005,   # R0
        0.005,   # Rg
        0.006,   # Rs (inicialmente mayor que Rg)
        0.4,    # L
        0.002,   # t_chamber
        0.002,   # t_cone
        20,      # alpha
        0.11      # Mpl
    ]

    # Ejecutar la optimización con límite de iteraciones
    options = {
        'maxiter': 50,  # Limitar el número máximo de iteraciones
        'disp': True,   # Mostrar información sobre el progreso
        'ftol': 1e-3,   # Relajar la tolerancia de la función objetivo
        'gtol': 1e-3    # Relajar la tolerancia del gradiente
    }

    result = minimize(evaluate_hmax, initial_guess, bounds=bounds, method='L-BFGS-B', options=options)

    if result.success:
        optimized_parameters = result.x
        h_max_optimized = -result.fun
        return {
            'optimized_parameters': optimized_parameters,
            'h_max': h_max_optimized
        }
    else:
        raise RuntimeError("La optimización no tuvo éxito.")

if __name__ == '__main__':
    try:
        results = optimize_hmax()
        print(f"Parámetros óptimos: {results['optimized_parameters']}")
        print(f"Altura máxima optimizada (h_max): {results['h_max']}")
    except RuntimeError as e:
        print(e)