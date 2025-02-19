import unittest

from algorithm.translation import init_locale


def custom_startTestRun(self):
    data = {'locale': 'en'}
    init_locale(data)


unittest.result.TestResult.startTestRun = custom_startTestRun
