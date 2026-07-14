# Why these defaults

CasMD's **Standard** configuration tier ships with parameters that match the
validated protein–nucleic-acid MD workflow.

| Parameter | Default | Rationale |
|---|---|---|
| pH | **7.9** | Slightly above physiological; matches lab conditions. |
| Temperature | **310.15 K** | Body temperature; standard for mammalian biology. |
| Box geometry | **12 Å rectangular** | Sufficient padding for solute; rectangular is fastest. |
| Water | **TIP3P** | Most-used 3-site water model, fast and reliable. |
| Salt | **0 M (neutralize only)** | Avoids artifacts in short simulations; add salt for longer. |
| Production length | **500 ns** | Balance between stability + cost. |
| NVT equilibration | **500 ps** | Standard equilibration time. |
| NPT equilibration | **500 ps** | Standard equilibration time. |
| Integrator | **2 fs timestep** | Combined with LINCS h-bond constraints. |

The **Quick** tier uses these same defaults but exposes only the system type
and production length. The **Advanced** tier exposes every parameter for
power users.
