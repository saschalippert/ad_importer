def is_prime(num):
    for i in range(2, num):
        if num % i == 0:
            return False

    return True


def get_primes(count):
    primes = []
    num = 2

    while len(primes) < count:
        if is_prime(num):
            primes.append(num)

        num = num + 1

    return primes
