import sys
from pathlib import Path
import unittest
import contextlib
import io
import socket
import tempfile
from unittest.mock import patch, MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/strike_lab'))
from apex import MEMORY_WARNING,milestones,progression,warning_path_passed,execution_summary
import apex


class ApexTests(unittest.TestCase):
    def test_world_entry_requires_dual_connection_before_launch(self):
        with patch.object(sys,'argv',['apex.py','god2-strike-runner','--recovered-world-entry']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:
                apex.main()
            self.assertEqual(error.exception.code,2)
        with tempfile.TemporaryDirectory() as directory,self.assertRaises(ValueError):
            apex.CppSeedServer(Path(directory),15,recovered_world_entry=True)

    def test_dual_connection_requires_character_persistence_before_launch(self):
        with patch.object(sys,'argv',['apex.py','god2-strike-runner','--recovered-dual-connection']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:
                apex.main()
            self.assertEqual(error.exception.code,2)
        with tempfile.TemporaryDirectory() as directory,self.assertRaises(ValueError):
            apex.CppSeedServer(Path(directory),15,recovered_dual_connection=True)

    def test_character_creation_requires_account_auth_before_launch(self):
        with patch.object(sys,'argv',['apex.py','god2-strike-runner','--recovered-character-create']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:
                apex.main()
            self.assertEqual(error.exception.code,2)
        with tempfile.TemporaryDirectory() as directory,self.assertRaises(ValueError):
            apex.CppSeedServer(Path(directory),15,recovered_character_create=True)

    def test_account_auth_requires_candidate_mode_before_launch(self):
        with patch.object(sys,'argv',['apex.py','god2-strike-runner','--recovered-account-auth']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:
                apex.main()
            self.assertEqual(error.exception.code,2)
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            apex.CppSeedServer(Path(directory),15,recovered_account_auth=True)

    def test_legacy_candidate_requires_explicit_non_ui_cpp_prefix(self):
        required=['--zero-ui-prefix','--server-list','--cpp-server']
        for omitted in required:
            argv=['apex.py','god2-strike-runner','--legacy-character-list-candidate']
            argv.extend(option for option in required if option!=omitted)
            with self.subTest(omitted=omitted), patch.object(sys,'argv',argv):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    apex.main()
                self.assertEqual(error.exception.code,2)

    def test_cpp_candidate_config_selection_does_not_change_default(self):
        for candidate,authentication,creation,dual,world,config in ((False,False,False,False,False,'recovered-post-server-select.json'),
                                 (True,False,False,False,False,'legacy-character-list-candidate.json'),
                                 (True,True,False,False,False,'recovered-account-login.json'),
                                 (True,True,True,False,False,'recovered-character-create.json'),
                                 (True,True,True,True,False,'recovered-dual-connection.json'),
                                 (True,True,True,True,True,'recovered-world-entry.json')):
            with self.subTest(candidate=candidate), tempfile.TemporaryDirectory() as directory:
                process=MagicMock()
                process.poll.return_value=None
                with patch.object(apex.subprocess,'Popen',return_value=process) as launch:
                    with patch.object(apex,'require_available_loopback_port'), patch.object(
                            Path,'read_text',return_value=(
                                'Character connection listening on 127.0.0.1:52463;\n'
                                'listening on 127.0.0.1:2592')):
                        server=apex.CppSeedServer(Path(directory),15,post_select=True,
                            legacy_character_list_candidate=candidate,recovered_account_auth=authentication,recovered_character_create=creation,recovered_dual_connection=dual,recovered_world_entry=world)
                        server.close()
                command=launch.call_args.args[0]
                self.assertEqual(Path(command[command.index('--config')+1]).name,config)
                self.assertEqual(command[-2:],['--run-for','18'])
                self.assertEqual(launch.call_args.kwargs['creationflags'],apex.subprocess.CREATE_NO_WINDOW)

    def test_occupied_loopback_port_rejected_before_client_probe(self):
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as listener:
            listener.bind(('127.0.0.1',0))
            listener.listen(1)
            port=listener.getsockname()[1]
            with self.assertRaisesRegex(RuntimeError,'occupied'):
                apex.require_available_loopback_port(port)

    def test_summary_does_not_promote_unstarted_protocol_failure(self):
        result={'result':'HARD_TIMEOUT','furthest_milestone':'WINSOCK_REACHED',
                'milestones':{'CONNECTED':False},'server_list':{'LAST_ACCEPTED_STATE':'REGRESSION'}}
        summary=execution_summary(result,Path('test-run'))
        self.assertEqual(summary['result'],'HARD_TIMEOUT')
        self.assertEqual(summary['downstream_protocol_execution'],'NOT_REACHED')
        result['milestones']['CONNECTED']=True
        self.assertEqual(execution_summary(result,Path('test-run')),result['server_list'])

    def test_summary_preserves_tool_error_without_milestones(self):
        result={'result':'TOOL_ERROR','error':'refused'}
        self.assertEqual(execution_summary(result,Path('test-run'))['error'],'refused')

    def natural_warning_events(self):
        result=[{'pc':pc,'native_stop':'[br=1]'} for pc in (0x40f186,0x40f246,0x40f2d0)]
        result.append(dict(event_type='API_RETURN',api='WSAStartup',matched=True,eax=0))
        for sequence,event in enumerate(result):
            event.update(pid=1,tid=2,global_sequence=sequence)
        return result

    def test_natural_no_dialog_path(self):
        events=self.natural_warning_events()
        self.assertTrue(progression(events)['MEMORY_WARNING_PASSED'])
        self.assertFalse(progression(events)['MEMORY_WARNING_CLOSED'])
        self.assertFalse(progression(events)['CONNECTED'])

    def test_natural_path_requires_all_evidence(self):
        original=self.natural_warning_events()
        for remove in range(len(original)):
            self.assertFalse(warning_path_passed(original[:remove]+original[remove+1:]))
        for key,value in [('tid',3),('pid',4),('matched',False),('eax',1),('global_sequence',-1)]:
            events=self.natural_warning_events()
            events[-1][key]=value
            with self.subTest(key=key):
                self.assertFalse(warning_path_passed(events))

    def test_warning_path_rejects_fallthrough(self):
        events=self.natural_warning_events()
        events[1]['native_stop']='[br=0]'
        self.assertFalse(warning_path_passed(events))

    def test_warning_seen_is_not_passed(self):
        state=progression([{'message_text':MEMORY_WARNING}])
        self.assertTrue(state['MEMORY_WARNING_SEEN'])
        self.assertFalse(state['MEMORY_WARNING_PASSED'])
        self.assertFalse(state['WINSOCK_REACHED'])

    def test_warning_requires_exact_text(self):
        self.assertFalse(progression([{'message_text':MEMORY_WARNING+'?'}])['MEMORY_WARNING_SEEN'])

    def test_closed_dialog_alone_is_not_passed(self):
        event={'event_type':'MEMORY_WARNING_RETURN','ui':{'matched':True,'ok_sent':True,'closed':True}}
        self.assertTrue(progression([event])['MEMORY_WARNING_CLOSED'])
        self.assertFalse(progression([event])['MEMORY_WARNING_PASSED'])
        event['event_type']='POST_WARNING_EXECUTION'
        self.assertTrue(progression([event])['MEMORY_WARNING_PASSED'])

    def test_socket_failure_and_attempt_do_not_mean_created(self):
        events=[{'event_type':'API_ENTRY','api':'socket'},
                {'event_type':'API_RETURN','api':'socket','eax':0xffffffff,'matched':True}]
        self.assertFalse(progression(events)['SOCKET_CREATED'])
        events[-1]['eax']=123
        self.assertTrue(progression(events)['SOCKET_CREATED'])

    def test_extended_socket_and_connect_apis(self):
        for api in ('WSASocketA','WSASocketW'):
            self.assertTrue(progression([{'event_type':'API_RETURN','api':api,'eax':123,'matched':True}])['SOCKET_CREATED'])
            self.assertFalse(progression([{'event_type':'API_RETURN','api':api,'eax':0xffffffff,'matched':True}])['SOCKET_CREATED'])
        events=[{'event_type':'API_ENTRY','api':'WSAConnect'},
                {'event_type':'API_RETURN','api':'WSAConnect','eax':0,'matched':True}]
        self.assertTrue(progression(events)['CONNECT_ATTEMPTED'])
        self.assertEqual(progression(events)['state'],'CONNECTED')

    def test_branch_pass_is_not_acceptance(self):
        state=milestones([{'event_type':'COMPAT_BRANCH'}])
        self.assertFalse(any(state.values()))

    def test_graphics_failure_is_not_success(self):
        self.assertFalse(milestones([{'event_type':'GRAPHICS_RETURN','eax':0}])['GRAPHICS_RETURNED'])

    def test_string_requires_flow_and_nonzero_fields(self):
        events=[{'event_type':kind} for kind in ('INPUT_LOADER','SYSTEMMESSAGE_DISPATCH','STRING_LOADER')]
        events.append({'event_type':'COUNT_STORE','after_store':{'pointer':1234,'count':0}})
        self.assertFalse(milestones(events)['STRING_TABLE_INITIALIZED'])
        events[-1]['after_store']['count']=1
        self.assertTrue(milestones(events)['STRING_TABLE_INITIALIZED'])
        self.assertFalse(milestones(events[1:])['STRING_TABLE_INITIALIZED'])

    def test_network_attempt_is_not_success(self):
        events=[{'event_type':'API_ENTRY','api':'connect'},
                {'event_type':'API_RETURN','api':'connect','eax':0xffffffff,'matched':True},
                {'event_type':'API_RETURN','api':'send','eax':0xffffffff,'matched':True}]
        state=milestones(events)
        self.assertTrue(state['WINSOCK_REACHED']);self.assertFalse(state['CONNECTED']);self.assertFalse(state['FIRST_TX'])

    def test_matched_positive_network_returns(self):
        events=[{'event_type':'API_RETURN','api':'connect','eax':0,'matched':True},
                {'event_type':'API_RETURN','api':'send','eax':12,'matched':True}]
        self.assertTrue(milestones(events)['CONNECTED']);self.assertTrue(milestones(events)['FIRST_TX'])
        for e in events:e['matched']=False
        self.assertFalse(milestones(events)['CONNECTED']);self.assertFalse(milestones(events)['FIRST_TX'])


if __name__=='__main__':unittest.main()
