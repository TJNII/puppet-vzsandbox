# hypervisor configuration manifest
# Common files

# Copyright 2013 Tom Noonan II (TJNII)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

class vzsandbox::hypervisor::common (
  $manage_firewall = true,
  $subnet_prefix,
  $min_containers = 25,
  $max_containers = 253,
  $sandbox_domain = $fqdn,
  $target_template,
  ) {
  file { "/usr/local/bin/vzsandboxlib.py":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 640,
    source  => "puppet:///modules/vzsandbox/hypervisor/usr/local/bin/vzsandboxlib.py",
  }

  file { "/etc/vzsandbox.yaml":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 644,
    content => template("vzsandbox/hypervisor/etc/vzsandbox.yaml.erb"),
  }
}
