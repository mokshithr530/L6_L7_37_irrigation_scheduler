import pytest
from irrigation_scheduler import should_irrigate, water_volume, schedule


# ---------------------------------------------------------------------------
# Tests for should_irrigate (100% Line & Branch Coverage)
# ---------------------------------------------------------------------------

def test_wet_soil_no_irrigation():
    # Initial starter test: moisture >= 60
    assert should_irrigate(70, 0, "seedling") is False
    assert should_irrigate(60, 0, "flowering") is False


def test_heavy_rain_no_irrigation():
    # rain_mm >= 10
    assert should_irrigate(50, 10, "seedling") is False
    assert should_irrigate(30, 15, "flowering") is False


def test_seedling_stage_branches():
    # stage == "seedling", moisture < 45 vs >= 45
    assert should_irrigate(44, 0, "seedling") is True
    assert should_irrigate(45, 0, "seedling") is False


def test_flowering_stage_branches():
    # stage == "flowering", moisture < 55 vs >= 55
    assert should_irrigate(54, 0, "flowering") is True
    assert should_irrigate(55, 0, "flowering") is False


def test_other_stage_rain_and_moisture_branches():
    # other stages: rain_mm >= 5 -> False; moisture < 40 vs >= 40
    assert should_irrigate(30, 5, "vegetative") is False
    assert should_irrigate(39, 2, "vegetative") is True
    assert should_irrigate(40, 2, "vegetative") is False


# ---------------------------------------------------------------------------
# Tests for water_volume (100% Line & Branch Coverage)
# ---------------------------------------------------------------------------

def test_water_volume_invalid_area():
    # area_m2 <= 0 raises ValueError
    with pytest.raises(ValueError, match="invalid area"):
        water_volume(0, "seedling", 20)
    with pytest.raises(ValueError, match="invalid area"):
        water_volume(-5, "seedling", 20)


def test_seedling_volume():
    # Initial starter test: stage == "seedling"
    assert water_volume(10, "seedling", 20) == 20.0


def test_flowering_and_other_volumes():
    # stage == "flowering" (litres=5) and else (litres=4)
    assert water_volume(10, "flowering", 20) == 50.0
    assert water_volume(10, "other", 20) == 40.0


def test_water_volume_temperature_branches():
    # temp_c > 35 (1.5x), temp_c < 10 (0.5x), normal temp (1.0x)
    assert water_volume(10, "seedling", 40) == 30.0
    assert water_volume(10, "seedling", 5) == 10.0
    assert water_volume(10, "seedling", 35) == 20.0


# ---------------------------------------------------------------------------
# Tests for schedule (100% Line & Branch Coverage)
# ---------------------------------------------------------------------------

def test_schedule_empty():
    assert schedule([], 100) == []


def test_schedule_branches():
    # Covers continue (unneeded), normal addition, and break (budget exhausted)
    zones = [
        ("Zone_Skipped", 10, 70, 0, "seedling", 20),      # should_irrigate False -> continue
        ("Zone_Added", 10, 30, 0, "seedling", 20),        # need = 20 <= 50 -> added, budget = 30
        ("Zone_Exceeds", 10, 30, 0, "flowering", 20),     # need = 50 > 30 -> break
        ("Zone_Ignored", 10, 30, 0, "seedling", 20),
    ]
    assert schedule(zones, 50) == ["Zone_Added"]


def test_schedule_exact_budget():
    zones = [("Zone_Exact", 10, 30, 0, "seedling", 20)]
    assert schedule(zones, 20) == ["Zone_Exact"]
