import test from 'node:test';
import assert from 'node:assert/strict';
import '../assets/loop-machine.js';

const {create, transition, terminal, allowed, scenarios} = globalThis.FieldnotesLoop;
const act = (state, ...events) => events.reduce(transition, state);
function finish(state) {
  for (let i = 0; i < 40 && !terminal(state); i++) {
    state = transition(state, state.status === 'approval' ? 'approve' : state.status === 'unknown' ? 'reconcile' : 'next');
  }
  assert.ok(terminal(state), 'bounded scenarios must terminate');
  return state;
}

test('normal run requires exact approval, costs 7 units and ignores repeated terminal actions', () => {
  let s = act(create(), 'next', 'next');
  assert.equal(s.status, 'approval');
  assert.equal(s.attempts, 0);
  assert.strictEqual(transition(s, 'next'), s);
  s = transition(s, 'approve');
  assert.strictEqual(transition(s, 'approve'), s);
  s = finish(s);
  assert.equal(s.status, 'succeeded');
  assert.equal(s.spent, 7);
  assert.equal(s.attempts, 1);
  assert.equal(s.writes, 1);
  for (const event of ['next', 'approve', 'deny', 'reconcile', 'cancel']) assert.strictEqual(transition(s, event), s);
});

test('denied approval performs no tool attempt or write', () => {
  const s = act(create(), 'next', 'next', 'deny');
  assert.equal(s.status, 'cancelled');
  assert.equal(s.attempts, 0);
  assert.equal(s.writes, 0);
});

test('confirmed transient failure retries only within the configured limit', () => {
  const noRetry = finish(create({scenario: 'transient', retries: 0}));
  assert.equal(noRetry.status, 'failed');
  assert.equal(noRetry.attempts, 1);
  assert.equal(noRetry.writes, 0);
  const retry = finish(create({scenario: 'transient', retries: 1}));
  assert.equal(retry.status, 'succeeded');
  assert.equal(retry.attempts, 2);
  assert.equal(retry.spent, 10);
});

test('unknown committed result prohibits blind retry and avoids a second write', () => {
  let s = act(create({scenario: 'lost_committed'}), 'next', 'next', 'approve', 'next');
  assert.equal(s.status, 'unknown');
  assert.equal(s.knownEffect, null);
  assert.equal(s.writes, 1);
  assert.strictEqual(transition(s, 'next'), s);
  s = finish(s);
  assert.equal(s.status, 'succeeded');
  assert.equal(s.attempts, 1);
  assert.equal(s.spent, 8);
});

test('unknown uncommitted result reconciles before an allowed retry', () => {
  let s = act(create({scenario: 'lost_uncommitted'}), 'next', 'next', 'approve', 'next');
  s = transition(s, 'reconcile');
  assert.equal(s.status, 'retry_wait');
  assert.equal(s.knownEffect, false);
  assert.equal(s.writes, 0);
  s = finish(s);
  assert.equal(s.status, 'succeeded');
  assert.equal(s.attempts, 2);
  assert.equal(s.spent, 11);
});

test('budget exhaustion before dispatch has no effect; after writing is not success', () => {
  const early = finish(create({budget: 1}));
  assert.equal(early.status, 'exhausted');
  assert.equal(early.spent, 0);
  assert.equal(early.writes, 0);
  const late = finish(create({budget: 6}));
  assert.equal(late.status, 'exhausted');
  assert.equal(late.spent, 5);
  assert.equal(late.writes, 1);
  assert.equal(late.knownEffect, true);
  assert.equal(finish(create({budget: 7})).status, 'succeeded');
});

test('cancellation preserves confirmed writes and unknown effects', () => {
  const known = act(create(), 'next', 'next', 'approve', 'next', 'cancel');
  assert.equal(known.status, 'cancelled');
  assert.equal(known.writes, 1);
  assert.equal(known.knownEffect, true);
  const unknown = act(create({scenario: 'lost_committed'}), 'next', 'next', 'approve', 'next', 'cancel');
  assert.equal(unknown.status, 'cancelled');
  assert.equal(unknown.writes, 1);
  assert.equal(unknown.knownEffect, null);
});

test('permanent failure never retries; transitions leave their input untouched', () => {
  const original = create({scenario: 'permanent', retries: 3});
  const snapshot = JSON.stringify(original);
  const end = finish(original);
  assert.equal(JSON.stringify(original), snapshot);
  assert.equal(end.status, 'failed');
  assert.equal(end.attempts, 1);
  assert.equal(end.writes, 0);
});

test('invalid inputs reject without coercion and resets are independent', () => {
  for (const budget of [0, 41, -1, 1.5, NaN, Infinity, '', '12']) assert.throws(() => create({budget}));
  for (const retries of [-1, 4, .5, Infinity, '1']) assert.throws(() => create({retries}));
  assert.throws(() => create({scenario: 'not-a-scenario'}));
  assert.throws(() => create({approval: 'false'}));
  const a = finish(create()), b = create();
  assert.equal(a.writes, 1);
  assert.equal(b.writes, 0);
  assert.equal(b.events.length, 1);
});

test('all 1600 configurations terminate within budget with at most one effect', () => {
  for (let budget = 1; budget <= 40; budget++) for (let retries = 0; retries <= 3; retries++) for (const scenario of scenarios) for (const approval of [true, false]) {
    let s = create({budget, retries, scenario, approval});
    for (let i = 0; i < 40 && !terminal(s); i++) {
      const before = s;
      for (const invalid of ['approve', 'deny', 'reconcile', 'not-an-event']) {
        if (!allowed(s).includes(invalid)) assert.strictEqual(transition(s, invalid), s);
      }
      s = transition(s, s.status === 'approval' ? 'approve' : s.status === 'unknown' ? 'reconcile' : 'next');
      assert.ok(s.spent >= before.spent && s.spent <= budget);
      assert.ok(s.writes >= before.writes && s.writes <= 1);
      assert.ok(s.attempts <= retries + 1);
    }
    assert.ok(terminal(s));
    if (s.status === 'succeeded') assert.equal(s.knownEffect, true);
  }
});
