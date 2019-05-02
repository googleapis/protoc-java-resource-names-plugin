load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def com_google_protoc_java_resource_names_plugin_repositories(
    omit_pypi_six = False,
    omit_com_google_protobuf = False,
    omit_pypi_py_yaml = False,
    omit_pypi_pystache = False,
    omit_pypi_ply = False):
    if not omit_pypi_six:
        pypi_six()
    if not omit_com_google_protobuf:
        com_google_protobuf()
    if not omit_pypi_py_yaml:
        pypi_py_yaml()
    if not omit_pypi_pystache:
        pypi_pystache()
    if not omit_pypi_ply:
        pypi_ply()

def com_google_protobuf():
    _protobuf_version = "3.7.1"

    http_archive(
        name = "com_google_protobuf",
        urls = ["https://github.com/protocolbuffers/protobuf/archive/v%s.zip" % _protobuf_version],
        strip_prefix = "protobuf-%s" % _protobuf_version
    )

    http_archive(
        name = "bazel_skylib",
        sha256 = "bbccf674aa441c266df9894182d80de104cabd19be98be002f6d478aaa31574d",
        strip_prefix = "bazel-skylib-2169ae1c374aab4a09aa90e65efe1a3aad4e279b",
        urls = ["https://github.com/bazelbuild/bazel-skylib/archive/2169ae1c374aab4a09aa90e65efe1a3aad4e279b.tar.gz"],
    )

    http_archive(
        name = "net_zlib",
        build_file = "@com_google_protobuf//:third_party/zlib.BUILD",
        sha256 = "c3e5e9fdd5004dcb542feda5ee4f0ff0744628baf8ed2dd5d66f8ca1197cb1a1",
        strip_prefix = "zlib-1.2.11",
        urls = ["https://zlib.net/zlib-1.2.11.tar.gz"]
    )

_DEFAULT_PY_BUILD_FILE = """
py_library(
    name = "lib",
    srcs = glob(["**/*.py"]),
    visibility = ["//visibility:public"],
)
"""

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

def pypi_py_yaml():
    http_archive(
        name = "pypi_py_yaml",
        url = ("https://files.pythonhosted.org/packages/4a/85/db5a2df477072b2902b0eb892feb37d88ac635d36245a72a6a69b23b383a/PyYAML-3.12.tar.gz"),
        strip_prefix = "PyYAML-3.12/lib",
        build_file_content = _DEFAULT_PY_BUILD_FILE,
    )

def pypi_pystache():
    http_archive(
        name = "pypi_pystache",
        url = ("https://files.pythonhosted.org/packages/d6/fd/eb8c212053addd941cc90baac307c00ac246ac3fce7166b86434c6eae963/pystache-0.5.4.tar.gz"),
        strip_prefix = "pystache-0.5.4",
        build_file_content = _DEFAULT_PY_BUILD_FILE,
    )

def pypi_ply():
    http_archive(
        name = "pypi_ply",
        url = ("https://files.pythonhosted.org/packages/96/e0/430fcdb6b3ef1ae534d231397bee7e9304be14a47a267e82ebcb3323d0b5/ply-3.8.tar.gz"),
        strip_prefix = "ply-3.8",
        build_file_content = _DEFAULT_PY_BUILD_FILE,
    )
