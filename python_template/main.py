async def is_prime(n: int) -> bool:
    # using the sieve of Eratosthenes
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
