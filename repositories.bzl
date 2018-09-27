load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def com_google_protoc_java_resource_names_plugin_repositories(
    omit_com_google_protobuf = False,
    omit_pypi_py_yaml = False,
    omit_pypi_pystache = False,
    omit_pypi_six = False):
    if not omit_com_google_protobuf:
        com_google_protobuf()
    if not omit_pypi_py_yaml:
        pypi_py_yaml()
    if not omit_pypi_pystache:
        pypi_pystache()
    if not omit_pypi_six:
        pypi_six()

def com_google_protobuf():
    native.git_repository(
        name = "com_google_protobuf",
        remote = "https://github.com/google/protobuf.git",
        tag = "v3.6.1",
    )

def pypi_py_yaml():
    http_archive(
        name = "pypi_py_yaml",
        url = ("https://files.pythonhosted.org/packages/4a/85/db5a2df477072b2902b0eb892feb37d88ac635d36245a72a6a69b23b383a/PyYAML-3.12.tar.gz"),
        strip_prefix = "PyYAML-3.12/lib/yaml",
        build_file_content = """
py_library(
    name = "lib",
    srcs = glob(["*.py"]),
    visibility = ["//visibility:public"],
)
""",
    )

def pypi_pystache():
    http_archive(
        name = "pypi_pystache",
        url = ("https://files.pythonhosted.org/packages/d6/fd/eb8c212053addd941cc90baac307c00ac246ac3fce7166b86434c6eae963/pystache-0.5.4.tar.gz"),
        strip_prefix = "pystache-0.5.4/pystache",
        build_file_content = """
py_library(
    name = "lib",
    srcs = glob(["**/*.py"]),
    visibility = ["//visibility:public"],
)
""",
    )

def pypi_six():
    http_archive(
        name = "pypi_six",
        build_file = "@com_google_protobuf//:six.BUILD",
        urls = ["https://pypi.python.org/packages/source/s/six/six-1.10.0.tar.gz"],
    )

    native.bind(
        name = "six",
        actual = "@pypi_six//:six"
    )
