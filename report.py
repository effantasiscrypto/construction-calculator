import io
from docx import Document
from profiles import STEEL_PROFILES, STEEL_RY

def generate_beam_recommendations(L: float, q: float, M_max: float, w_max: float, profile_name: str, Wy: float) -> list[str]:
    recs = []
    
    # 1. Проверка по I группе предельных состояний (Прочность: sigma = M / W <= Ry)
    sigma_max = M_max / Wy  # Па
    k_strength = sigma_max / STEEL_RY  # Коэффициент использования по прочности
    
    if k_strength > 1.0:
        recs.append(
            f"❌ КРИТИЧНО (Прочность): Нормальные напряжения ({sigma_max/1e6:.1f} МПа) превышают "
            f"расчётное сопротивление стали С245 ({STEEL_RY/1e6:.0f} МПа) в {k_strength:.2f} раза. "
            f"Сечение «{profile_name}» не проходит!"
        )
    elif k_strength > 0.85:
        recs.append(
            f"⚠️ ВНИМАНИЕ (Прочность): Сечение работает на пределе (загрузка {k_strength*100:.0f}%). "
            f"Рекомендуется взять следующий номер профиля по сортаменту для запаса."
        )
    else:
        recs.append(
            f"✅ ПРОЧНОСТЬ ОБЕСПЕЧЕНА: Максимальные напряжения {sigma_max/1e6:.1f} МПа "
            f"(использование несущей способности: {k_strength*100:.0f}%)."
        )

    # 2. Проверка по II группе предельных состояний (Жёсткость: w_max <= L / 250 по СП 20.13330)
    w_limit = L / 250.0  # Предельный прогиб, м
    k_stiffness = w_max / w_limit
    
    if k_stiffness > 1.0:
        recs.append(
            f"❌ КРИТИЧНО (Жёсткость): Прогиб ({w_max*1000:.2f} мм) превышает допустимый по СП 20.13330 "
            f"L/250 = {w_limit*1000:.2f} мм. Увеличьте высоту сечения или уменьшите шаг балок."
        )
    else:
        recs.append(
            f"✅ ЖЁСТКОСТЬ ОБЕСПЕЧЕНА: Прогиб {w_max*1000:.2f} мм не превышает допустимый "
            f"{w_limit*1000:.2f} мм (использование по прогибу: {k_stiffness*100:.0f}%)."
        )

    # 3. Автоподбор оптимального профиля из базы ГОСТ
    suitable = []
    for name, props in STEEL_PROFILES.items():
        if (M_max / props["Wy"]) <= STEEL_RY:
            suitable.append(name)
            
    if suitable:
        recs.append(f"💡 РЕКОМЕНДАЦИЯ ПО СОРТАМЕНТУ: Минимально достаточный профиль из базы ГОСТ — «{suitable[0]}».")
    else:
        recs.append("💡 РЕКОМЕНДАЦИЯ ПО СОРТАМЕНТУ: Стандартных прокатных профилей из базы недостаточно — перейдите на сварной двутавр или уменьшите пролёт.")

    return recs


def create_word_report(title: str, inputs: dict, results: dict, recommendations: list[str]) -> io.BytesIO:
    doc = Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph("Направление подготовки: 08.03.01 Строительство. Автоматизированный инженерный отчёт.")

    # Раздел 1: Исходные данные
    doc.add_heading("1. Исходные данные конструкции", level=2)
    table_in = doc.add_table(rows=1, cols=2)
    table_in.style = "Table Grid"
    table_in.rows[0].cells[0].text = "Параметр"
    table_in.rows[0].cells[1].text = "Значение"
    for k, v in inputs.items():
        row = table_in.add_row().cells
        row[0].text = str(k)
        row[1].text = str(v)

    # Раздел 2: Результаты расчёта
    doc.add_heading("2. Результаты статического расчёта", level=2)
    table_res = doc.add_table(rows=1, cols=2)
    table_res.style = "Table Grid"
    table_res.rows[0].cells[0].text = "Показатель"
    table_res.rows[0].cells[1].text = "Расчётное значение"
    for k, v in results.items():
        row = table_res.add_row().cells
        row[0].text = str(k)
        row[1].text = str(v)

    # Раздел 3: Инженерные рекомендации
    doc.add_heading("3. Выводы и рекомендации по проектированию", level=2)
    for rec in recommendations:
        doc.add_paragraph(rec, style="List Bullet")

    # Сохраняем документ в оперативную память для скачивания в браузере
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
