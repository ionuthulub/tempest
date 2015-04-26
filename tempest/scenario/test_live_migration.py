# Copyright 2013 NEC Corporation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging

from tempest.common import custom_matchers
from tempest import config
from tempest import exceptions
from tempest.scenario import manager
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class TestLiveMigrationScenario(manager.ScenarioTest):
    """
    This test suite a attempts to test connectivity to a vm during live migration,
    migration of a vm with cinder volume attached to it and migration of a vm with
    data on root and ephemeral disk.

    """

    def test_network_connectivity_during_live_migration(self):
        pass

    def test_migration_of_vm_with_cinder_volume(self):
        pass

    def test_migration_of_vm_with_data_on_root_and_ephemeral_disk(self):
        pass
