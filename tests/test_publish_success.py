# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import builtins
import datapackage
import json
import responses
from mock import patch, mock_open
from six import string_types

from dpm.main import cli
from .base import BaseCliTestCase


def jsonify(data):
    if not data:
        return ''
    if isinstance(data, bytes):
        return json.loads(data.decode('utf8'))
    if not isinstance(data, string_types):
        return data.read(100)
    return json.loads(data)


class PublishSuccessTest(BaseCliTestCase):
    """
    When user publishes valid datapackage, and server accepts it, dpm should
    report sucess.
    """

    def setUp(self):
        # GIVEN datapackage that can be treated as valid by the dpm
        self.valid_dp = datapackage.DataPackage({
            "name": "some-datapackage",
            "resources": [
                { "name": "some-resource", "path": "./data/some_data.csv", }
            ]
        })
        patch('dpm.main.client.do_publish.validate', lambda *a: self.valid_dp).start()

    @patch('dpm.client.do_publish.open', mock_open())  # mock csv file open
    @patch('dpm.client.do_publish.getsize', lambda a: 5)  # mock csv file size
    def test_publish_success(self):
        # GIVEN the registry server that accepts any user
        responses.add(
                responses.POST, 'https://example.com/api/auth/token',
                json={'token': 'blabla'},
                status=200)
        # AND registry server accepts any datapackage
        responses.add(
                responses.PUT, 'https://example.com/api/package/user/some-datapackage',
                json={'message': 'OK'},
                status=200)
        # AND registry server gives bitstore upload url
        responses.add(
                responses.POST, 'https://example.com/api/auth/bitstore_upload',
                json={'key': 'https://s3.fake/put_here'},
                status=200)
        # AND s3 server allows data upload
        responses.add(
                responses.PUT, 'https://s3.fake/put_here',
                json={'message': 'OK'},
                status=200)
        # AND registry server successfully finalizes upload
        responses.add(
                responses.GET, 'https://example.com/api/package/user/some-datapackage/finalize',
                json={'message': 'OK'},
                status=200)

        # WHEN `dpm publish` is invoked
        result = self.invoke(cli, ['publish', '--publisher', 'testpub'])

        # THEN 'publish ok' should be printed to stdout
        self.assertRegexpMatches(result.output, 'publish ok')
        # AND 5 requests should be sent
        self.assertEqual(
            [(x.request.method, x.request.url, jsonify(x.request.body)) for x in responses.calls],
            [
                # POST authorization
                ('POST', 'https://example.com/api/auth/token',
                    {"username": "user", "secret": "password"}),
                # PUT metadata with datapackage.json contents
                ('PUT', 'https://example.com/api/package/user/some-datapackage',
                    self.valid_dp.to_dict()),
                # POST authorize presigned url for s3 upload
                ('POST', 'https://example.com/api/auth/bitstore_upload',
                    {"publisher": "user", "package": "some-datapackage", "path": "some_data.csv"}),
                # PUT data to s3
                ('PUT', 'https://s3.fake/put_here', ''),
                # GET finalize upload
                ('GET', 'https://example.com/api/package/user/some-datapackage/finalize', '')])
        # AND PUT request should contain serialized datapackage metadata
        self.assertEqual(responses.calls[1].request.body.decode(), self.valid_dp.to_json())
        # AND exit code should be 0
        self.assertEqual(result.exit_code, 0)
