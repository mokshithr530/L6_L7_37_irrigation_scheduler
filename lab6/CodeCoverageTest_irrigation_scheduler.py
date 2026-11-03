import pytest
from irrigation_scheduler import should_irrigate, water_volume, schedule


# ---------------------------------------------------------------------------
# Code (Line) Coverage Tests for should_irrigate
# ---------------------------------------------------------------------------

def test_should_irrigate_high_moisture():
    # Covers line: moisture >= 60 -> returns False
    assert should_irrigate(60, 0, "seedling") is False


def test_should_irrigate_heavy_rain():
    # Covers line: rain_mm >= 10 -> returns False
    assert should_irrigate(50, 10, "seedling") is False


def test_should_irrigate_seedling_dry():
    # Covers line: stage == "seedling" and moisture < 45 -> returns True
    assert should_irrigate(40, 0, "seedling") is True


def test_should_irrigate_seedling_moist():
    # Covers line: stage == "seedling" and moisture >= 45 -> returns False
    assert should_irrigate(50, 0, "seedling") is False


def test_should_irrigate_flowering():
    # Covers line: stage == "flowering" -> returns moisture < 55
    assert should_irrigate(50, 0, "flowering") is True
    assert should_irrigate(58, 0, "flowering") is False


def test_should_irrigate_moderate_rain():
    # Covers line: rain_mm >= 5 for other stages -> returns False
    assert should_irrigate(30, 5, "vegetative") is False


def test_should_irrigate_other_stage_dry_and_moist():
    # Covers line: return moisture < 40 for other stages
    assert should_irrigate(35, 2, "vegetative") is True
    assert should_irrigate(45, 2, "vegetative") is False


# ---------------------------------------------------------------------------
# Code (Line) Coverage Tests for water_volume
# ---------------------------------------------------------------------------

def test_water_volume_invalid_area():
    # Covers line: area_m2 <= 0 -> raises ValueError
    with pytest.raises(ValueError, match="invalid area"):
        water_volume(0, "seedling", 20)
    with pytest.raises(ValueError, match="invalid area"):
        water_volume(-10, "seedling", 20)


def test_water_volume_seedling_normal_temp():
    # Covers line: stage == "seedling" -> litres = 2
    assert water_volume(10, "seedling", 20) == 20.0


def test_water_volume_flowering_high_temp():
    # Covers line: stage == "flowering" -> litres = 5, temp_c > 35 -> litres * 1.5
    assert water_volume(10, "flowering", 40) == 75.0


def test_water_volume_other_stage_low_temp():
    # Covers line: else -> litres = 4, temp_c < 10 -> litres * 0.5
    assert water_volume(10, "mature", 5) == 20.0


# ---------------------------------------------------------------------------
# Code (Line) Coverage Tests for schedule
# ---------------------------------------------------------------------------

def test_schedule_zones():
    # Covers schedule loop, skipping unneeded zones, adding needed zones, and budget exhaustion break
    zones = [
        ("Zone_Skipped", 10, 70, 0, "seedling", 20),      # moisture=70 -> should_irrigate False (continue)
        ("Zone_Added", 10, 30, 0, "seedling", 20),        # need=20, budget=50 -> added (plan: ["Zone_Added"]), budget=30
        ("Zone_Exceeds", 10, 30, 0, "flowering", 20),     # need=50, budget=30 -> need > budget (break)
        ("Zone_Unreached", 10, 30, 0, "seedling", 20),    # unreachable due to break
    ]
    result = schedule(zones, 50)
    assert result == ["Zone_Added"]


def test_schedule_empty_zones():
    assert schedule([], 100) == []
