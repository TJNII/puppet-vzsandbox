# hypervisor configuration manifest
class vzsandbox::hypervisor (
  $manage_firewall = true,
  $control_server  = undef,
  ) {
  # the API requires flask-restful which is installed by pip which is provided by epel
  include "repoconfig::epel"

  package { ['python-pip', 'PyYAML']:
    ensure   => installed,
    require  => Class['repoconfig::epel'],
  }
  
  # Install flask-restful and its deps to enable the API
  package { ['flask-restful', 'six']:
    ensure   => installed,
    provider => 'pip',
    require  => Package['python-pip'],
  }

  file { "/usr/local/bin/vzsandbox-api.py":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 750,
    source  => "puppet:///modules/vzsandbox/hypervisor/usr/local/bin/vzsandbox-api.py",
  }

  file { "/usr/local/bin/vzsandboxlib.py":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 640,
    source  => "puppet:///modules/vzsandbox/hypervisor/usr/local/bin/vzsandboxlib.py",
  }

  file { "/usr/local/bin/vzsandbox-api-daemon.sh":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 750,
    source  => "puppet:///modules/vzsandbox/hypervisor/usr/local/bin/vzsandbox-api-daemon.sh",
  }

  file { "/etc/vzsandbox-api.yaml":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 644,
    source  => "puppet:///modules/vzsandbox/hypervisor/etc/vzsandbox-api.yaml",
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
                         File["/etc/vzsandbox-api.yaml"],
                         File["/etc/sysconfig/vzsandbox-api"],
                         File["/etc/init.d/vzsandbox-api"],
                         ],
  }

  if $manage_firewall == true {
    include firewall-config::base
    
    firewall { '99 allow 5000/TCP for vzsandboxapi from control server':
      state => ['NEW'],
      dport => '5000',
      proto => 'tcp',
      source => "$control_server",
      iniface => "$interfaces_internal",
      action => accept,
    }
  }
}
