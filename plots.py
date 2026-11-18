import numpy as np
import sympy as sp
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_beam_diagrams(L: float, M_expr_str: str, Q_expr_str: str, w_expr_str: str):
    x = sp.symbols('x')
    
    # Превращаем строковые формулы обратно в математические выражения SymPy
    M_expr = sp.sympify(M_expr_str)
    Q_expr = sp.sympify(Q_expr_str)
    w_expr = sp.sympify(w_expr_str)
    
    # Создаём 100 точек вдоль длины балки от 0 до L
    x_vals = np.linspace(0, L, 100)
    
    # sp.lambdify компилирует формулу SymPy в быструю функцию для массива NumPy
    Q_func = sp.lambdify(x, Q_expr, "numpy")
    M_func = sp.lambdify(x, M_expr, "numpy")
    w_func = sp.lambdify(x, w_expr, "numpy")
    
    # Вычисляем значения (если сила или момент константа, растягиваем на весь массив)
    Q_vals = np.broadcast_to(Q_func(x_vals), x_vals.shape)
    M_vals = np.broadcast_to(M_func(x_vals), x_vals.shape)
    w_vals = np.broadcast_to(w_func(x_vals), x_vals.shape) * 1000  # переводим метры в мм

    # Создаём холст с 3 графиками друг под другом
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        subplot_titles=(
            "Эпюра поперечных сил Q(x), Н",
            "Эпюра изгибающих моментов M(x), Н·м",
            "Линия прогиба w(x), мм"
        ),
        vertical_spacing=0.1
    )

    # 1. График Q(x)
    fig.add_trace(go.Scatter(
        x=x_vals, y=Q_vals, fill='tozeroy', name="Q(x)", line=dict(color="#1f77b4")
    ), row=1, col=1)

    # 2. График M(x)
    fig.add_trace(go.Scatter(
        x=x_vals, y=M_vals, fill='tozeroy', name="M(x)", line=dict(color="#ff7f0e")
    ), row=2, col=1)

    # 3. График прогиба w(x)
    fig.add_trace(go.Scatter(
        x=x_vals, y=w_vals, fill='tozeroy', name="w(x)", line=dict(color="#2ca02c")
    ), row=3, col=1)

    fig.update_layout(
        height=700,
        title_text="Результаты расчёта однопролётной балки",
        showlegend=False,
        hovermode="x unified"
    )
    fig.update_xaxes(title_text="Координата вдоль балки x, м", row=3, col=1)
    
    return fig

def plot_frame_scheme(nodes: dict, members: dict, loads: list):
    fig = go.Figure()

    for name, data in members.items():
        node_i, node_j = data[0], data[1]
        x1, y1, _ = nodes[node_i]
        x2, y2, _ = nodes[node_j]
        fig.add_trace(go.Scatter(
            x=[x1, x2], y=[y1, y2],
            mode="lines+markers+text",
            name=name,
            line=dict(color="#1f77b4", width=5),
            marker=dict(size=10, color="#d62728"),
            text=[node_i, node_j],
            textposition="top left"
        ))




    # Отмечаем узлы с приложенными нагрузками
    for node_name, direction, val in loads:
        if val != 0 and node_name in nodes:
            nx, ny, _ = nodes[node_name]
            fig.add_annotation(
                x=nx, y=ny,
                text=f"Сила {direction} = {val} Н",
                showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor="#ff7f0e",
                ax=-50 if direction == "FX" else 0,
                ay=0 if direction == "FX" else -50
            )

    fig.update_layout(
        title="Расчётная схема рамы (X–Y)",
        xaxis_title="Координата X, м",
        yaxis_title="Координата Y, м",
        yaxis=dict(scaleanchor="x", scaleratio=1),  # одинаковый масштаб по осям
        height=450,
        showlegend=False
    )
    return fig
