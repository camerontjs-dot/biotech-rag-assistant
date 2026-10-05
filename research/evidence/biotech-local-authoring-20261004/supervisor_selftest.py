#!/usr/bin/env python3
"""Offline self-test for supervisor.py. No model is loaded and nothing is generated.

Stand-in child processes replace the wrapper. Provider access is limited to the read-only
process list. Every abort rule must trip and every failure must stay a failure.
"""

import copy
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import supervisor as sup  # noqa: E402

BUDGET = json.loads((Path(__file__).resolve().parent / "budget.json").read_text())
HEALTHY = {"free_percentage": 70, "pressure_level": 1, "swap_used_mib": 100.0, "battery_percentage": 90,
           "on_ac_power": False, "thermal": None, "models": [], "at_utc": "t"}


def snap(**changes):
    return {**copy.deepcopy(HEALTHY), **changes}


class Parsers(unittest.TestCase):
    def test_probe_text(self):
        self.assertEqual(sup.parse_free_percentage("x\nSystem-wide memory free percentage: 62%\n"), 62)
        self.assertIsNone(sup.parse_free_percentage("no figure"))
        self.assertEqual(sup.parse_swap_used_mib("total = 1024.00M  used = 164.50M  free = 1M"), 164.5)
        self.assertEqual(sup.parse_swap_used_mib("used = 2.00G"), 2048.0)
        self.assertEqual(sup.parse_battery("Now drawing from 'Battery Power'\n 100%; discharging"), (100, False))
        self.assertEqual(sup.parse_battery("Now drawing from 'AC Power'\n 80%; charging"), (80, True))


class StartLimits(unittest.TestCase):
    def test_healthy_start(self):
        self.assertEqual(sup.start_blockers(snap(), BUDGET), [])

    def test_each_start_blocker(self):
        cases = [snap(models=[{"name": "other", "digest": "d", "size": 1, "context_length": 1}]),
                 snap(models=None), snap(free_percentage=59), snap(free_percentage=None),
                 snap(pressure_level=2), snap(swap_used_mib=768.0), snap(swap_used_mib=None),
                 snap(battery_percentage=34), snap(battery_percentage=None), snap(on_ac_power=None)]
        for case in cases:
            self.assertTrue(sup.start_blockers(case, BUDGET), case)

    def test_ac_power_ignores_battery_floor(self):
        self.assertEqual(sup.start_blockers(snap(on_ac_power=True, battery_percentage=5), BUDGET), [])


class AbortRules(unittest.TestCase):
    def check_all(self, *snaps):
        watch = sup.Watch(BUDGET, snap())
        trips = []
        for item in snaps:
            trips = watch.check(item)
        return trips

    def test_healthy_never_trips(self):
        self.assertEqual(self.check_all(snap(), snap(), snap()), [])

    def test_single_low_free_sample_is_not_enough_but_two_are(self):
        self.assertEqual(self.check_all(snap(free_percentage=10)), [])
        self.assertTrue(self.check_all(snap(free_percentage=10), snap(free_percentage=10)))
        self.assertEqual(self.check_all(snap(free_percentage=10), snap(), snap(free_percentage=10)), [])

    def test_critical_pressure_trips_at_once_and_warn_needs_three(self):
        self.assertTrue(self.check_all(snap(pressure_level=4)))
        self.assertEqual(self.check_all(snap(pressure_level=2), snap(pressure_level=2)), [])
        self.assertTrue(self.check_all(*[snap(pressure_level=2)] * 3))

    def test_swap_growth_resident_context_battery_and_probe_failure(self):
        self.assertTrue(self.check_all(snap(swap_used_mib=100.0 + 256)))
        big = {"name": "m", "digest": "d", "size": 12884901888, "context_length": 40960}
        self.assertTrue(self.check_all(snap(models=[big])))
        wide = {"name": "m", "digest": "d", "size": 1, "context_length": 40961}
        self.assertTrue(self.check_all(snap(models=[wide])))
        self.assertTrue(self.check_all(snap(battery_percentage=11)))
        self.assertEqual(self.check_all(snap(battery_percentage=11, on_ac_power=True)), [])
        broken = snap(free_percentage=None)
        self.assertTrue(self.check_all(broken, broken, broken))


class Launch(unittest.TestCase):
    """Real child processes. The wrapper is replaced; the supervision logic is not."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.args = SimpleNamespace(python=sys.executable, root=base, run_dir=base / "run",
                                    log_dir=base / "logs", private_dir=base / "private")
        (self.args.run_dir / "calls").mkdir(parents=True)
        self.args.log_dir.mkdir()
        self.fake_log = base / "server.log"
        self.fake_log.write_bytes(b"[GIN] earlier unrelated line\n")
        self.budget = copy.deepcopy(BUDGET)
        self.budget["context_evidence"]["provider_log"] = str(self.fake_log)
        self.budget["limits"]["sample_interval_seconds"] = 1
        self.budget["limits"]["start_requires"].update(min_free_percentage=0, max_swap_used_mib=10 ** 9,
                                                       min_battery_percentage_when_on_battery=0)
        self.real_build = sup.build_command
        self.real_sample = sup.sample
        sup.sample = lambda budget: {**self.real_sample(budget), "models": []}

    def tearDown(self):
        sup.build_command = self.real_build
        sup.sample = self.real_sample
        self.tmp.cleanup()

    def stand_in(self, code):
        sup.build_command = lambda python, root, run, group: [python, "-c", code]

    def accepted_code(self, group):
        return ("import json,pathlib;d=pathlib.Path(%r)/'calls'/%r;d.mkdir(parents=True);"
                "(d/'author-boundary.json').write_text(json.dumps({'status':'PASS_AUTHOR_PARTITION_STRUCTURE_ONLY'}));"
                "print('{}')" % (str(self.args.run_dir), group))

    def test_accepted_call_is_recorded_with_real_exit_status(self):
        self.stand_in(self.accepted_code("author-01"))
        result = sup.run_call(self.args, self.budget, "author-01", self.args.log_dir)
        self.assertEqual(result["outcome"], "ACCEPTED")
        record = json.loads((self.args.log_dir / "author-01.supervisor.json").read_text())
        self.assertEqual(record["returncode"], 0)
        self.assertTrue(record["accepted_by_supervisor"])

    def test_nonzero_exit_is_terminal_even_with_accepted_looking_files(self):
        self.stand_in(self.accepted_code("author-01") + ";raise SystemExit(7)")
        result = sup.run_call(self.args, self.budget, "author-01", self.args.log_dir)
        self.assertTrue(result["terminal"])
        self.assertEqual(result["returncode"], 7)

    def test_missing_boundary_file_is_terminal(self):
        self.stand_in("print('{}')")
        result = sup.run_call(self.args, self.budget, "author-02", self.args.log_dir)
        self.assertTrue(result["terminal"])
        self.assertIsNone(result["status"])

    def test_wrong_boundary_status_is_terminal(self):
        code = self.accepted_code("author-03").replace("PASS_AUTHOR_PARTITION_STRUCTURE_ONLY", "APPARATUS_INVALID")
        self.stand_in(code)
        self.assertTrue(sup.run_call(self.args, self.budget, "author-03", self.args.log_dir)["terminal"])

    def test_abort_limit_kills_only_the_started_child(self):
        self.budget["limits"]["abort_if"].update(free_percentage_below=101, free_percentage_consecutive_samples=1)
        self.stand_in("import time;time.sleep(60)")
        began = time.monotonic()
        result = sup.run_call(self.args, self.budget, "author-04", self.args.log_dir)
        self.assertLess(time.monotonic() - began, 30)
        self.assertTrue(result["terminal"])
        self.assertTrue(result["trips"])
        self.assertNotEqual(result["returncode"], 0)

    def test_wall_limit_terminates_a_hung_child(self):
        self.budget["limits"]["per_call_wall_limit_seconds"] = 2
        self.stand_in("import time;time.sleep(60)")
        began = time.monotonic()
        result = sup.run_call(self.args, self.budget, "author-05", self.args.log_dir)
        self.assertLess(time.monotonic() - began, 30)
        self.assertTrue(result["terminal"])

    def logging_code(self, group, truncated):
        lines = ("llama_context: n_ctx                 = 40960\\n"
                 "llama_kv_cache:       MTL0 KV buffer size =  1280.00 MiB\\n"
                 "slot   load_model: id  0 | task -1 | new slot, n_ctx = 40960\\n"
                 "slot   operator(): id  0 | task 0 | new prompt, n_ctx_slot = 40960, n_keep = 4, task.n_tokens = 16700\\n"
                 "slot print_timing: id  0 | task 0 | prompt eval time =  126000.00 ms / 16700 tokens (  7.54 ms per token)\\n"
                 "slot print_timing: id  0 | task 0 |        eval time =  335894.46 ms /  2185 tokens (6.50 tokens per second)\\n"
                 "slot      release: id  0 | task 0 | stop processing: n_tokens = 18885, truncated = %d\\n"
                 '[GIN] 2026/10/04 - 20:56:17 | 200 |         9m22s |       127.0.0.1 | POST     \\"/api/generate\\"\\n'
                 % truncated)
        return self.accepted_code(group) + (";open(%r,'ab').write(b'%s')" % (str(self.fake_log), lines))

    def test_runner_log_window_is_extracted_and_untruncated_call_is_accepted(self):
        self.stand_in(self.logging_code("author-08", 0))
        result = sup.run_call(self.args, self.budget, "author-08", self.args.log_dir)
        self.assertEqual(result["outcome"], "ACCEPTED")
        record = json.loads((self.args.log_dir / "author-08.supervisor.json").read_text())
        window = record["provider_log_window"]
        self.assertEqual(window["status"], "OBSERVED")
        self.assertEqual(window["prompt_tokens_received"], [16700])
        self.assertEqual(window["n_ctx_slot"], [40960])
        self.assertEqual(window["slot_releases"], [{"n_tokens": 18885, "truncated": 0}])
        self.assertEqual(window["generation_eval"], [{"ms": 335894.46, "tokens": 2185}])
        self.assertEqual(window["generate_requests"], [{"http_status": 200, "duration": "9m22s"}])
        self.assertNotIn("earlier unrelated line", json.dumps(record))
        self.assertTrue((self.args.private_dir / "author-08.provider-log-window.private.txt").is_file())

    def test_runner_reported_truncation_is_terminal_even_when_everything_else_passes(self):
        self.stand_in(self.logging_code("author-09", 1))
        result = sup.run_call(self.args, self.budget, "author-09", self.args.log_dir)
        self.assertEqual(result["outcome"], "FAILED")
        self.assertTrue(result["terminal"])
        record = json.loads((self.args.log_dir / "author-09.supervisor.json").read_text())
        self.assertEqual(record["provider_log_window"]["truncated_nonzero"], 1)
        self.assertFalse(record["accepted_by_supervisor"])

    def test_unreadable_provider_log_is_recorded_unavailable_and_is_not_a_stop(self):
        self.fake_log.unlink()
        self.stand_in(self.accepted_code("author-10"))
        result = sup.run_call(self.args, self.budget, "author-10", self.args.log_dir)
        self.assertEqual(result["outcome"], "ACCEPTED")
        record = json.loads((self.args.log_dir / "author-10.supervisor.json").read_text())
        self.assertEqual(record["provider_log_window"]["status"], "UNAVAILABLE")

    def test_rotated_log_cannot_yield_a_window(self):
        self.assertIsNone(sup.read_log_window(self.fake_log, 100, 10))
        self.assertIsNone(sup.read_log_window(self.fake_log, None, 10))
        self.assertEqual(sup.extract_log_facts(None), {"status": "UNAVAILABLE"})
        self.assertEqual(sup.extract_log_facts(b"[GIN] nothing relevant\n")["status"], "NO_SLOT_RELEASE_IN_WINDOW")

    def test_wait_that_never_starts_a_request_is_not_a_failed_call(self):
        self.budget["limits"]["start_requires"]["min_free_percentage"] = 101
        self.budget["limits"]["max_wait_for_slot_seconds"] = 1
        self.budget["limits"]["wait_poll_seconds_first_120s"] = 1
        self.stand_in("raise SystemExit(99)")
        result = sup.run_call(self.args, self.budget, "author-06", self.args.log_dir)
        self.assertEqual(result["outcome"], "WAIT_EXCEEDED")
        self.assertFalse(result["terminal"])
        self.assertFalse((self.args.log_dir / "author-06.stdout.txt").exists())


DRIVER = """
import json, sys
sys.path.insert(0, sys.argv[1])
import supervisor as sup
base = sys.argv[2]
child_code = "import os,time;open(%r,'w').write(str(os.getpid()));time.sleep(120)" % (base + "/child.pid")
sup.build_command = lambda python, root, run, group: [python, "-c", child_code]
healthy = json.loads(sys.argv[3])
sup.sample = lambda budget: healthy
sys.argv = ["supervisor.py", "--root", base, "--run-dir", base + "/run", "--python", sys.executable,
            "--budget", base + "/budget.json", "--log-dir", base + "/logs", "author-01"]
raise SystemExit(sup.main())
"""


class Interruption(unittest.TestCase):
    def test_sigterm_to_the_supervisor_leaves_no_running_child(self):
        import os
        import signal
        import subprocess
        with tempfile.TemporaryDirectory() as name:
            base = Path(name)
            budget = copy.deepcopy(BUDGET)
            budget["context_evidence"]["provider_log"] = str(base / "server.log")
            budget["limits"]["sample_interval_seconds"] = 1
            (base / "budget.json").write_text(json.dumps(budget))
            (base / "run" / "calls").mkdir(parents=True)
            pid_file = base / "child.pid"
            parent = subprocess.Popen([sys.executable, "-c", DRIVER, str(Path(__file__).resolve().parent),
                                       name, json.dumps(HEALTHY)])
            for _ in range(100):
                if pid_file.exists() and pid_file.read_text():
                    break
                time.sleep(0.1)
            child = int(pid_file.read_text())
            os.kill(child, 0)  # the child is running while supervised
            os.kill(parent.pid, signal.SIGTERM)
            parent.wait(timeout=60)
            time.sleep(1)
            with self.assertRaises(ProcessLookupError):
                os.kill(child, 0)
            self.assertIn("supervisor_interrupted", (base / "logs" / "events.jsonl").read_text())


class Commands(unittest.TestCase):
    def test_commands_match_the_protocol_actions_exactly(self):
        run = Path("/r")
        self.assertEqual(sup.build_command("py", Path("/w"), run, "canary"),
                         ["py", sup.WRAPPER, "canary", "--root", "/w", "--run-dir", "/r"])
        self.assertEqual(sup.build_command("py", Path("/w"), run, "author-07"),
                         ["py", sup.WRAPPER, "run", "--root", "/w", "--run-dir", "/r", "--group", "author-07"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
