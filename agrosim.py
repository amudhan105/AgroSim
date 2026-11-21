"""
AgroSim Research Edition
A lightweight agent-based sugarcane farm model.

Run:
    python agrosim.py --mode baseline
    python agrosim.py --mode research
    python agrosim.py --mode research --ticks 3240 --rainfall-mm 5 --rain-interval 12
    python agrosim.py --check

Important:
Research-mode rainfall, evaporation, and root-demand defaults are controlled
experimental inputs, NOT locally calibrated agronomic measurements.
"""

import argparse
import math
from pathlib import Path

import mesa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# SOIL PARAMETERS: loam, initial literature-based illustrative values
# ---------------------------------------------------------------------------
SOIL_TYPE = "loam"
SATURATION_WATER_CONTENT = 0.47
FIELD_CAPACITY = 0.27
WILTING_POINT = 0.12
SOIL_DEPTH_M = 0.30
INITIAL_SOIL_MOISTURE = FIELD_CAPACITY


class SoilWater:
    """One-dimensional water balance for a 0.30 m soil layer."""

    def __init__(self):
        layer_mm = SOIL_DEPTH_M * 1000.0
        self.saturation_mm = SATURATION_WATER_CONTENT * layer_mm
        self.field_capacity_mm = FIELD_CAPACITY * layer_mm
        self.wilting_point_mm = WILTING_POINT * layer_mm
        self.water_mm = INITIAL_SOIL_MOISTURE * layer_mm
        self.total_rainfall_mm = 0.0
        self.total_drainage_mm = 0.0
        self.total_evaporation_mm = 0.0
        self.total_root_uptake_mm = 0.0

    def add_rainfall(self, rainfall_mm):
        if rainfall_mm < 0:
            raise ValueError("Rainfall cannot be negative.")
        self.total_rainfall_mm += rainfall_mm
        self.water_mm += rainfall_mm
        drainage = max(0.0, self.water_mm - self.saturation_mm)
        self.water_mm -= drainage
        self.total_drainage_mm += drainage
        return drainage

    def evaporate(self, evaporation_mm):
        if evaporation_mm < 0:
            raise ValueError("Evaporation cannot be negative.")
        actual = min(evaporation_mm, self.water_mm)
        self.water_mm -= actual
        self.total_evaporation_mm += actual
        return actual

    def absorb_water(self, uptake_mm):
        if uptake_mm < 0:
            raise ValueError("Root uptake cannot be negative.")
        available = max(0.0, self.water_mm - self.wilting_point_mm)
        actual = min(uptake_mm, available)
        self.water_mm -= actual
        self.total_root_uptake_mm += actual
        return actual

    def get_moisture(self):
        return self.water_mm / (SOIL_DEPTH_M * 1000.0)

    def water_stress_factor(self):
        """Simple linear stress factor between wilting point and field capacity."""
        available_range = self.field_capacity_mm - self.wilting_point_mm
        if available_range <= 0:
            return 0.0
        return max(0.0, min(
            1.0,
            (self.water_mm - self.wilting_point_mm) / available_range
        ))


class SugarcaneAgent(mesa.Agent):
    """One sugarcane field cell."""

    def __init__(self, model):
        super().__init__(model)
        self.sugar_content = self.random.uniform(0, 0.112)
        self.height = self.random.uniform(0, 2)
        self.price_at_mill = 0.0
        self.pos = None
        self.soil = SoilWater()
        self.water_stress = 1.0

    def calculate_price_at_mill(self):
        if self.pos is None:
            raise ValueError("Agent position is not set.")
        x1, y1 = self.pos
        x2, y2 = self.model.width, 0
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        price = 14000 * (
            self.sugar_content * (1 - distance * (0.6 / 16.9))
        )
        return round(price, 2)

    def harvest(self):
        self.height = 0.0
        self.sugar_content = 0.0
        self.model.number_harvested += 1
        self.model.cashflow += self.price_at_mill
        self.model.cashflow -= 0.05

    def step(self):
        if self.model.mode == "baseline":
            if self.model.rain <= self.model.rain_probability:
                self.height += 0.00123 * 2
                self.sugar_content += 0.0000688 * 2
            else:
                self.height += 0.00123
                self.sugar_content += 0.0000688
                self.model.cashflow -= 0.3
        else:
            # Research extension: water stress scales growth.
            self.height += 0.00123 * self.water_stress
            self.sugar_content += 0.0000688 * self.water_stress
            # Controlled experimental root-water demand, not calibrated.
            requested_uptake = self.model.root_demand_mm * self.water_stress
            self.soil.absorb_water(requested_uptake)

        self.price_at_mill = self.calculate_price_at_mill()

        if (
            self.model.best_patch == self.pos
            and self.height >= self.model.minimum_height_to_harvest
            and self.model.current_harvesting_capacity > 0
        ):
            self.harvest()
            self.model.current_harvesting_capacity -= 1


def average_height(model):
    return float(np.mean([agent.height for agent in model.agents]))


def average_soil_moisture(model):
    if model.mode == "baseline":
        return float("nan")
    return float(np.mean([agent.soil.get_moisture() for agent in model.agents]))


def total_drainage(model):
    if model.mode == "baseline":
        return 0.0
    return float(sum(a.soil.total_drainage_mm for a in model.agents))


def total_evaporation(model):
    if model.mode == "baseline":
        return 0.0
    return float(sum(a.soil.total_evaporation_mm for a in model.agents))


def total_root_uptake(model):
    if model.mode == "baseline":
        return 0.0
    return float(sum(a.soil.total_root_uptake_mm for a in model.agents))


class AgroSimModel(mesa.Model):
    def __init__(
        self,
        mode="baseline",
        width=30,
        height=30,
        minimum_height_to_harvest=2.4,
        harvesting_capacity_per_step=1,
        rain_probability=0.3,
        seed=100,
        rainfall_mm=5.0,
        rain_interval=12,
        evaporation_mm=0.01,
        root_demand_mm=0.02,
    ):
        super().__init__(rng=seed)
        self.mode = mode
        self.width = width
        self.height = height
        self.grid = mesa.space.MultiGrid(width, height, torus=False)

        self.rain = None
        self.rain_probability = rain_probability
        self.rainfall_mm = rainfall_mm
        self.rain_interval = rain_interval
        self.evaporation_mm = evaporation_mm
        self.root_demand_mm = root_demand_mm

        self.minimum_height_to_harvest = minimum_height_to_harvest
        self.harvesting_capacity_per_step = harvesting_capacity_per_step
        self.current_harvesting_capacity = harvesting_capacity_per_step
        self.number_harvested = 0
        self.cashflow = 1_000_000.0
        self.best_patch = None
        self.mill_position = (width - 1, 0)

        for x in range(width):
            for y in range(height):
                if (x, y) == self.mill_position:
                    continue
                plant = SugarcaneAgent(self)
                self.grid.place_agent(plant, (x, y))
                plant.price_at_mill = plant.calculate_price_at_mill()

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Average Height": average_height,
                "Cashflow": "cashflow",
                "Number Harvested": "number_harvested",
                "Average Soil Moisture": average_soil_moisture,
                "Cumulative Drainage (mm per cell)": total_drainage,
                "Cumulative Evaporation (mm per cell)": total_evaporation,
                "Cumulative Root Uptake (mm per cell)": total_root_uptake,
            },
            agent_reporters={
                "Height": "height",
                "Sugar Content": "sugar_content",
                "Soil Water (mm)": lambda a: a.soil.water_mm,
                "Soil Moisture": lambda a: a.soil.get_moisture(),
                "Water Stress": "water_stress",
            },
        )

    def find_best_patch(self):
        best = None
        max_price = -float("inf")
        for agent in self.agents:
            if agent.price_at_mill > max_price:
                max_price = agent.price_at_mill
                best = agent.pos
        return best

    def prepare_research_water_cycle(self):
        # Synthetic, repeatable rainfall pulse. This is an experiment input.
        rainfall = (
            self.rainfall_mm
            if self.rain_interval > 0 and (self.steps + 1) % self.rain_interval == 0
            else 0.0
        )
        for agent in self.agents:
            agent.soil.add_rainfall(rainfall)
            agent.soil.evaporate(self.evaporation_mm)
            agent.water_stress = agent.soil.water_stress_factor()
        return rainfall

    def step(self):
        if self.mode == "baseline":
            self.rain = self.random.uniform(0, 1)
        else:
            self.rain = self.prepare_research_water_cycle()

        self.best_patch = self.find_best_patch()
        # Preserves the original project's pre-agent-activation collection order.
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")
        self.current_harvesting_capacity = self.harvesting_capacity_per_step


def run_checks():
    soil = SoilWater()
    assert round(soil.water_mm, 6) == 81.0
    assert round(soil.add_rainfall(20), 6) == 0.0
    assert round(soil.water_mm, 6) == 101.0
    assert round(soil.add_rainfall(60), 6) == 20.0
    assert round(soil.water_mm, 6) == 141.0

    soil = SoilWater()
    assert round(soil.evaporate(10), 6) == 10.0
    assert round(soil.water_mm, 6) == 71.0
    assert round(soil.evaporate(100), 6) == 71.0
    assert round(soil.water_mm, 6) == 0.0

    soil = SoilWater()
    assert round(soil.absorb_water(2), 6) == 2.0
    assert round(soil.water_mm, 6) == 79.0
    assert round(soil.absorb_water(100), 6) == 43.0
    assert round(soil.water_mm, 6) == 36.0
    assert round(soil.absorb_water(2), 6) == 0.0

    for bad in (-1,):
        for operation in (soil.add_rainfall, soil.evaporate, soil.absorb_water):
            try:
                operation(bad)
            except ValueError:
                pass
            else:
                raise AssertionError("Negative water flux was accepted.")
    print("All integrated soil-water checks passed.")


def export_results(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    model_df = model.datacollector.get_model_vars_dataframe()
    agent_df = model.datacollector.get_agent_vars_dataframe()
    model_df.to_csv(output_dir / "model_results.csv", index=False)
    agent_df.to_csv(output_dir / "agent_results.csv")

    # Charts are generated from recorded simulation data.
    plt.figure(figsize=(10, 5))
    plt.plot(model_df["Cashflow"])
    plt.title(f"AgroSim {model.mode.title()}: Farm Cashflow")
    plt.xlabel("Simulation tick")
    plt.ylabel("Cashflow")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_dir / "cashflow.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(model_df["Number Harvested"])
    plt.title("Cumulative Sugarcane Harvesting")
    plt.xlabel("Simulation tick")
    plt.ylabel("Cumulative plants harvested")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_dir / "harvesting.png", dpi=150)
    plt.close()

    if model.mode == "research":
        plt.figure(figsize=(10, 5))
        plt.plot(model_df["Average Soil Moisture"])
        plt.axhline(FIELD_CAPACITY, linestyle="--", label="Field capacity")
        plt.axhline(WILTING_POINT, linestyle=":", label="Wilting point")
        plt.title("Average Soil Moisture")
        plt.xlabel("Simulation tick")
        plt.ylabel("Volumetric water content (m³/m³)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_dir / "soil_moisture.png", dpi=150)
        plt.close()

        plt.figure(figsize=(10, 5))
        plt.hist(agent_df["Soil Water (mm)"].dropna(), bins=30)
        plt.title("Final Recorded Soil Water Distribution")
        plt.xlabel("Soil water in 0.30 m layer (mm)")
        plt.ylabel("Number of field cells")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_dir / "soil_water_distribution.png", dpi=150)
        plt.close()

    return model_df, agent_df


def main():
    parser = argparse.ArgumentParser(description="Run AgroSim sugarcane ABM.")
    parser.add_argument("--mode", choices=["baseline", "research"], default="baseline")
    parser.add_argument("--ticks", type=int, default=3240)
    parser.add_argument("--seed", type=int, default=100)
    parser.add_argument("--rainfall-mm", type=float, default=5.0)
    parser.add_argument("--rain-interval", type=int, default=12)
    parser.add_argument("--evaporation-mm", type=float, default=0.01)
    parser.add_argument("--root-demand-mm", type=float, default=0.02)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        run_checks()
        return
    if args.ticks <= 0:
        parser.error("--ticks must be positive")
    if args.rain_interval < 0:
        parser.error("--rain-interval cannot be negative")

    model = AgroSimModel(
        mode=args.mode,
        seed=args.seed,
        rainfall_mm=args.rainfall_mm,
        rain_interval=args.rain_interval,
        evaporation_mm=args.evaporation_mm,
        root_demand_mm=args.root_demand_mm,
    )

    print(f"AGROSIM: {args.mode.upper()} SIMULATION")
    print("-------------------------------------")
    print("Ticks:", args.ticks)
    print("Field agents:", len(model.agents))
    if args.mode == "research":
        print("Soil:", SOIL_TYPE)
        print("Soil layer depth:", SOIL_DEPTH_M, "m")
        print("Synthetic rainfall:", args.rainfall_mm, "mm every", args.rain_interval, "ticks")
        print("Experimental evaporation demand:", args.evaporation_mm, "mm/tick/cell")
        print("Experimental root demand:", args.root_demand_mm, "mm/tick/cell")

    for tick in range(args.ticks):
        model.step()
        if (tick + 1) % 500 == 0 or tick + 1 == args.ticks:
            print(f"Completed ticks: {tick + 1}")

    print("\nSIMULATION RESULTS")
    print("-------------------------------------")
    print("Total ticks:", model.steps)
    print("Total plants:", len(model.agents))
    print("Final average height:", round(average_height(model), 4))
    print("Total harvested:", model.number_harvested)
    print("Final cashflow:", round(model.cashflow, 2))

    if args.mode == "research":
        print("Final average soil moisture:", round(average_soil_moisture(model), 4))
        print("Total drainage (sum across cells, mm):", round(total_drainage(model), 3))
        print("Total evaporation (sum across cells, mm):", round(total_evaporation(model), 3))
        print("Total root uptake (sum across cells, mm):", round(total_root_uptake(model), 3))

    output_dir = Path("outputs") / args.mode
    export_results(model, output_dir)
    print("\nCSV files and graphs saved in:", output_dir)
    print("Note: DataCollector records before agent activation on each tick.")


if __name__ == "__main__":
    main()
