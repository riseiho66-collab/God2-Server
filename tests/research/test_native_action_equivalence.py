"""Synthetic gate inputs are unit fixtures, never client execution evidence."""

from dataclasses import replace
import unittest

from tools.native_lab.action_equivalence import (
    ActionEvidence, IMAGE_SHA256, StateWrite, WIRE, evaluate_equivalence, frozen_report,
)


class NativeActionEquivalenceTests(unittest.TestCase):
    def setUp(self):
        self.human = ActionEvidence(
            run_id="SYNTHETIC-human", lane="HUMAN_UI", source="unit-fixture",
            raw_wire=WIRE, human_confirmed=True, runtime_trace_source="unit-fixture",
            image_sha256=IMAGE_SHA256, builder_rva=0x147d0, send_return_rva=0x12506,
            relevant_writes=(StateWrite("UI", 0x178cec, b"\x02\x00\x00\x00",
                                        b"\x03\x00\x00\x00", 0xaffc),),
            writes_complete=True, write_scope=("UI-state", "network-session"),
            action_trace_bound=True, correct_thread_observed=True,
            state_before="SERVER_AUTO_SELECTED", selected_entry_id=0,
        )
        self.lab = replace(self.human, run_id="SYNTHETIC-lab",
                           lane="NATIVE_LAB_CAPTURE", human_confirmed=False)

    def test_complete_synthetic_evidence_passes(self):
        result = evaluate_equivalence(self.human, self.lab)
        self.assertEqual(result["status"], "STRUCTURALLY_EQUIVALENT")
        self.assertTrue(result["structurally_equivalent"])
        self.assertFalse(result["equivalent"])

    def test_each_mandatory_proof_is_required(self):
        for field, value in (("builder_rva", None), ("send_return_rva", None),
                             ("relevant_writes", None), ("writes_complete", False),
                             ("runtime_trace_source", None), ("action_trace_bound", False),
                             ("correct_thread_observed", False), ("write_scope", ()),
                             ("raw_wire", None), ("image_sha256", None)):
            for side in ("human", "lab"):
                with self.subTest(field=field, side=side):
                    human = replace(self.human, **{field: value}) if side == "human" else self.human
                    lab = replace(self.lab, **{field: value}) if side == "lab" else self.lab
                    result = evaluate_equivalence(human, lab)
                    self.assertEqual(result["status"], "UNPROVEN")
                    self.assertFalse(result["equivalent"])

    def test_static_builder_and_matching_wire_are_insufficient(self):
        result = evaluate_equivalence(replace(self.human, runtime_trace_source=None,
                                             relevant_writes=None), self.lab)
        self.assertEqual(result["status"], "UNPROVEN")

    def test_mismatches_reject(self):
        for field, value in (("raw_wire", b"\x06\x00\xa3\xa3\xfd\x00"),
                             ("builder_rva", 0x147d1), ("send_return_rva", 0x12507),
                             ("relevant_writes", (replace(self.lab.relevant_writes[0],
                                                         after=b"\x04\x00\x00\x00"),)),
                             ("write_scope", ("UI-state",)), ("selected_entry_id", 1)):
            with self.subTest(field=field):
                result = evaluate_equivalence(self.human, replace(self.lab, **{field: value}))
                self.assertEqual(result["status"], "REJECTED")
                self.assertIn(field, result["mismatches"])

    def test_empty_write_trace_does_not_prove_known_state_action(self):
        self.assertEqual(evaluate_equivalence(replace(self.human, relevant_writes=()),
                                             self.lab)["status"], "UNPROVEN")

    def test_human_provenance_required(self):
        self.assertEqual(evaluate_equivalence(replace(self.human, human_confirmed=False),
                                             self.lab)["status"], "UNPROVEN")

    def test_frozen_capture_remains_unproven(self):
        result = frozen_report()
        self.assertEqual(result["status"], "UNPROVEN")
        self.assertIn("human.builder_rva", result["missing_proof"])
        self.assertIn("human.complete_relevant_state_write_trace", result["missing_proof"])
        self.assertIn("lab.native_action_capture", result["missing_proof"])
        self.assertEqual(result["observed_wire_hex"], "06 00 a3 a3 fd d5")
        self.assertEqual(result["candidate_abi"]["entry_rva"], "0x7010")


if __name__ == "__main__":
    unittest.main()
