# hypervisor configuration manifest

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

class vzsandbox::hypervisor (
  $manage_firewall = true,
  $control_server  = undef,
  # TODO: Combine in openvz class and calculate from subnet
  $subnet_prefix,
  $min_containers,
  $max_containers,
  $vmaccess_interface = $interfaces_internal,
  $control_interface = $interfaces_internal,
  $target_template,
  ) {

    class { "vzsandbox::hypervisor::common":
      manage_firewall => $manage_firewall,
      subnet_prefix   => $subnet_prefix,
      min_containers  => $min_containers,
      max_containers  => $max_containers,
      target_template => $target_template,
    }

    class { "vzsandbox::hypervisor::api":
      manage_firewall   => $manage_firewall,
      control_server    => $control_server,
      control_interface => $control_interface,
    }

    class { "vzsandbox::hypervisor::clean":
    }

    # Templates directory
    file { "/vzTemplates":
      ensure => directory,
      mode   => 755,
      owner  => root,
      group  => root,
    }


    if $manage_firewall == true {
      if $vmaccess_interface != $control_interface {
        firewall { "010 Reject control iface inbound forward":
          chain    => 'FORWARD',
          action   => reject,
          proto    => 'all',
          reject   => 'icmp-host-prohibited',
          iniface  => "$control_interface",
        }
        firewall { "011 Reject control iface outbound forward":
          chain    => 'FORWARD',
          action   => reject,
          proto    => 'all',
          reject   => 'icmp-host-prohibited',
          outiface => "$control_interface",
        }
      }
      
      firewall { "020 Allow openvz inbound traffic":
        chain    => 'FORWARD',
        action   => accept,
        proto    => 'all',
        iniface  => "$vmaccess_interface",
        outiface => "venet0",
      }
      
    }

}
