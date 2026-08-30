from pathlib import Path

module_path = Path("src/kodepoia/tuning/gguf.py")
test_path = Path("tests/test_gguf_conversion_r15_12.py")
module = module_path.read_text(encoding="utf-8")
tests = test_path.read_text(encoding="utf-8")

old_module = '''        elif value.startswith("--"):
            shape.append(value)
        elif index > 0 and argv[index - 1] in {"--outtype"}:
            shape.append(value)
'''
new_module = '''        elif value.startswith("--") or (index > 0 and argv[index - 1] == "--outtype"):
            shape.append(value)
'''
if module.count(old_module) != 1:
    raise SystemExit("R15.12 module Ruff fix cardinality mismatch")
module = module.replace(old_module, new_module)

old_test = '''        if "--outfile" in argv:
            output = Path(argv[argv.index("--outfile") + 1])
        else:
            output = Path(argv[-2])
'''
new_test = '''        output = Path(argv[argv.index("--outfile") + 1]) if "--outfile" in argv else Path(argv[-2])
'''
if tests.count(old_test) != 2:
    raise SystemExit("R15.12 test Ruff fix cardinality mismatch")
tests = tests.replace(old_test, new_test)

module_path.write_text(module, encoding="utf-8")
test_path.write_text(tests, encoding="utf-8")
