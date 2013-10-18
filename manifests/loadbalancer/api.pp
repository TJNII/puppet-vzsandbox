# hypervisor configuration manifest
# API files
class vzsandbox::loadbalancer::api (
  $manage_firewall = true,
  $lb_hypervisors,
  ) {
  # the API requires flask-restful which is installed by pip which is provided by epel
  include "repoconfig::epel"
  include "vzsandbox::common::api"

  file { "/etc/vzsandbox-lb.yaml":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 644,
    content => template("vzsandbox/lb/etc/vzsandbox-lb.yaml.erb"),
  }                        
    
  file { "/usr/local/bin/vzsandbox-lbapi.py":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 750,
    source  => "puppet:///modules/vzsandbox/lb/usr/local/bin/vzsandbox-lbapi.py",
    require => Class["vzsandbox::common::api"],
  }

  file { "/usr/local/bin/vzsandbox-lbapi-daemon.sh":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 750,
    source  => "puppet:///modules/vzsandbox/lb/usr/local/bin/vzsandbox-lbapi-daemon.sh",
  }

  file { "/etc/sysconfig/vzsandbox-lbapi":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 644,
    source  => "puppet:///modules/vzsandbox/lb/etc/sysconfig/vzsandbox-lbapi",
  }

  file { "/etc/init.d/vzsandbox-lbapi":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 754,
    source  => "puppet:///modules/vzsandbox/lb/etc/init.d/vzsandbox-lbapi",
  }

  service { 'vzsandbox-lbapi':
        ensure    => running,
        enable    => true,
        subscribe   => [ File["/usr/local/bin/vzsandbox-lbapi.py"],
                         File["/usr/local/bin/vzsandbox-lbapi-daemon.sh"],
                         File["/etc/vzsandbox-lb.yaml"],
                         File["/etc/sysconfig/vzsandbox-lbapi"],
                         File["/etc/init.d/vzsandbox-lbapi"],
                         ],
  }

#  if $manage_firewall == true {
#    include firewall-config::base
#    
#    firewall { '99 allow 5000/TCP for vzsandboxlbapi from control server':
#      state => ['NEW'],
#      dport => '5000',
#      proto => 'tcp',
#      source => "$control_server",
#      iniface => "$interfaces_internal",
#      action => accept,
#    }
#  }
}
