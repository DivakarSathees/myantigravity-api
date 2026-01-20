#!/usr/bin/env python3

def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True

if __name__ == '__main__':
    limit = 100
    primes = [str(n) for n in range(2, limit + 1) if is_prime(n)]
    print(f"Prime numbers up to {limit}:")
    print(', '.join(primes))
