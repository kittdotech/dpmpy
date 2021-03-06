# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import datapackage
from mock import patch

from dpm.main import cli
from .base import BaseCliTestCase


class ValidateNonDatapackageDirTest(BaseCliTestCase):
    """
    When user launches `validate` and datapackage.json is not found, error message
    should be displayed.
    """

    def test_validate_empty_dir(self):
        # GIVEN empty current dir
        with self.runner.isolated_filesystem():
            # WHEN `dpm validate` is invoked
            result = self.invoke(cli, ['validate'])

            # THEN exit code should be 1
            self.assertEqual(result.exit_code, 1)
            # AND 'datapackage.json not found' should be printed to stdout
            self.assertRegexpMatches(result.output, 'datapackage.json not found')
