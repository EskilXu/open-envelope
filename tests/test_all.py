import json, pathlib, subprocess, sys
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "compat/hdeb/tools"))
import jepx_to_hdeb, kclkvl_check

def _hdeb_validator():
    block = json.load(open(ROOT/"compat/hdeb/schema/hdeb-0.1.schema.json", encoding="utf-8"))
    doc = json.load(open(ROOT/"compat/hdeb/schema/hdeb-document-0.1.schema.json", encoding="utf-8"))
    reg = Registry().with_resources([(block["$id"], Resource.from_contents(block)), (doc["$id"], Resource.from_contents(doc))])
    return Draft202012Validator(doc, registry=reg, format_checker=Draft202012Validator.FORMAT_CHECKER)

def test_envelope_schema_and_examples():
    s = json.load(open(ROOT/"envelope/envelope-0.0.3.schema.json", encoding="utf-8"))
    Draft202012Validator.check_schema(s)
    v = Draft202012Validator(s, format_checker=Draft202012Validator.FORMAT_CHECKER)
    for f in (ROOT/"envelope").glob("example_*.json"):
        v.validate(json.load(open(f, encoding="utf-8")))

def test_registry_yaml_parses():
    import yaml
    y = yaml.safe_load(open(ROOT/"registry/standards.yaml", encoding="utf-8"))
    assert len(y["standards"]) >= 30 and all("maps_to" in s for s in y["standards"])
    yaml.safe_load(open(ROOT/"registry/profiles/example.mapping.yaml", encoding="utf-8"))

def test_hdeb_compat_schema_and_examples():
    v = _hdeb_validator()
    for f in (ROOT/"compat/hdeb/examples").glob("*.json"):
        errs = list(v.iter_errors(json.load(open(f, encoding="utf-8")))); assert not errs, (f.name, [e.message for e in errs][:3])

def test_jepx_converter_on_fixture():
    text = open(ROOT/"tests/fixtures/jepx_spot_summary_2026-04-01.csv", encoding="utf-8-sig").read()
    doc = jepx_to_hdeb.convert(text, "fixture", "2026-09-04T00:00:00+00:00")
    assert len(doc["blocks"]) == 48 * 10
    sysblk = [b for b in doc["blocks"] if b["hierarchy_level"] == "system"]
    assert sysblk[0]["window"]["start"] == "2026-04-01T00:00:00+09:00" and sysblk[19]["price"]["value"] == 20.53
    assert not list(_hdeb_validator().iter_errors(doc))

def test_kcl_kvl_pass_and_fail():
    ok, v = kclkvl_check.check(json.load(open(ROOT/"compat/hdeb/examples/site_schedule_pass.json"))); assert ok, v
    ok, v = kclkvl_check.check(json.load(open(ROOT/"compat/hdeb/examples/site_schedule_fail.json"))); assert not ok and v["kvl"] and v["limits"]

def test_cli_exit_codes():
    py = sys.executable; t = ROOT/"compat/hdeb/tools/kclkvl_check.py"; e = ROOT/"compat/hdeb/examples"
    assert subprocess.run([py, t, e/"site_schedule_pass.json"], capture_output=True).returncode == 0
    assert subprocess.run([py, t, e/"site_schedule_fail.json"], capture_output=True).returncode == 1
