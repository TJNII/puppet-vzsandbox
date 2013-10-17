# hypervisor configuration manifest
class vzsandbox::hypervisor {
  # the API requires flask-restful which is installed by pip which is provided by epel
  include "repoconfig::epel"

  package {'python-pip':
    ensure   => installed,
    require  => Class['repoconfig::epel'],
  }
  
  # Install flask-restful and its deps to enable the API
  package { ['flask-restful', 'six']:
    ensure   => installed,
    provider => 'pip',
    require  => Package['python-pip'],
  }
}
