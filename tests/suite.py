import sys, os, os.path
import unittest

sys.path.insert(0, os.path.abspath('..'))

from test_config import ConfigurationTestCase
from test_createrssfeed import ExcludedFoldersTestCase

def config_test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(ConfigurationTestCase)

def rssfeed_test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(ExcludedFoldersTestCase)

def test_main():
    testsuite = config_test_suite()
    runner = unittest.TextTestRunner(sys.stdout, verbosity=2)
    result = runner.run(testsuite)

    testsuite = rssfeed_test_suite()
    runner = unittest.TextTestRunner(sys.stdout, verbosity=2)
    result = runner.run(testsuite)

if __name__ == "__main__":
    test_main()