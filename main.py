from pydantic import ValidationError
from beam import analyze_simple_beam
from frame import analyze_frame
from schemas import BeamInput, FrameInput
from plots import plot_beam_diagrams

def run_calculation(method: str, params: dict) -> dict:
    try:
        if method == "beam":
                # 1. Проверяем данные через Pydantic
            valid_data = BeamInput(**params)
                # 2. Передаём проверенный словарь в расчёт
            return analyze_simple_beam(**valid_data.model_dump())
                
        elif method == "frame":
            valid_data = FrameInput(**params)
            return analyze_frame(**valid_data.model_dump())
                
        else:
            raise ValueError(f"Неизвестный метод расчёта: {method}")
    except ValidationError as e:
        # Выводим понятную ошибку, если инженер ввёл некорректные данные
        print(f"❌ Ошибка входных данных ({method}):\n{e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Тест 1: Корректные данные (должно сработать)
    res_beam = run_calculation("beam", {"L": 6.0, "E": 2.1e11, "I": 8e-5, "q": 10000.0})
    if "error" not in res_beam:
        print("✅ Балка посчитана. Реакция R:", res_beam["R"], "Н\n")
        fig = plot_beam_diagrams(
            L=6.0,
            M_expr_str=res_beam["M_expr"],
            Q_expr_str=res_beam["Q_expr"],
            w_expr_str=res_beam["w_expr"]
        )
        fig.show()  # Откроет интерактивный график в браузере!

    # Тест 2: Намеренная ошибка — отрицательный пролёт L = -5 (Pydantic должен заблокировать)
    print("--- Проверка защиты от дурака ---")
    run_calculation("beam", {"L": -5.0, "E": 2.1e11, "I": 8e-5, "q": 10000.0})

if __name__ == "__main__":
    # Проверка балки
    res_beam = run_calculation("beam", {"L": 6.0, "E": 2.1e11, "I": 8e-5, "q": 10000.0})
    print("Балка -> Реакция R:", res_beam["R"], "Н")

    # Проверка рамы
    nodes = {"N1": (0, 0, 0), "N2": (0, 4, 0), "N3": (6, 4, 0), "N4": (6, 0, 0)}
    props = (2.1e11, 8.1e10, 8e-5, 8e-5, 1e-5, 0.005)
    members = {"Col_L": ("N1", "N2", *props), "Beam": ("N2", "N3", *props), "Col_R": ("N3", "N4", *props)}
    supports = {"N1": (True, True, True, True, True, True), "N4": (True, True, True, True, True, True)}
    loads = [("N2", "FX", 5000.0)]

    res_frame = run_calculation("frame", {"nodes": nodes, "members": members, "loads": loads, "supports": supports})
    print("Рама -> Реакции FY:", res_frame["reactions_FY"])