# hypervisor configuration manifest
# API files

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

class vzsandbox::hypervisor::api (
  $manage_firewall = true,
  $control_server,
  $control_interface,
  ) {
  # the API requires flask-restful which is installed by pip which is provided by epel
  include "vzsandbox::hypervisor::common"
  include "vzsandbox::common::api"

  file { "/usr/local/bin/vzsandbox-api.py":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 750,
    source  => "puppet:///modules/vzsandbox/hypervisor/usr/local/bin/vzsandbox-api.py",
    require => [ Class["vzsandbox::hypervisor::common"],
                 Class["vzsandbox::common::api"] ],
  }

  file { "/usr/local/bin/vzsandbox-api-daemon.sh":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 750,
    source  => "puppet:///modules/vzsandbox/hypervisor/usr/local/bin/vzsandbox-api-daemon.sh",
  }

  file { "/etc/sysconfig/vzsandbox-api":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 644,
    source  => "puppet:///modules/vzsandbox/hypervisor/etc/sysconfig/vzsandbox-api",
  }

  file { "/etc/init.d/vzsandbox-api":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 754,
    source  => "puppet:///modules/vzsandbox/hypervisor/etc/init.d/vzsandbox-api",
  }

  service { 'vzsandbox-api':
        ensure    => running,
        enable    => true,
        subscribe   => [ File["/usr/local/bin/vzsandbox-api.py"],
                         File["/usr/local/bin/vzsandboxlib.py"],
                         File["/usr/local/bin/vzsandbox-api-daemon.sh"],
                         File["/etc/vzsandbox.yaml"],
                         File["/etc/sysconfig/vzsandbox-api"],
                         File["/etc/init.d/vzsandbox-api"],
                         ],
  }

  if $manage_firewall == true {
    include firewall-config::base
    
    firewall { '99 allow 5000/TCP for vzsandboxapi from control server':
      state   => ['NEW'],
      dport   => '5000',
      proto   => 'tcp',
      source  => "$control_server",
      iniface => "$control_interface",
      action  => accept,
    }
  }
}
