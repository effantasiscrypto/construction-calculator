# расчёт балок SymPy
import sympy as sp

#sympy
def analyze_simple_beam (L,E,I,q):
	# L — длина пролёта балки (например, в метрах или миллиметрах)
	# E — модуль упругости (модуль Юнга) материала балки, характеризующий его жёсткость
	# I — момент инерции поперечного сечения балки
	# q — интенсивность равномерно распределённой нагрузки по длине балки
    x = sp.symbols('x')
    R = q * L / 2
    M = R * x - q * x**2 / 2
    Q = sp.diff(M, x)

    w = sp.integrate(sp.integrate(-M/E/I, x), x)
    C1, C2 = sp.symbols('C1 C2')
    w = w + C1*x + C2
    eq1 = w.subs(x, 0)
    eq2 = w.subs(x, L)
    sol = sp.solve([eq1, eq2], [C1, C2])
    w = w.subs(sol)
    return {
        "method": "SymPy (Аналитика)",
        "R": R,
        "M_expr": M,
        "Q_expr": Q,
        "w_expr": w,
        "M_max": sp.maximum(M, x, sp.Interval(0, L)),
        "w_max": sp.maximum(w, x, sp.Interval(0, L))
    }
