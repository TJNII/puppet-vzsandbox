# hypervisor configuration manifest
# Common files
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
