import unittest


class CyclicU16(int):
    """Cyclic 16-bit unsigned numbers, with special handling of wraparound

    When dealing with 16-bit counters, special care must be taken when
    overflowinging the number. For example, consider two increasing counter
    variables, x and y. At a point in time, we have:

        x == 0xFFF2
        y == 0xFFF5

    At this time `x < y` works, as expected. However, 12 steps later, we have:

        x == 0xFFFE
        y == 0x0001

    which will invert the result of `x < y`, even though the counters have
    increased at the same rate.

    To handle this situation, we define a range (CyclicU16.wrap) in which the
    numbers are assumed to have recently wrapped around, such that:

       x, y = 0xFFFE, 0x0001

       (x < y) == False

    but:

       x, y = CyclicU16(0xFFFE), CyclicU16(0x0001)

       (x < y) == True
    """

    def __new__(cls, k):
        return int.__new__(cls, cls.trunc(k))

    def __init__(self, k, wrap=0x100):
        self._wrap = wrap

    @property
    def wrap(self):
        return self._wrap

    @staticmethod
    def trunc(n):
        return int(n) & 0xFFFF

    def __hash__(self):
        return int(self)

    def __add__(self, k):
        return type(self)(int(self) + int(k))

    def __sub__(self, k):
        return type(self)(int(self) - int(k))

    def __eq__(self, k):
        return int(self) == self.trunc(k)

    def __ne__(self, k):
        return not self.__eq__(k)

    def __lt__(self, other):
        # if sign bit differs, take wrap into account
        if (self ^ other) & 0x8000:
            return self.trunc(self - self.wrap) < self.trunc(other - self.wrap)
        else:
            return int(self) < other

    def __gt__(self, other):
        # if sign bit differs, take wrap into account
        if (self ^ other) & 0x8000:
            return self.trunc(self - self.wrap) > self.trunc(other - self.wrap)
        else:
            return int(self) > other

    def __le__(self, other):
        return not self.__gt__(other)

    def __ge__(self, other):
        return not self.__lt__(other)


class TestCyclic(unittest.TestCase):

    def test_equal(self):
        C = CyclicU16

        self.assertEqual(C(0x42), 0x42)
        self.assertEqual(C(0x10001), 0x1)

    def test_lt(self):
        C = CyclicU16

        self.assertFalse(C(0x1) < C(0x1))
        self.assertFalse(C(0xFFFF) < C(0xFFFF))
        self.assertTrue(C(0x1) < C(0x2))
        self.assertFalse(C(0x2) < C(0x1))
        self.assertTrue(C(0x90) < C(0x120))
        self.assertFalse(C(0x120) < C(0x90))
        self.assertTrue(C(0x101) < C(0x120))
        self.assertFalse(C(0x120) < C(0x101))
        self.assertTrue(C(0xFFFE) < C(0xFFFF))
        self.assertTrue(C(0xFFFE) < C(0x10))
        self.assertFalse(C(0xFFFE) < C(0x110))

    def test_gt(self):
        C = CyclicU16

        self.assertFalse(C(0x1) > C(0x1))
        self.assertFalse(C(0xFFFF) > C(0xFFFF))
        self.assertTrue(C(0x2) > C(0x1))
        self.assertFalse(C(0x1) > C(0x2))
        self.assertTrue(C(0x120) > C(0x90))
        self.assertFalse(C(0x90) > C(0x120))
        self.assertTrue(C(0x120) > C(0x101))
        self.assertFalse(C(0x101) > C(0x120))
        self.assertTrue(C(0xFFFF) > C(0xFFFE))
        self.assertTrue(C(0x10) > C(0xFFFE))
        self.assertFalse(C(0x110) > C(0xFFFE))

    def test_overflow(self):
        C = CyclicU16

        n = C(0xFFFE)
        self.assertEqual(n, 0xFFFE)
        n += 1
        self.assertEqual(n, 0xFFFF)
        n += 1
        self.assertEqual(n, 0x0000)
        n += 1
        self.assertEqual(n, 0x0001)
