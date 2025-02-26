@echo off
echo "----------black-report-------------" > "linters_report_%1.txt"
black --diff %1 >> "linters_report_%1.txt" 2>&1

echo "----------flake8-report-------------" >> "linters_report_%1.txt"
flake8 %1 >> "linters_report_%1.txt" 2>&1

echo "----------pyflakes-report-------------" >> "linters_report_%1.txt"
pyflakes %1 >> "linters_report_%1.txt" 2>&1

echo "----------pycodestyle-report-------------" >> "linters_report_%1.txt"
pycodestyle %1 >> "linters_report_%1.txt" 2>&1

echo "----------pylint-report-------------" >> "linters_report_%1.txt"
pylint %1 >> "linters_report_%1.txt" 2>&1

echo "----------mypy-report-------------" >> "linters_report_%1.txt"
mypy %1 >> "linters_report_%1.txt" 2>&1

echo "----------radon-report-------------" >> "linters_report_%1.txt"
echo "----------radon-cc-check-----------" >> "linters_report_%1.txt"
radon cc %1 >> "linters_report_%1.txt" 2>&1

echo "----------radon-mi-check-----------" >> "linters_report_%1.txt"
radon mi %1 >> "linters_report_%1.txt" 2>&1

echo "----------radon-raw-check-----------" >> "linters_report_%1.txt"
radon raw %1 >> "linters_report_%1.txt" 2>&1

echo "----------radon-hal-check-----------" >> "linters_report_%1.txt"
radon hal %1 >> "linters_report_%1.txt" 2>&1

echo "----------bandit-report-------------" >> "linters_report_%1.txt"
bandit %1 >> "linters_report_%1.txt" 2>&1
echo "Codestyle and efficiency check has been completed. Check the report in directory."