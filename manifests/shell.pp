# shell: Provide files for frontend login server shell
class vzsandbox::shell (
  $loadbalancer_host = "127.0.0.1",
  )
{
  # TODO: Fix PyYAML collission
  package { 'pexpect':
    ensure   => installed,
  }
  
  file { "/usr/local/bin/vzsandbox-shell.py":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 755,
    source  => "puppet:///modules/vzsandbox/shell/usr/local/bin/vzsandbox-shell.py",
    require => Package["PyYAML"],
  }
  
  file { "/etc/vzsandbox-shell.yaml":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 644,
    content => template("vzsandbox/shell/etc/vzsandbox-shell.yaml.erb"),
  }
  
  file { "/etc/vzsandbox_keys":
    ensure  => directory,
    purge   => true,
    recurse => true,
    force   => true,
    owner   => root,
    group   => root,
    mode    => 644,
    source  => "puppet:///modules/vzsandbox/shell/etc/vzsandbox_keys",
  }
  
  file { "/etc/shells":
    ensure  => file,
    source  => "puppet:///modules/vzsandbox/shell/etc/shells",
  }
  
  group { 'vzsusers':
    ensure => "present",
    system => true,
  }

  file { "/vzsandbox-shell-tmp":
    ensure  => directory,
    owner   => root,
    group   => vzsusers,
    mode    => 770,
    require => Group['vzsusers'],
  }
}
                  
