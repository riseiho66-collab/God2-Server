"""Small per-thread transition ledger; unmatched events never imply unwinding."""
class TransitionFrameStack:
    def __init__(self):
        self.frames = []
        self.stacks = {}
        self.unmatched = []

    def enter(self, event):
        key = (event['pid'], event['tid'])
        stack = self.stacks.setdefault(key, [])
        frame = dict(event, transition_id=len(self.frames),
                     parent_id=stack[-1]['transition_id'] if stack else None,
                     depth=len(stack), entry_pc=event['pc'], entry_tid=event['tid'],
                     entry_esp=event['sp'], expected_return_pc=event['expected'],
                     expected_return_esp=event['sp']+4, status='OPEN')
        stack.append(frame)
        self.frames.append(frame)
        return frame

    def returned(self, event):
        stack = self.stacks.get((event['pid'], event['tid']), [])
        if not stack:
            self.unmatched.append(dict(event, reason='NO_OPEN_FRAME'))
            return False
        frame = stack[-1]
        if not (event['pc'] == frame['expected_return_pc']
                and event['sp'] == frame['expected_return_esp']
                and event['caller'] == frame['caller']
                and event['time'] >= frame['time']):
            self.unmatched.append(dict(event, reason='TOP_FRAME_MISMATCH_UNEXPLAINED'))
            return False
        frame.update(status='RETURNED', returned=event)
        stack.pop()
        return True

    def finish(self):
        for stack in self.stacks.values():
            for frame in stack:
                frame['status'] = 'LOST'
        return {'frames': self.frames, 'unmatched': self.unmatched,
                'nested_observed': any(f['depth'] > 0 for f in self.frames),
                'nesting_scope': 'Ledger entry ordering only; invalid return chains do not prove genuine nested callbacks',
                'all_returned': bool(self.frames) and not self.unmatched
                    and all(f['status'] == 'RETURNED' for f in self.frames)}
