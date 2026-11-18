import pandas as pd
import streamlit as st
from main import run_calculation
from plots import plot_beam_diagrams, plot_frame_scheme
from profiles import STEEL_PROFILES, STEEL_E, STEEL_G
from report import generate_beam_recommendations, create_word_report

st.set_page_config(page_title="САПР-прототип | 08.03.01 Строительство", layout="wide")
st.title("🏗️ Прототип приложения для анализа строительных конструкций")

with st.sidebar:
    st.header("1. Выбор конструкции")
    mode = st.radio(
        "Расчётная схема:",
        options=["beam", "frame"],
        format_func=lambda x: "Однопролётная балка (SymPy)" if x == "beam" else "Плоская рама (Pynite МКЭ)"
    )
    
    st.divider()
    st.header("2. Загрузка данных из файла")
    uploaded_file = st.file_uploader("Загрузить параметры (CSV)", type=["csv"])
    st.caption("Формат CSV для балки: колонки L, q")

# ==========================================
# РЕЖИМ 1: БАЛКА (SYMPY + ГОСТ + РЕКОМЕНДАЦИИ + WORD)
# ==========================================
if mode == "beam":
    st.subheader("Расчёт и проверка стальной балки перекрытия")
    
    # Значения по умолчанию или из загруженного CSV
    default_L, default_q = 6.0, 10000.0
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if "L" in df.columns and "q" in df.columns:
            default_L = float(df["L"].iloc[0])
            default_q = float(df["q"].iloc[0])
            st.toast("Данные успешно загружены из CSV!")

    col1, col2, col3 = st.columns(3)
    L = col1.number_input("Пролёт балки L (м)", value=default_L, step=0.5)
    q = col2.number_input("Распределённая нагрузка q (Н/м)", value=default_q, step=1000.0)
    profile_name = col3.selectbox("Профиль по ГОСТ (Сталь С245)", options=list(STEEL_PROFILES.keys()), index=2)

    prof = STEEL_PROFILES[profile_name]
    st.caption(f"Характеристики сечения: I_y = {prof['Iy']*1e8:.0f} см⁴ | W_y = {prof['Wy']*1e6:.1f} см³ | A = {prof['A']*1e4:.1f} см²")

    if st.button("Выполнить расчёт и анализ", type="primary"):
        res = run_calculation("beam", {"L": L, "E": STEEL_E, "I": prof["Iy"], "q": q})
        
        if "error" in res:
            st.error(f"Ошибка валидации:\n{res['error']}")
        else:
            # 1. Ключевые метрики
            m1, m2, m3 = st.columns(3)
            m1.metric("Опорная реакция R", f"{res['R']:,.1f} Н")
            m2.metric("Макс. момент M_max", f"{res['M_max']:,.1f} Н·м")
            m3.metric("Макс. прогиб w_max", f"{res['w_max']*1000:.2f} мм")

            # 2. Инженерные рекомендации
            st.subheader("📋 Инженерный анализ и рекомендации")
            recs = generate_beam_recommendations(L, q, res["M_max"], res["w_max"], profile_name, prof["Wy"])
            for r in recs:
                if "❌" in r:
                    st.error(r)
                elif "⚠️" in r:
                    st.warning(r)
                elif "✅" in r:
                    st.success(r)
                else:
                    st.info(r)

            # 3. Экспорт отчёта в Word
            word_file = create_word_report(
                title="Отчёт по расчёту однопролётной стальной балки",
                inputs={"Пролёт L, м": L, "Нагрузка q, Н/м": q, "Профиль ГОСТ": profile_name, "Модуль упругости E, Па": f"{STEEL_E:.2e}"},
                results={"Опорная реакция R, Н": round(res["R"], 1), "Макс. момент M, Н·м": round(res["M_max"], 1), "Макс. прогиб w, мм": round(res["w_max"]*1000, 2)},
                recommendations=recs
            )
            st.download_button(
                label="📥 Скачать инженерный отчёт (.docx)",
                data=word_file,
                file_name="otchet_balka.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

            # 4. Визуализация эпюр
            fig = plot_beam_diagrams(L, res["M_expr"], res["Q_expr"], res["w_expr"])
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# РЕЖИМ 2: РАМА (PYNITE + ГОСТ + РЕКОМЕНДАЦИИ + WORD)
# ==========================================
elif mode == "frame":
    st.subheader("МКЭ-расчёт стальной П-образной рамы")
    
    col1, col2, col3, col4 = st.columns(4)
    L = col1.number_input("Пролёт ригеля L (м)", value=6.0, step=0.5)
    H = col2.number_input("Высота стоек H (м)", value=4.0, step=0.5)
    F_horiz = col3.number_input("Горизонтальная сила на N2 (Н)", value=5000.0, step=500.0)
    profile_name = col4.selectbox("Профиль стержней (ГОСТ)", options=list(STEEL_PROFILES.keys()), index=3)

    prof = STEEL_PROFILES[profile_name]

    if st.button("Рассчитать раму", type="primary"):
        nodes = {"N1": (0, 0, 0), "N2": (0, H, 0), "N3": (L, H, 0), "N4": (L, 0, 0)}
        props = (STEEL_E, STEEL_G, prof["Iy"], prof["Iz"], prof["J"], prof["A"])
        members = {
            "Col_L": ("N1", "N2", *props),
            "Beam":  ("N2", "N3", *props),
            "Col_R": ("N3", "N4", *props),
        }
        supports = {
            "N1": (True, True, True, True, True, True),
            "N4": (True, True, True, True, True, True),
        }
        loads = [("N2", "FX", F_horiz)]

        res = run_calculation("frame", {"nodes": nodes, "members": members, "loads": loads, "supports": supports})

        if "error" in res:
            st.error(res["error"])
        else:
            r1 = float(res["reactions_FY"]["N1"])
            r4 = float(res["reactions_FY"]["N4"])
            
            c1, c2 = st.columns(2)
            c1.metric("Реакция в левой опоре (N1)", f"{r1:,.2f} Н")
            c2.metric("Реакция в правой опоре (N4)", f"{r4:,.2f} Н")

            recs_frame = [
                f"✅ РАВНОВЕСИЕ СИСТЕМЫ: Сумма вертикальных реакций опор равна {r1 + r4:.2f} Н (условие статики выполнено).",
                f"💡 ФУНДАМЕНТЫ: Левая опора N1 испытывает отрывающее усилие {abs(r1):.1f} Н — требуется анкеровка базы колонны. Правая опора N4 работает на сжатие ({r4:.1f} Н).",
                f"💡 ЖЁСТКОСТЬ УЗЛОВ: При отношении высоты к пролёту H/L = {H/L:.2f} рекомендуется проверить горизонтальное перемещение верха колонн."
            ]
            for r in recs_frame:
                st.info(r)

            word_file = create_word_report(
                title="Отчёт по МКЭ-расчёту плоской стальной рамы",
                inputs={"Пролёт L, м": L, "Высота H, м": H, "Горизонтальная сила, Н": F_horiz, "Профиль ГОСТ": profile_name},
                results={"Реакция FY (узел N1), Н": r1, "Реакция FY (узел N4), Н": r4},
                recommendations=recs_frame
            )
            st.download_button(
                label="📥 Скачать отчёт по раме (.docx)",
                data=word_file,
                file_name="otchet_rama.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

            fig_frame = plot_frame_scheme(nodes, members, loads)
            st.plotly_chart(fig_frame, use_container_width=True)
