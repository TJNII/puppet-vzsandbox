# hypervisor configuration manifest
class vzsandbox::hypervisor (
  $manage_firewall = true,
  $control_server  = undef,
  ) {

    class { "vzsandbox::hypervisor::common":
      manage_firewall => $manage_firewall,
    }

    class { "vzsandbox::hypervisor::api":
      manage_firewall => $manage_firewall,
      control_server  => $control_server,
    }

    class { "vzsandbox::hypervisor::clean":
    }
}
