from pydantic import BaseModel, Field, model_validator
from typing import Dict, List, Tuple, Literal

# --- 1. Схема проверки данных для БАЛКИ ---
class BeamInput(BaseModel):
    # gt=0 (greater than 0) гарантирует, что геометрия и жёсткость строго больше нуля
    L: float = Field(..., gt=0, description="Пролёт балки, м")
    E: float = Field(..., gt=0, description="Модуль упругости, Па")
    I: float = Field(..., gt=0, description="Момент инерции, м⁴")
    # Нагрузка может быть любой (положительной, отрицательной или нулевой)
    q: float = Field(..., description="Распределённая нагрузка, Н/м")


# --- 2. Схема проверки данных для РАМЫ ---
class FrameInput(BaseModel):
    nodes: Dict[str, Tuple[float, float, float]] = Field(..., min_length=2)
    members: Dict[str, Tuple[str, str, float, float, float, float, float, float]] = Field(..., min_length=1)
    supports: Dict[str, Tuple[bool, bool, bool, bool, bool, bool]] = Field(..., min_length=1)
    loads: List[Tuple[str, Literal["FX", "FY", "FZ", "MX", "MY", "MZ"], float]] = []

    # Инженерная проверка: существуют ли узлы, на которые ссылаются стержни, опоры и нагрузки?
    @model_validator(mode='after')
    def check_topology(self):
        existing_nodes = set(self.nodes.keys())

        # Проверяем узлы стержней
        for member_name, data in self.members.items():
            node_i, node_j = data[0], data[1]
            if node_i not in existing_nodes or node_j not in existing_nodes:
                raise ValueError(f"Стержень '{member_name}' ссылается на несуществующий узел ({node_i} или {node_j})")
            if node_i == node_j:
                raise ValueError(f"Стержень '{member_name}' имеет нулевую длину (узел {node_i} соединён сам с собой)")

        # Проверяем узлы опор
        for sup_node in self.supports.keys():
            if sup_node not in existing_nodes:
                raise ValueError(f"Опора задана для несуществующего узла '{sup_node}'")

        # Проверяем узлы нагрузок
        for load_node, _, _ in self.loads:
            if load_node not in existing_nodes:
                raise ValueError(f"Нагрузка приложена к несуществующему узлу '{load_node}'")

        return self