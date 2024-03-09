from python_template.main import is_prime


async def test_is_prime() -> None:
    assert all([await is_prime(n) is False for n in range(-2, 1)])
    assert await is_prime(2) is True
    assert await is_prime(3) is True
    assert await is_prime(4) is False
    assert await is_prime(41) is True
    assert await is_prime(42) is False
