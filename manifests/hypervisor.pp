# hypervisor configuration manifest
class vzsandbox::hypervisor (
  $manage_firewall = true,
  $control_server  = undef,
  # TODO: Combine in openvz class and calculate from subnet
  $subnet_prefix,
  $min_containers,
  $max_containers,
  $vmaccess_interface = $interfaces_internal,
  $control_interface = $interfaces_internal,
  ) {

    class { "vzsandbox::hypervisor::common":
      manage_firewall => $manage_firewall,
      subnet_prefix   => $subnet_prefix,
      min_containers  => $min_containers,
      max_containers  => $max_containers,
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
      
      
      firewall { "020 Allow openvz inbound traffic":
        chain    => 'FORWARD',
        action   => accept,
        proto    => 'all',
        iniface  => "$vmaccess_interface",
        outiface => "venet0",
      }
      
    }

}
