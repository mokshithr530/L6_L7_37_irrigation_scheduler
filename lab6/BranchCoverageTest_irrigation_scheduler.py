import pytest
from irrigation_scheduler import should_irrigate, water_volume, schedule


# ===========================================================================
# 1. Branch Coverage Tests: should_irrigate
# Control structures evaluated:
#   - if moisture >= 60 (True/False)
#   - if rain_mm >= 10 (True/False)
#   - if stage == "seedling" (True/False)
#       - if moisture < 45 (True/False)
#   - if stage == "flowering" (True/False)
#       - returns moisture < 55 (True/False)
#   - if rain_mm >= 5 (True/False)
#   - return moisture < 40 (True/False)
# ===========================================================================

def test_branch_should_irrigate_moisture_boundary():
    # Branch: moisture >= 60 -> True (no irrigation)
    assert should_irrigate(60, 0, "seedling") is False
    assert should_irrigate(80, 0, "seedling") is False
    # Branch: moisture < 60 -> False (proceeds to next check)
    assert should_irrigate(59, 15, "seedling") is False


def test_branch_should_irrigate_rain_boundary_10mm():
    # Branch: rain_mm >= 10 -> True (no irrigation)
    assert should_irrigate(50, 10, "seedling") is False
    assert should_irrigate(50, 20, "flowering") is False
    # Branch: rain_mm < 10 -> False (proceeds to stage checks)
    assert should_irrigate(40, 9, "seedling") is True


def test_branch_should_irrigate_seedling_stage():
    # Branch: stage == "seedling" -> True
    #   Sub-branch: moisture < 45 -> True (irrigate)
    assert should_irrigate(44, 0, "seedling") is True
    assert should_irrigate(30, 2, "seedling") is True
    #   Sub-branch: moisture >= 45 -> False (do not irrigate)
    assert should_irrigate(45, 0, "seedling") is False
    assert should_irrigate(55, 0, "seedling") is False


def test_branch_should_irrigate_flowering_stage():
    # Branch: stage != "seedling", stage == "flowering" -> True
    #   Sub-branch: moisture < 55 -> True
    assert should_irrigate(54, 0, "flowering") is True
    assert should_irrigate(20, 2, "flowering") is True
    #   Sub-branch: moisture >= 55 -> False
    assert should_irrigate(55, 0, "flowering") is False
    assert should_irrigate(58, 2, "flowering") is False


def test_branch_should_irrigate_other_stage_rain_5mm():
    # Branch: stage != "seedling" and stage != "flowering"
    #   Branch: rain_mm >= 5 -> True (no irrigation)
    assert should_irrigate(30, 5, "vegetative") is False
    assert should_irrigate(20, 8, "fruiting") is False
    #   Branch: rain_mm < 5 -> False (proceeds to moisture < 40)
    #     Sub-branch: moisture < 40 -> True
    assert should_irrigate(39, 4, "vegetative") is True
    #     Sub-branch: moisture >= 40 -> False
    assert should_irrigate(40, 4, "vegetative") is False
    assert should_irrigate(50, 0, "vegetative") is False


# ===========================================================================
# 2. Branch Coverage Tests: water_volume
# Control structures evaluated:
#   - if area_m2 <= 0 (True: raises ValueError, False: proceeds)
#   - if stage == "seedling" (litres = 2)
#   - elif stage == "flowering" (litres = 5)
#   - else (litres = 4)
#   - if temp_c > 35 (litres *= 1.5)
#   - elif temp_c < 10 (litres *= 0.5)
#   - else normal temp (10 <= temp_c <= 35) (no adjustment)
# ===========================================================================

def test_branch_water_volume_invalid_area():
    # Branch: area_m2 <= 0 -> True (raises ValueError)
    with pytest.raises(ValueError, match="invalid area"):
        water_volume(0, "seedling", 25)
    with pytest.raises(ValueError, match="invalid area"):
        water_volume(-5.5, "flowering", 25)


def test_branch_water_volume_stages():
    # Branch: stage == "seedling" (litres = 2)
    assert water_volume(10, "seedling", 25) == 20.0
    # Branch: stage == "flowering" (litres = 5)
    assert water_volume(10, "flowering", 25) == 50.0
    # Branch: else (litres = 4)
    assert water_volume(10, "vegetative", 25) == 40.0
    assert water_volume(10, "harvest", 25) == 40.0


def test_branch_water_volume_temperatures():
    # Branch: temp_c > 35 -> True (1.5x)
    assert water_volume(10, "seedling", 36) == 30.0
    assert water_volume(10, "flowering", 40) == 75.0
    assert water_volume(10, "other", 35.1) == pytest.approx(60.0)

    # Branch: temp_c < 10 -> True (0.5x)
    assert water_volume(10, "seedling", 9) == 10.0
    assert water_volume(10, "flowering", 0) == 25.0
    assert water_volume(10, "other", -5) == 20.0

    # Branch: 10 <= temp_c <= 35 -> False for both temp branches (1.0x)
    assert water_volume(10, "seedling", 10) == 20.0
    assert water_volume(10, "seedling", 35) == 20.0
    assert water_volume(10, "flowering", 20) == 50.0


# ===========================================================================
# 3. Branch Coverage Tests: schedule
# Control structures evaluated:
#   - for name, area, moisture, rain, stage, temp in zones (empty vs non-empty)
#   - if not should_irrigate(...) (True: continue, False: proceeds)
#   - if need > budget (True: break, False: budget -= need, append)
# ===========================================================================

def test_branch_schedule_empty_zones():
    # Branch: for loop over empty list (does not enter body)
    assert schedule([], 500) == []


def test_branch_schedule_all_branches():
    zones = [
        # Zone 1: should_irrigate is False -> triggers 'continue'
        ("Zone_Wet", 10, 75, 0, "seedling", 25),
        # Zone 2: should_irrigate is True, need = 20 <= budget (100) -> added, rem budget = 80
        ("Zone_A", 10, 30, 0, "seedling", 20),
        # Zone 3: should_irrigate is True, need = 50 <= budget (80) -> added, rem budget = 30
        ("Zone_B", 10, 30, 0, "flowering", 20),
        # Zone 4: should_irrigate is True, need = 40 > budget (30) -> triggers 'break'
        ("Zone_C", 10, 30, 0, "vegetative", 20),
        # Zone 5: unreachable after break
        ("Zone_D", 10, 30, 0, "seedling", 20),
    ]
    scheduled = schedule(zones, 100)
    assert scheduled == ["Zone_A", "Zone_B"]


def test_branch_schedule_exact_budget():
    # Tests edge case where need == budget (need > budget evaluates to False)
    zones = [
        ("Zone_Exact", 10, 30, 0, "seedling", 20), # need = 20
    ]
    assert schedule(zones, 20) == ["Zone_Exact"]
