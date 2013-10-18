# hypervisor configuration manifest
# Common files
class vzsandbox::hypervisor::clean  {
  file { "/usr/local/bin/vzsandbox-clean.py":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 750,
    source  => "puppet:///modules/vzsandbox/hypervisor/usr/local/bin/vzsandbox-clean.py",
  }

  file { "/etc/cron.d/vzsandbox-cleanup":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 644,
    source  => "puppet:///modules/vzsandbox/hypervisor/etc/cron.d/vzsandbox-cleanup",
  }
}
