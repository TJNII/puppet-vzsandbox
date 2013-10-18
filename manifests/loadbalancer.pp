# hypervisor configuration manifest
class vzsandbox::loadbalancer (
  $manage_firewall = true,
  $lb_hypervisors,  
  ) {
    class { 'vzsandbox::loadbalancer::api':
      manage_firewall => $manage_firewall,
      lb_hypervisors  => $lb_hypervisors,
    }
}
