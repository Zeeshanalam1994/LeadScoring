"""HTTP API for refinery simulator."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from refinery_sim.core.reactor_palette import PALETTE
from refinery_sim.core.schema import RefineryConfig, SimulationResult
from refinery_sim.core.solver import RefinerySolver

app = FastAPI(title="Refinery Configuration Simulator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = Path(__file__).resolve().parents[1] / "web" / "dist"


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/config/default", response_model=RefineryConfig)
def default_config() -> RefineryConfig:
    return RefineryConfig.default_config()


@app.get("/api/reactor-palette")
def reactor_palette() -> list:
    return [
        {
            "block_type": e.block_type,
            "display_name": e.display_name,
            "host_unit": e.host_unit,
            "description": e.description,
            "default_params": e.default_params,
        }
        for e in PALETTE
    ]


@app.post("/api/simulate", response_model=SimulationResult)
def simulate(config: RefineryConfig) -> SimulationResult:
    solver = RefinerySolver(config)
    return solver.solve()


if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
