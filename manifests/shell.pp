# shell: Provide files for frontend login server shell

# Copyright 2013 Tom Noonan II (TJNII)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

class vzsandbox::shell (
  $loadbalancer_host = "127.0.0.1",
  )
{
  include commonpackages::python::yaml
  include commonpackages::python::pexpect
  
  file { "/usr/local/bin/vzsandbox-shell.py":
    ensure  => file,
    owner   => root,
    group   => root,
    mode    => 755,
    source  => "puppet:///modules/vzsandbox/shell/usr/local/bin/vzsandbox-shell.py",
    require => [ Class['commonpackages::python::yaml'],
                 Class['commonpackages::python::pexpect'],
                 ],
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
                  
