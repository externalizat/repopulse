"""Observable outcomes of every built-in analysis family."""

import pytest

from repopulse.checks import documentation as docs
from repopulse.checks import engineering as eng
from repopulse.checks import maintenance as maint
from repopulse.checks import security as sec


def test_missing_readme(context):
    assert docs.readme(context({}))[0].message == "Root README missing"


def test_short_readme(context):
    assert len(docs.readme(context({"README.md": "# Toy"}))) == 2


def test_readme_case(context):
    assert not docs.readme(context({"ReadMe.md": "## Features\n" + "useful " * 80}))


def test_onboarding_missing(context):
    assert len(docs.onboarding(context({}))) == 2


def test_onboarding_in_docs(context):
    assert not docs.onboarding(context({"docs/start.md": "Installation\nQuick start"}))


def test_license_nested_dependency_not_counted(context):
    assert docs.presence(context({"lib/LICENSE": "MIT"}), ("license",), "license")


def test_community_github_location(context):
    assert not docs.presence(
        context({".github/CONTRIBUTING.md": "Guide"}), ("contributing",), "guide"
    )


def test_broken_link_line(context):
    findings = docs.links(context({"README.md": "# Test\n[missing](no.md)"}))
    assert len(findings) == 1 and findings[0].line == 2


def test_links_existing_encoded_and_external(context):
    ctx = context(
        {
            "README.md": "[ok](docs/a%20b.md#heading) [web](https://example.com) [anchor](#x)",
            "docs/a b.md": "# heading",
        }
    )
    assert not docs.links(ctx)


def test_reference_link(context):
    assert len(docs.links(context({"README.md": "[guide][g]\n[g]: missing.md"}))) == 1


def test_code_links_ignored(context):
    assert not docs.links(context({"README.md": "```md\n[x](missing)\n```\n`[y](missing)`"}))


def test_link_escape(context):
    assert "escapes" in docs.links(context({"README.md": "[x](../../outside)"}))[0].message


@pytest.mark.parametrize("name", ["tests/test_app.py", "app_test.go", "src/app.test.ts"])
def test_test_conventions(context, name):
    assert not eng.tests(context({name: "test code"}))


def test_empty_test_directory_not_enough(context):
    assert eng.tests(context({"tests/README.md": "No tests yet"}))


def test_ci(context):
    assert not eng.ci(context({".github/workflows/check.yml": "name: CI"}))
    assert eng.ci(context({".github/workflows/README.md": "CI"}))


def test_dependency_presence(context):
    assert not eng.dependencies(context({"Cargo.toml": ""}))
    assert eng.dependencies(context({}))


def test_python_pins(context):
    findings = eng.pins(context({"requirements.txt": "foo==1.2.3\nbar>=2\nbaz==1.*\n# comment"}))
    assert findings[0].message.startswith("2 dependencies")


def test_python_extras_pins(context):
    assert not eng.pins(context({"requirements.txt": 'foo[extra]==1.2; python_version > "3.10"'}))


def test_npm_pins(context):
    assert eng.pins(context({"package.json": '{"dependencies":{"a":"^1.0.0","b":"2.0.0"}}'}))[
        0
    ].message.startswith("1 dependencies")


def test_bad_manifest(context):
    assert "Cannot parse" in eng.pins(context({"package.json": "{"}))[0].message


def test_todos_grouped(context):
    findings = maint.todos(context({"src/a.py": "# TODO\n# TODO\n# HACK", "src/b.py": "# FIXME"}))
    assert len(findings) == 2
    assert "TODO: 2" in findings[0].message


def test_large_source_boundary(context):
    assert not maint.large_files(context({"x.py": "a\nb"}, max_source_lines=2))
    assert maint.large_files(context({"x.py": "a\nb\nc"}, max_source_lines=2))


def test_structure_clutter(context):
    assert maint.structure(context({f"a{i}.py": "" for i in range(11)}))


def test_env_required(context):
    assert sec.env_example(context({"app.py": 'os.getenv("DATABASE_URL")'}))
    assert not sec.env_example(context({"app.py": 'os.getenv("HOME")'}))


def test_env_drift(context):
    findings = sec.env_drift(
        context(
            {
                "app.ts": 'process.env.API_URL; process.env["PORT"]',
                ".env.example": "API_URL=\nOLD=\n",
            }
        )
    )
    assert len(findings) == 2
    assert "PORT" in findings[0].message
    assert findings[1].severity == "info"


def test_secret_redaction(context):
    token = "ghp_" + "aB34" * 9
    findings = sec.secrets(context({"app.py": f'\nTOKEN="{token}"'}))
    assert findings[0].line == 2
    assert findings[0].snippet == "[REDACTED]"
    assert token not in findings[0].model_dump_json()


def test_private_key(context):
    assert sec.secrets(context({"key.pem": "-----BEGIN " + "PRIVATE KEY-----"}))


def test_placeholder_not_secret(context):
    assert not sec.secrets(context({".env.example": 'api_key="your_example_key_12345678"'}))
