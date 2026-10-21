import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import contracts as gate
import lab
from backends import LocalBackend, MockBackend, Reply, mock_report, validate_endpoint


class OrchestrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_three_baselines_same_fixture_and_call_limits(self):
        results = [await lab.run(MockBackend(2), mode) for mode in ('single', 'sequential', 'parallel')]
        self.assertEqual({r['summary']['fixture_sha256'] for r in results}, {gate.digest(gate.packet())})
        self.assertEqual([r['summary']['calls_reserved'] for r in results], [5, 5, 5])
        self.assertEqual([r['summary']['peak_active_calls'] for r in results], [1, 1, 2])
        self.assertTrue(all(r['summary']['validated'] and r['summary']['reported_usage'] is None for r in results))
        self.assertEqual({gate.digest(r['candidate']) for r in results}, {gate.digest(mock_report())})
        for r in results:
            self.assertEqual(r['events'][-1]['event'], 'run_ended')

    async def test_real_overlap_not_just_two_role_names(self):
        r = await lab.run(MockBackend(10))
        events = r['events']
        start = {x['role']: x['seq'] for x in events if x['event'] == 'call_started'}
        finish = {x['role']: x['seq'] for x in events if x['event'] == 'call_finished'}
        self.assertLess(start['validation'], finish['implementation'])
        self.assertGreater(start['reviewer'], max(finish['implementation'], finish['validation']))

    async def test_conflict_feedback_revises_only_target_and_rechecks_join(self):
        r = await lab.run(MockBackend(0, 'conflict'))
        self.assertTrue(r['summary']['validated'])
        self.assertEqual(r['summary']['calls_reserved'], 7)
        messages = [x for x in r['events'] if x['event'] == 'message_delivered']
        self.assertEqual([x['recipient'] for x in messages], ['validation'])
        validation = [x for x in r['artifacts'] if x['name'] == 'validation']
        self.assertEqual([x['value']['assessment'] for x in validation], ['ready', 'needs_gate'])
        self.assertEqual([x['revision'] for x in validation], [1, 2])
        inputs = [x['payload'] for x in r['inputs'].values() if x['role'] == 'validation']
        self.assertIsNone(inputs[0]['feedback'])
        self.assertIn('T2', inputs[1]['feedback']['evidence_ids'])

    async def test_retry_timeout_and_retry_limit(self):
        for fault in ('transient', 'timeout'):
            r = await lab.run(MockBackend(0, fault), timeout=.02)
            self.assertTrue(r['summary']['validated'])
            self.assertEqual(r['summary']['calls_reserved'], 6)
            self.assertEqual(sum(x['event'] == 'retry_scheduled' for x in r['events']), 1)
        r = await lab.run(MockBackend(0, 'transient'), retries=0)
        self.assertEqual(r['summary']['status'], 'failed')
        self.assertIsNone(r['candidate'])
        self.assertFalse(any(x.get('role') in ('reviewer', 'synthesizer') for x in r['events']))

    async def test_malformed_output_and_review_rejection_do_not_unlock_synthesis(self):
        for fault in ('malformed', 'review_reject'):
            r = await lab.run(MockBackend(0, fault))
            self.assertEqual(r['summary']['status'], 'failed')
            self.assertIsNone(r['candidate'])
            self.assertFalse(any(x.get('role') == 'synthesizer' for x in r['events']))
        r = await lab.run(MockBackend(0, 'conflict'), max_revisions=0)
        self.assertEqual(r['summary']['calls_reserved'], 4)
        self.assertIsNone(r['candidate'])

    async def test_budget_before_dispatch_and_cancel_cleanup(self):
        for budget in (1, 2, 4):
            r = await lab.run(MockBackend(1), max_calls=budget)
            self.assertLessEqual(r['summary']['calls_reserved'], budget)
            self.assertIsNone(r['candidate'])
        r = await lab.run(MockBackend(30), cancel_after_ms=45)
        self.assertEqual(r['summary']['status'], 'cancelled')
        self.assertTrue(any(x['event'] == 'call_cancelled' for x in r['events']))
        self.assertFalse(any(x.get('role') == 'synthesizer' for x in r['events']))
        end_count = len(r['events'])
        await asyncio.sleep(.05)
        self.assertEqual(len(r['events']), end_count)
        r = await lab.run(MockBackend(40), deadline=.02)
        self.assertEqual(r['summary']['status'], 'deadline')
        self.assertIsNone(r['candidate'])

    async def test_invalid_runtime_boundaries(self):
        for config in ({'max_calls': 0}, {'max_calls': 51}, {'retries': -1}, {'retries': 3}, {'timeout': float('nan')}, {'deadline': float('inf')}, {'single_turns': 0}, {'cancel_after_ms': 0}, {'max_revisions': 3}):
            with self.assertRaises(gate.ContractError):
                await lab.run(MockBackend(0), **config)

    async def test_approval_is_hash_bound_idempotent_and_not_a_model_decision(self):
        result = await lab.run(MockBackend(0))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'runs'
            manifest = lab.save(result, root)
            folder = root / manifest['run_id']
            self.assertFalse((folder / 'report.json').exists())
            with self.assertRaises(gate.ContractError):
                lab.approve(manifest['run_id'], '0' * 64, root)
            self.assertEqual(lab.approve(manifest['run_id'], manifest['candidate_sha256'], root)['status'], 'published_locally')
            original = (folder / 'report.json').read_bytes()
            self.assertEqual(lab.approve(manifest['run_id'], manifest['candidate_sha256'], root)['status'], 'already_published')
            self.assertEqual(original, (folder / 'report.json').read_bytes())
            candidate = json.loads((folder / 'candidate.json').read_text())
            candidate['summary'] = 'changed after approval'
            (folder / 'candidate.json').write_text(json.dumps(candidate))
            with self.assertRaises(gate.ContractError):
                lab.approve(manifest['run_id'], manifest['candidate_sha256'], root)


class ContractTests(unittest.TestCase):
    def test_tool_permission_and_plan_validation(self):
        data = gate.packet()
        for ids in (['../../private'], ['release', 'release'], [], ['shell']):
            with self.assertRaises(gate.ContractError):
                gate.evidence(data, ids)
        with self.assertRaises(gate.ContractError):
            gate.plan({'tasks': [{'worker_id': 'attacker'}]}, data)

    def test_unseen_or_fabricated_citation_rejected(self):
        visible = gate.evidence(gate.packet(), ['release'])
        for key, quote in [('T2', 'outside visible context'), ('R2', 'fabricated')]:
            with self.assertRaises(gate.ContractError):
                gate.findings({'assessment': 'ready', 'findings': [{'evidence_id': key, 'quote': quote, 'note': 'claim'}]}, visible)

    def test_fixture_grader_is_separate_from_review(self):
        report = mock_report()
        report['verdict'] = 'ready'
        with self.assertRaises(gate.ContractError):
            gate.report(report, gate.packet())

    def test_endpoint_restrictions(self):
        for url in ('https://api.openai.com/v1', 'http://example.com:80/v1', 'http://127.0.0.1/v1', 'http://user:pass@127.0.0.1:80/v1', 'http://127.0.0.1:80/v1?key=x', 'http://127.0.0.1:80/other'):
            with self.assertRaises(gate.ContractError):
                validate_endpoint(url)
        self.assertEqual(validate_endpoint('http://127.0.0.1:8000/v1'), 'http://127.0.0.1:8000/v1/chat/completions')
        self.assertIn('[::1]', validate_endpoint('http://[::1]:8000/v1'))

    def test_run_path_is_not_an_arbitrary_file_reader(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(gate.ContractError):
                lab.approve('../../private', '0' * 64, Path(temp))


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def serve(self, behavior='normal'):
        self.requests = []
        active = set()

        async def handler(reader, writer):
            active.add(asyncio.current_task())
            try:
                header = await reader.readuntil(b'\r\n\r\n')
                length = int(next(line.split(b':')[1] for line in header.split(b'\r\n') if line.lower().startswith(b'content-length:')))
                body = json.loads(await reader.readexactly(length))
                self.requests.append(body)
                if behavior == 'slow':
                    await asyncio.sleep(.2)
                if behavior == 'redirect':
                    writer.write(b'HTTP/1.1 302 Found\r\nLocation: http://example.com/\r\nContent-Length: 0\r\n\r\n')
                elif behavior == 'oversize':
                    writer.write(b'HTTP/1.1 200 OK\r\nContent-Length: 2097152\r\n\r\n')
                else:
                    payload = json.loads(body['messages'][1]['content'])
                    reply = await MockBackend(0).complete(payload['stage'], payload['input'], 1, 2)
                    if payload['stage'] == 'plan':
                        reply.data['tasks'][0]['document_ids'] = ['release', 'tests', 'policy']
                        reply.data['tasks'][0]['focus'] = 'HTTP stub changed real routing payload'
                    if payload['stage'] == 'synthesize':
                        reply.data['summary'] = 'Protocol stub output, NOT a real LLM result.'
                    content = 'invalid JSON' if behavior == 'malformed' else gate.canonical(reply.data)
                    raw = json.dumps({'choices': [{'finish_reason': 'stop', 'message': {'content': content}}], 'usage': {'prompt_tokens': 10, 'completion_tokens': 20}}).encode()
                    if behavior == 'wrong_shape':
                        raw = b'{"choices":["bad"]}'
                    if behavior == 'chunked':
                        writer.write(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n' + hex(len(raw))[2:].encode() + b'\r\n' + raw + b'\r\n0\r\n\r\n')
                    else:
                        writer.write(b'HTTP/1.1 200 OK\r\nContent-Length: ' + str(len(raw)).encode() + b'\r\n\r\n' + raw)
                await writer.drain()
            except (ConnectionError, asyncio.IncompleteReadError):
                pass
            finally:
                writer.close()
                active.discard(asyncio.current_task())

        server = await asyncio.start_server(handler, '127.0.0.1', 0)

        async def cleanup():
            server.close()
            await server.wait_closed()
            tasks = list(active)
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        self.addAsyncCleanup(cleanup)
        return 'http://127.0.0.1:' + str(server.sockets[0].getsockname()[1]) + '/v1'

    async def test_protocol_stub_drives_plan_content_and_usage(self):
        url = await self.serve()
        r = await lab.run(LocalBackend(url, 'protocol-stub'))
        self.assertTrue(r['summary']['validated'], r['summary'])
        self.assertIn('Protocol stub', r['candidate']['summary'])
        inputs = [x for x in r['inputs'].values() if x['role'] == 'implementation']
        self.assertEqual(len(inputs[0]['payload']['evidence']), 9)
        self.assertEqual(r['summary']['reported_usage']['completion_tokens'], 100)
        self.assertTrue(r['summary']['usage_complete'])
        self.assertEqual(len(self.requests), 5)
        self.assertTrue(all(x['model'] == 'protocol-stub' for x in self.requests))

    async def test_chunked_local_response(self):
        url = await self.serve('chunked')
        r = await lab.run(LocalBackend(url, 'protocol-stub'))
        self.assertTrue(r['summary']['validated'])

    async def test_redirect_oversize_malformed_and_timeout_fail_closed(self):
        for behavior in ('redirect', 'oversize', 'malformed', 'wrong_shape', 'slow'):
            url = await self.serve(behavior)
            r = await lab.run(LocalBackend(url, 'protocol-stub'), timeout=.02, retries=0)
            self.assertFalse(r['summary']['validated'])
            self.assertIsNone(r['candidate'])
            self.assertEqual(len(self.requests), 1)


if __name__ == '__main__':
    unittest.main()
