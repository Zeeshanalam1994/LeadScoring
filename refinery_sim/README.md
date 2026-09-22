# Refinery Configuration Simulator

Interactive, first-principles **material-balance** simulator for a typical conversion refinery:

- **CDU** (atmospheric distillation)
- **VDU** (vacuum distillation)
- **FCC** (fluid catalytic cracking)
- **Hydrocracker**
- **Delayed coker**
- **CCR** (continuous catalytic reforming)

Product streams are aggregated into **LPG**, **kerosene**, **diesel**, and **gasoline** pools.

## Model basis

- Pseudo-components by boiling range (`light_gas`, `lpg`, `naphtha`, `kerosene`, `diesel`, `gas_oil`, `vac_residue`, `coke`, `hydrogen`).
- Each unit applies literature-style **yield correlations** with **closed hydrocarbon mass balances** (hydrogen tracked separately for reformer / hydrocracker).
- CDU splits crude by assay and cut logic; downstream units consume capped feeds based on configured capacities.

## Run locally

```bash
# Backend
cd /workspace
pip install -r refinery_sim/requirements.txt
PYTHONPATH=/workspace uvicorn refinery_sim.backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd refinery_sim/web
npm install
npm run dev
```

Open http://localhost:5173 — adjust unit toggles, capacities, and key parameters; the flowsheet updates utilisation after each solve.

## Tests

```bash
PYTHONPATH=/workspace pytest refinery_sim/tests -q
```

## Production bundle

```bash
cd refinery_sim/web && npm run build
PYTHONPATH=/workspace uvicorn refinery_sim.backend.main:app --port 8000
```

Serves the built UI from `/` when `refinery_sim/web/dist` exists.
