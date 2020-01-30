load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

_DEFAULT_PY_BUILD_FILE = """
py_library(
    name = "lib",
    srcs = glob(["**/*.py"]),
    visibility = ["//visibility:public"],
)
"""

_DEFAULT_PY3_BUILD_FILE = """
py_library(
    name = "lib",
    srcs = glob(["**/*.py"]),
    visibility = ["//visibility:public"],
    srcs_version = "PY3",
)
"""

def com_google_protoc_java_resource_names_plugin_repositories():
    _protobuf_version = "3.7.1"
    _protobuf_version_in_link = "v%s" % _protobuf_version
    _maybe(
        http_archive,
        name = "com_google_protobuf",
        urls = ["https://github.com/protocolbuffers/protobuf/archive/%s.zip" % _protobuf_version_in_link],
        strip_prefix = "protobuf-%s" % _protobuf_version,
    )

    _maybe(
        http_archive,
        name = "bazel_skylib",
        sha256 = "bbccf674aa441c266df9894182d80de104cabd19be98be002f6d478aaa31574d",
        strip_prefix = "bazel-skylib-2169ae1c374aab4a09aa90e65efe1a3aad4e279b",
        urls = ["https://github.com/bazelbuild/bazel-skylib/archive/2169ae1c374aab4a09aa90e65efe1a3aad4e279b.tar.gz"],
    )

    _maybe(
        http_archive,
        name = "net_zlib",
        build_file = "@com_google_protobuf//:third_party/zlib.BUILD",
        sha256 = "c3e5e9fdd5004dcb542feda5ee4f0ff0744628baf8ed2dd5d66f8ca1197cb1a1",
        strip_prefix = "zlib-1.2.11",
        urls = ["https://zlib.net/zlib-1.2.11.tar.gz"],
    )

    _maybe(
        native.bind,
        name = "zlib",
        actual = "@net_zlib//:zlib",
    )

    _maybe(
        http_archive,
        name = "pypi_six",
        build_file = "@com_google_protobuf//:six.BUILD",
        urls = ["https://pypi.python.org/packages/source/s/six/six-1.10.0.tar.gz"],
    )

    _maybe(
        native.bind,
        name = "six",
        actual = "@pypi_six//:six",
    )

    _maybe(
        http_archive,
        name = "pypi_py_yaml",
        url = ("https://files.pythonhosted.org/packages/4a/85/db5a2df477072b2902b0eb892feb37d88ac635d36245a72a6a69b23b383a/PyYAML-3.12.tar.gz"),
        strip_prefix = "PyYAML-3.12/lib3",
        build_file_content = _DEFAULT_PY3_BUILD_FILE,
    )

    _maybe(
        http_archive,
        name = "pypi_ply",
        url = ("https://files.pythonhosted.org/packages/96/e0/430fcdb6b3ef1ae534d231397bee7e9304be14a47a267e82ebcb3323d0b5/ply-3.8.tar.gz"),
        strip_prefix = "ply-3.8",
        build_file_content = _DEFAULT_PY_BUILD_FILE,
    )

    _maybe(
        http_archive,
        name = "pypi_chevron",
        url = ("https://files.pythonhosted.org/packages/2a/01/efb4ef22ea9b6377392bd5d6af5acbd218100ee7379dbcd8a7322585710d/chevron-0.13.1.tar.gz"),
        strip_prefix = "chevron-0.13.1",
        build_file_content = _DEFAULT_PY_BUILD_FILE,
    )

def _maybe(repo_rule, name, strip_repo_prefix = "", **kwargs):
    if not name.startswith(strip_repo_prefix):
        return
    repo_name = name[len(strip_repo_prefix):]
    if repo_name in native.existing_rules():
        return
    repo_rule(name = repo_name, **kwargs)
