from points_logic import calculate_base_points

def test_base_points():
    assert calculate_base_points(500) == 50
    assert calculate_base_points(300) == 30
    assert calculate_base_points(99) == 0
