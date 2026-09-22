# Refinery Configuration Simulator

Interactive, first-principles **material-balance** simulator for a typical conversion refinery:

- **CDU** (atmospheric distillation)
- **VDU** (vacuum distillation)
- **FCC** (fluid catalytic cracking)
- **Hydrocracker**
- **Delayed coker**
- **CCR** (continuous catalytic reforming)

### Rigorous reactor palette
Configurable reactor blocks per unit, including **FCC riser + regenerator** (kinetic riser, coke combustion / air / flue gas / heat balance), hydrocracker trickle-bed + HP separator, CCR reactor train + stabilizer, coker furnace + drum, CDU column and VDU flash train anchors, plus hydrotreater / isom / alkylation entries in the palette.

Product streams are aggregated into **LPG**, **kerosene**, **diesel**, and **gasoline** pools, then **product blenders** check finished-product specs (RON, cetane, sulfur).

**Crude feeders** blend multiple assays (Arab Medium, Light Sweet, Heavy Sour, etc.) before the CDU.

**Fired heaters** are modelled on each major unit (Q = ṁ Cp ΔT, fuel from LHV and efficiency). Plant **steam** generation/consumption and **emissions** (CO₂ from fuel + flare, SO₂, NOₓ) are reported.

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

Open http://localhost:5173 — **HYSYS-style PFD**: equipment symbols, labeled streams with flows, object palette, workbook properties, stream table, energy pane, and status bar. Adjust feeds/units/reactors in the workbook; click **▶ Solve** or edit inputs for automatic re-solve.

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
