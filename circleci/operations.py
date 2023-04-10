""" Copyright start
  Copyright (C) 2008 - 2023 Fortinet Inc.
  All rights reserved.
  FORTINET CONFIDENTIAL & FORTINET PROPRIETARY SOURCE CODE
  Copyright end """

import json
import requests
from connectors.core.connector import get_logger, ConnectorError
from .constants import *

logger = get_logger('circleci')


class CircleCI(object):
    def __init__(self, config):
        self.verify_ssl = config.get('verify_ssl')
        self.vc_type = config.get('vc_type')
        self.organization = config.get('organization')
        self.project = config.get('project')
        self.api_key = config.get('api_key')
        self.server_url = config.get('server_url')

    def make_api_call(self, method="GET", endpoint="", params=None, data=None, json_data=None):
        try:
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                'Circle-Token': self.api_key
            }
            url = self.server_url + '/api/v2/' + endpoint
            response = requests.request(method=method, url=url,
                                        headers=headers, data=data, json=json_data, params=params,
                                        verify=self.verify_ssl)
            if response.ok:
                return response.json()
            else:
                if response.text != "":
                    err_resp = response.json()
                    failure_msg = err_resp['message']
                    error_msg = 'Response [{0}:{1} Details: {2}]'.format(response.status_code, response.reason,
                                                                         failure_msg if failure_msg else '')
                else:
                    error_msg = 'Response [{0}:{1}]'.format(response.status_code, response.reason)
                logger.error(error_msg)
                raise ConnectorError(error_msg)
        except requests.exceptions.SSLError:
            logger.error('An SSL error occurred')
            raise ConnectorError('An SSL error occurred')
        except requests.exceptions.ConnectionError:
            logger.error('A connection error occurred')
            raise ConnectorError('A connection error occurred')
        except requests.exceptions.Timeout:
            logger.error('The request timed out')
            raise ConnectorError('The request timed out')
        except requests.exceptions.RequestException:
            logger.error('There was an error while handling the request')
            raise ConnectorError('There was an error while handling the request')
        except Exception as err:
            raise ConnectorError(str(err))

    def build_payload(self, params):
        return {k: MAPPING.get(v, v) for k, v in params.items() if v is not None and v != ''}

    def project_slug(self, params):
        return '{vc_type}/{organization}/{project}'.format(vc_type=SLUG_MAPPING.get(params.pop('vc_type', self.vc_type)),
                                                           organization=params.pop('organization', self.organization),
                                                           project=params.pop('project', self.project))


def get_workflows_list(config, params):
    CCI = CircleCI(config)
    params = CCI.build_payload(params)
    endpoint = f'insights/{CCI.project_slug(params)}/workflows'
    if params.pop('branch_name', "") == "Retrieve Data From All Branches":
        params.update({"all-branches": True})
    logger.error("endpoint is {} and params {}".format(endpoint, params))
    return CCI.make_api_call(endpoint=endpoint, params=params)


def get_artifacts_list(config, params):
    CCI = CircleCI(config)
    params = CCI.build_payload(params)
    job_number = params.get('job-number')
    endpoint = f'project/{CCI.project_slug(params)}/{job_number}/artifacts'
    return CCI.make_api_call(endpoint=endpoint)


def get_workflow_jobs_list(config, params):
    CCI = CircleCI(config)
    endpoint = 'workflow/{0}/job'.format(params.get('id'))
    return CCI.make_api_call(endpoint=endpoint)


def get_workflow_last_runs(config, params):
    CCI = CircleCI(config)
    params = CCI.build_payload(params)
    workflow_name = params.pop('workflow-name')
    endpoint = f'insights/{CCI.project_slug(params)}/workflows/{workflow_name}'
    if params.pop('branch_name', "") == "Retrieve Data From All Branches":
        params.update({"all-branches": True})
    return CCI.make_api_call(endpoint=endpoint, params=params)


def trigger_workflow(config, params):
    CCI = CircleCI(config)
    payload = params.pop('parameters', "")
    params = CCI.build_payload(params)
    endpoint = f'project/{CCI.project_slug(params)}/pipeline'
    return CCI.make_api_call(method='POST', endpoint=endpoint, data=json.dumps(payload))


def _check_health(config):
    try:
        CCI = CircleCI(config)
        CCI.make_api_call(endpoint='me')
        return True
    except Exception as e:
        logger.error("Invalid Credentials: %s" % str(e))
        raise ConnectorError("Invalid Credentials")


operations = {
    'get_workflows_list': get_workflows_list,
    'get_artifacts_list': get_artifacts_list,
    'get_workflow_jobs_list': get_workflow_jobs_list,
    'get_workflow_last_runs': get_workflow_last_runs,
    'trigger_workflow': trigger_workflow
}
