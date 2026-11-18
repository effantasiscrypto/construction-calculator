from Pynite import FEModel3D

 # Pynite ---
def analyze_frame(nodes, members, loads, supports):
    model = FEModel3D()
    
    for name, (x, y, z) in nodes.items():
        model.add_node(name, x, y, z)
        
    for name, (i, j, E, G, Iy, Iz, J, A) in members.items():
        mat_name = f"Mat_{name}"
        sec_name = f"Sec_{name}"
        model.add_material(mat_name, E=E, G=G, nu=0.3, rho=7850)
        model.add_section(sec_name, A=A, Iy=Iy, Iz=Iz, J=J)
        model.add_member(name, i, j, mat_name, sec_name)
        
    for node, support in supports.items():
        model.def_support(node, *support)
        
    for node, direction, value in loads:
        model.add_node_load(node, direction, value)
        
    model.analyze()
    
    reactions = {
        node: round(model.nodes[node].RxnFY["Combo 1"], 2)
        for node, sup in supports.items() if sup
    }
    return {
        "method": "Pynite (МКЭ)",
        "model": model,
        "reactions_FY": reactions
    }