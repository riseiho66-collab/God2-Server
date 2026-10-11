# Owned pending checkpoint discovery

load_pending_checkpoint(account,character) finds the current unledgered reservation
without trusting a client-provided battle ID. A transaction covers ownership check,
reservation selection, checkpoint load and resource validation. No reservation
returns none. Multiple reservations, missing checkpoint/resources, terminal state,
wrong resource revision or values, and missing/duplicate owned actor fail closed.
It does not delete incomplete reservations, seed replacements or award anything.

Tests distinguish no encounter from reserved-but-missing-checkpoint, reject foreign
ownership, duplicate pending rows and resource value/revision divergence, find the
exact snapshot after SQLite file reopen, and exclude successfully settled battles.

This is a consistent read result, not a lock held after the function returns or an
exclusive durable lease. The eventual resume writer must CAS its baseline again.
Policy/receipt state and native client initialization still need integration; no
Application call or end-to-end reconnect acceptance is claimed.
