from __future__ import annotations

import sys
from pathlib import Path

import pytest


class CaseCounter:
	def __init__(self) -> None:
		self.total = 0
		self.passed = 0
		self.failed = 0

	def pytest_runtest_logreport(self, report) -> None:
		if report.when != "call":
			return
		self.total += 1
		if report.passed:
			self.passed += 1
		elif report.failed:
			self.failed += 1


def _collect_api_test_files(api_test_dir: Path) -> list[Path]:
	return sorted(
		path
		for path in api_test_dir.glob("test_*.py")
		if path.is_file() and path.name != "test_all.py"
	)


def main() -> int:
	project_root = Path(__file__).resolve().parents[2]
	if str(project_root) not in sys.path:
		sys.path.insert(0, str(project_root))

	api_test_dir = Path(__file__).resolve().parent
	test_files = _collect_api_test_files(api_test_dir)

	if not test_files:
		print("[INFO] 未找到可执行的 API 测试文件。")
		return 0

	print("[INFO] 即将执行以下 API 测试文件：")
	for file_path in test_files:
		print(f"  - {file_path.name}")

	results: list[tuple[str, int, int, int, int]] = []
	total_cases = 0
	total_passed = 0
	total_failed = 0
	for file_path in test_files:
		print("\n" + "=" * 80)
		print(f"[RUN] {file_path.name}")
		print("=" * 80)

		counter = CaseCounter()
		exit_code = pytest.main([str(file_path), "-s", "-q"], plugins=[counter])
		results.append((file_path.name, int(exit_code), counter.total, counter.passed, counter.failed))
		total_cases += counter.total
		total_passed += counter.passed
		total_failed += counter.failed

	print("\n" + "#" * 80)
	print("[SUMMARY] API 测试执行结果")
	print("#" * 80)

	failed_files = 0
	for file_name, code, case_total, case_passed, case_failed in results:
		status = "PASS" if code == 0 else "FAIL"
		print(
			f"[{status}] {file_name} (exit_code={code}, total={case_total}, passed={case_passed}, failed={case_failed})"
		)
		if code != 0:
			failed_files += 1

	print("-" * 80)
	print(f"总用例数: {total_cases}")
	print(f"成功用例数: {total_passed}")
	print(f"失败用例数: {total_failed}")

	return 0 if failed_files == 0 else 1


if __name__ == "__main__":
	raise SystemExit(main())

