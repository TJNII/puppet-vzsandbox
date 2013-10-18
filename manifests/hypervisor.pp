# hypervisor configuration manifest
class vzsandbox::hypervisor (
  $manage_firewall = true,
  $control_server  = undef,
  # TODO: Combine in openvz class and calculate from subnet
  $subnet_prefix,
  $max_containers,
  ) {

    class { "vzsandbox::hypervisor::common":
      manage_firewall => $manage_firewall,
      subnet_prefix   => $subnet_prefix,
      max_containers  => $max_containers,
    }

    class { "vzsandbox::hypervisor::api":
      manage_firewall => $manage_firewall,
      control_server  => $control_server,
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
}
