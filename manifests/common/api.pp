# hypervisor configuration manifest
# API files
class vzsandbox::common::api {
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
}
