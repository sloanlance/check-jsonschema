from unittest import mock

import pytest
from click.testing import CliRunner

from check_jsonschema import main as cli_main
from check_jsonschema.cli import ParseResult, SchemaLoadingMode


@pytest.fixture
def mock_parse_result():
    args = ParseResult()
    with mock.patch("check_jsonschema.cli.ParseResult.ensure") as m:
        m.return_value = args
        yield args


@pytest.fixture(autouse=True)
def mock_cli_exec():
    with mock.patch("check_jsonschema.cli.execute") as m:
        yield m


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


@pytest.mark.parametrize(
    "schemafile,builtin_schema,check_metaschema,expect_mode",
    [
        ("foo.json", None, False, SchemaLoadingMode.filepath),
        (None, "foo", False, SchemaLoadingMode.builtin),
        (None, None, True, SchemaLoadingMode.metaschema),
    ],
)
def test_parse_result_set_schema(
    schemafile, builtin_schema, check_metaschema, expect_mode
):
    args = ParseResult()
    # access prior to setting raises an error
    with pytest.raises(ValueError):
        args.schema_mode
    with pytest.raises(ValueError):
        args.schema_path
    args.set_schema(schemafile, builtin_schema, check_metaschema)
    assert args.schema_mode == expect_mode
    if schemafile:
        assert args.schema_path == schemafile
    if builtin_schema:
        assert args.schema_path == builtin_schema
    if check_metaschema:
        with pytest.raises(ValueError):
            args.schema_path


def test_requires_some_args(runner):
    result = runner.invoke(cli_main, [])
    assert result.exit_code == 2


def test_schemafile_and_instancefile(runner, mock_parse_result):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert mock_parse_result.schema_mode == SchemaLoadingMode.filepath
    assert mock_parse_result.schema_path == "schema.json"
    assert mock_parse_result.instancefiles == ("foo.json",)


def test_requires_at_least_one_instancefile(runner):
    result = runner.invoke(cli_main, ["--schemafile", "schema.json"])
    assert result.exit_code == 2


def test_requires_schemafile(runner):
    result = runner.invoke(cli_main, ["foo.json"])
    assert result.exit_code == 2


def test_no_cache_defaults_false(runner, mock_parse_result):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert mock_parse_result.disable_cache is False


def test_no_cache_flag_is_true(runner, mock_parse_result):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json", "--no-cache"])
    assert mock_parse_result.disable_cache is True


@pytest.mark.parametrize(
    "cmd_args",
    [
        [
            "--schemafile",
            "x.json",
            "--builtin-schema",
            "vendor.travis",
            "foo.json",
        ],
        [
            "--schemafile",
            "x.json",
            "--builtin-schema",
            "vendor.travis",
            "--check-metaschema",
            "foo.json",
        ],
        [
            "--schemafile",
            "x.json",
            "--check-metaschema",
            "foo.json",
        ],
        [
            "--builtin-schema",
            "vendor.travis",
            "--check-metaschema",
            "foo.json",
        ],
    ],
)
def test_mutex_schema_opts(runner, cmd_args):
    result = runner.invoke(cli_main, cmd_args)
    assert result.exit_code == 2
    assert "are mutually exclusive" in result.stderr
