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
import testtools

CONF = config.CONF

LOG = logging.getLogger(__name__)


class TestLiveMigrationScenario(manager.ScenarioTest):
    """
    This test suite attempts to test connectivity to a vm during live migration,
    migration of a vm with cinder volume attached to it and migration of a vm
    with data on root and ephemeral disk.

    """

    _host_key = 'OS-EXT-SRV-ATTR:host'

    def glance_image_create(self):
        img_path = CONF.scenario.img_dir + "/" + CONF.scenario.img_file
        aki_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.aki_img_file
        ari_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.ari_img_file
        ami_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.ami_img_file
        img_container_format = CONF.scenario.img_container_format
        img_disk_format = CONF.scenario.img_disk_format
        LOG.debug("paths: img: %s, container_fomat: %s, disk_format: %s, "
                  "ami: %s, ari: %s, aki: %s" %
                  (img_path, img_container_format, img_disk_format,
                   ami_img_path, ari_img_path, aki_img_path))
        try:
            self.image = self._image_create('scenario-img',
                                            img_container_format,
                                            img_path,
                                            properties={'disk_format':
                                                        img_disk_format})
        except IOError:
            LOG.debug("A qcow2 image was not found. Try to get a uec image.")
            kernel = self._image_create('scenario-aki', 'aki', aki_img_path)
            ramdisk = self._image_create('scenario-ari', 'ari', ari_img_path)
            properties = {
                'properties': {'kernel_id': kernel, 'ramdisk_id': ramdisk}
            }
            self.image = self._image_create('scenario-ami', 'ami',
                                            path=ami_img_path,
                                            properties=properties)
        LOG.debug("image:%s" % self.image)

    def _nova_keypair_add(self):
        self.keypair = self.create_keypair()

    def _nova_boot(self):
        create_kwargs = {'key_name': self.keypair['name']}
        self.server = self.create_server(
            image=self.image, create_kwargs=create_kwargs)

    def _get_compute_hostnames(self):
        body = self.admin_hosts_client.list_hosts()
        return [
            host_record['host_name']
            for host_record in body
            if host_record['service'] == 'compute'
        ]

    def _get_server_details(self, server_id):
        return self.admin_servers_client.get_server(server_id)

    def _get_host_for_server(self, server_id):
        return self._get_server_details(server_id)[self._host_key]

    def _migrate_server_to(self, server_id, dest_host):
        body = self.admin_servers_client.live_migrate_server(
            server_id, dest_host,
            CONF.compute_feature_enabled.block_migration_for_live_migration)
        return body

    def _get_host_other_than(self, host):
        for target_host in self._get_compute_hostnames():
            if host != target_host:
                return target_host

    def _migration(self):
        actual_host = self._get_host_for_server(self.server['id'])
        target_host = self._get_host_other_than(actual_host)
        self._migrate_server_to(self.server['id'], target_host)
        self.servers_client.wait_for_server_status(self.server['id'], 'ACTIVE')
        self.assertEqual(target_host, self._get_host_for_server(self.server['id']))

    def _launch_instance(self):
        self.glance_image_create()
        self._nova_keypair_add()
        self._nova_boot()

    @testtools.skipUnless(False, 'skip')
    def test_network_connectivity_during_live_migration(self):
        if len(self._get_compute_hostnames()) < 2:
            raise self.skipTest(
                "Less than 2 compute nodes, skipping migration test.")
        self._launch_instance()
        floating_ip = self.create_floating_ip(self.server)
        linux_client = self.get_remote_client(floating_ip['ip'])
        self._migration()
        linux_client.exec_command('ls')

    @testtools.skipUnless(False, 'skip')
    def test_migration_of_vm_with_cinder_volume(self):
        if len(self._get_compute_hostnames()) < 2:
            raise self.skipTest(
                "Less than 2 compute nodes, skipping migration test.")
        self._launch_instance()
        self.cinder_create()
        self.nova_volume_attach()
        self.addCleanup(self.nova_volume_detach)
        self._migration()
        self.cinder_show()

    # @testtools.skipUnless(False, 'skip')
    def test_migration_of_vm_with_data_on_root_and_ephemeral_disk(self):
        if len(self._get_compute_hostnames()) < 2:
            raise self.skipTest(
                "Less than 2 compute nodes, skipping migration test.")
        self._launch_instance()
        floating_ip = self.create_floating_ip(self.server)
        linux_client = self.get_remote_client(floating_ip['ip'])
        linux_client.exec_command('echo "Hello World!" > test_live_migration.txt')
        self._migration()
        output = linux_client.exec_command('cat test_live_migration.txt').strip()
        self.assertEqual('Hello World!', output)