# hypervisor configuration manifest
# API files
class vzsandbox::common::api {
  # packages moved to the commonpackages class
  include commonpackages::python::yaml
  include commonpackages::python::flask-restful
}
