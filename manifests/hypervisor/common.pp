# hypervisor configuration manifest
# Common files
class vzsandbox::hypervisor::common (
  $manage_firewall = true,
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
    source  => "puppet:///modules/vzsandbox/hypervisor/etc/vzsandbox.yaml",
  }
}
