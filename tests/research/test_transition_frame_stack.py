"""Synthetic nesting tests validate the ledger, never certify runtime tracing."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/research'))
from trace_qualification.frame_stack import TransitionFrameStack


class StackTests(unittest.TestCase):
    def event(self, sp=0x2000, **overrides):
        return dict(dict(pid=1, tid=2, pc=0x3000, sp=sp, expected=0x4000,
                         caller=0x5000, time=1), **overrides)

    def test_nested_same_return_address(self):
        stack = TransitionFrameStack()
        outer = stack.enter(self.event())
        inner = stack.enter(self.event(0x1f00, time=2))
        self.assertEqual(inner['parent_id'], outer['transition_id'])
        self.assertTrue(stack.returned(self.event(0x1f04, pc=0x4000, time=3)))
        self.assertTrue(stack.returned(self.event(0x2004, pc=0x4000, time=4)))
        self.assertTrue(stack.finish()['all_returned'])

    def test_out_of_order_does_not_invent_unwind(self):
        stack = TransitionFrameStack()
        stack.enter(self.event())
        stack.enter(self.event(0x1f00))
        self.assertFalse(stack.returned(self.event(0x2004, pc=0x4000)))
        self.assertEqual([f['status'] for f in stack.finish()['frames']], ['LOST','LOST'])

    def test_thread_and_caller_mismatch(self):
        for changes in ({'tid':3}, {'caller':0x5555}, {'time':0}):
            stack = TransitionFrameStack()
            stack.enter(self.event())
            self.assertFalse(stack.returned(self.event(0x2004, **dict({'pc':0x4000}, **changes))))

    def test_duplicate_return_not_silently_dropped(self):
        stack = TransitionFrameStack()
        stack.enter(self.event())
        event = self.event(0x2004, pc=0x4000)
        self.assertTrue(stack.returned(event))
        self.assertFalse(stack.returned(event))
        self.assertFalse(stack.finish()['all_returned'])


if __name__ == '__main__':
    unittest.main()
