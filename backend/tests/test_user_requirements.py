import unittest
from unittest.mock import patch, MagicMock
from app.services.verification_service import verification_service

class TestUserRequirements(unittest.TestCase):

    def test_1_invalid_syntax(self):
        res = verification_service.verify_email('xyy@gmail..com')
        self.assertEqual(res.email_format, 'INVALID')
        self.assertEqual(res.status, 'INVALID')
        self.assertEqual(res.classification, 'INVALID')
        self.assertEqual(res.data_sent, False)

    def test_2_non_existent_domain(self):
        res = verification_service.verify_email('user@nonexistent-domain-xyz-99999.com')
        self.assertEqual(res.status, 'INVALID')
        self.assertEqual(res.domain_status, 'INVALID')
        self.assertEqual(res.data_sent, False)

    def test_3_domain_without_mx(self):
        with patch('app.services.verification_service.dns_service.check_domain_dns') as mock_dns:
            mock_dns.return_value = {
                'domain': 'nomxdomain.com',
                'is_resolvable': True,
                'has_mx': False,
                'mx_records': [],
                'a_records': ['1.2.3.4'],
                'error': None,
                'is_timeout': False
            }
            res = verification_service.verify_email('user@nomxdomain.com')
            self.assertEqual(res.status, 'INVALID')
            self.assertEqual(res.mx_status, 'MISSING')
            self.assertEqual(res.data_sent, False)

    def test_4_smtp_permanent_rejection(self):
        with patch('app.services.verification_service.smtp_service.verify_mailbox_smtp') as mock_smtp:
            mock_smtp.return_value = {
                'attempted': True,
                'connected': True,
                'smtp_status': 'REJECTED',
                'mailbox_status': 'NOT_FOUND',
                'is_catch_all': False,
                'server_code': 550,
                'server_message': '550 5.1.1 <user@example.com>: Recipient address rejected: User unknown',
                'mx_host_used': 'mx.example.com',
                'data_sent': False,
                'smtp_trace': {
                    'attempted': True,
                    'connected': True,
                    'hostname': 'mx.example.com',
                    'port': 25,
                    'stage': 'RCPT_TO',
                    'greeting': {'code': 220, 'response': '220 mx.example.com ESMTP'},
                    'ehlo': {'code': 250, 'response': '250 OK'},
                    'mail_from': {'code': 250, 'response': '250 Sender OK'},
                    'rcpt_to': {'code': 550, 'response': '550 5.1.1 User unknown'},
                    'data_sent': False,
                    'catch_all_probe': None,
                    'attempted_servers': []
                },
                'details': {'stage': 'RCPT_TO', 'code': 550}
            }
            res = verification_service.verify_email('user@example.com')
            self.assertEqual(res.status, 'INVALID')
            self.assertEqual(res.classification, 'INVALID')
            self.assertEqual(res.data_sent, False)
            self.assertEqual(res.smtp['data_sent'], False)

    def test_5_smtp_acceptance(self):
        with patch('app.services.verification_service.smtp_service.verify_mailbox_smtp') as mock_smtp:
            mock_smtp.return_value = {
                'attempted': True,
                'connected': True,
                'smtp_status': 'ACCEPTED',
                'mailbox_status': 'CONFIRMED',
                'is_catch_all': False,
                'server_code': 250,
                'server_message': '250 2.1.5 Recipient OK',
                'mx_host_used': 'mx.example.com',
                'data_sent': False,
                'smtp_trace': {
                    'attempted': True,
                    'connected': True,
                    'hostname': 'mx.example.com',
                    'port': 25,
                    'stage': 'RCPT_TO',
                    'greeting': {'code': 220, 'response': '220 mx.example.com ESMTP'},
                    'ehlo': {'code': 250, 'response': '250 OK'},
                    'mail_from': {'code': 250, 'response': '250 Sender OK'},
                    'rcpt_to': {'code': 250, 'response': '250 Recipient OK'},
                    'data_sent': False,
                    'catch_all_probe': {'tested': True, 'code': 550, 'is_catch_all': False},
                    'attempted_servers': []
                },
                'details': {'stage': 'RCPT_TO', 'code': 250}
            }
            res = verification_service.verify_email('user@example.com')
            self.assertEqual(res.status, 'VALID')
            self.assertEqual(res.classification, 'REAL')
            self.assertEqual(res.final_status, 'REAL / REACHABLE')
            self.assertEqual(res.data_sent, False)
            self.assertEqual(res.smtp['data_sent'], False)

    def test_6_temporary_smtp_failure(self):
        with patch('app.services.verification_service.smtp_service.verify_mailbox_smtp') as mock_smtp:
            mock_smtp.return_value = {
                'attempted': True,
                'connected': True,
                'smtp_status': 'GREYLISTED',
                'mailbox_status': 'UNCONFIRMED',
                'is_catch_all': False,
                'server_code': 421,
                'server_message': '421 4.7.0 Service unavailable, try again later',
                'mx_host_used': 'mx.example.com',
                'data_sent': False,
                'smtp_trace': {
                    'attempted': True,
                    'connected': True,
                    'hostname': 'mx.example.com',
                    'port': 25,
                    'stage': 'RCPT_TO',
                    'greeting': {'code': 220, 'response': '220 mx.example.com ESMTP'},
                    'ehlo': {'code': 250, 'response': '250 OK'},
                    'mail_from': {'code': 250, 'response': '250 Sender OK'},
                    'rcpt_to': {'code': 421, 'response': '421 4.7.0 Service unavailable'},
                    'data_sent': False,
                    'catch_all_probe': None,
                    'attempted_servers': []
                },
                'details': {'stage': 'RCPT_TO', 'code': 421}
            }
            res = verification_service.verify_email('user@example.com')
            self.assertEqual(res.status, 'UNKNOWN')
            self.assertEqual(res.classification, 'UNKNOWN')
            self.assertEqual(res.data_sent, False)

    def test_7_smtp_timeout(self):
        with patch('app.services.verification_service.smtp_service.verify_mailbox_smtp') as mock_smtp:
            mock_smtp.return_value = {
                'attempted': True,
                'connected': False,
                'smtp_status': 'TIMEOUT',
                'mailbox_status': 'UNCONFIRMED',
                'is_catch_all': False,
                'server_code': None,
                'server_message': 'SMTP probe connection to mx.example.com:25 timed out.',
                'mx_host_used': 'mx.example.com',
                'data_sent': False,
                'smtp_trace': {
                    'attempted': True,
                    'connected': False,
                    'hostname': 'mx.example.com',
                    'port': 25,
                    'stage': 'CONNECT_TIMEOUT',
                    'greeting': None,
                    'ehlo': None,
                    'mail_from': None,
                    'rcpt_to': None,
                    'data_sent': False,
                    'catch_all_probe': None,
                    'attempted_servers': []
                },
                'details': {'error': 'Connection timed out'}
            }
            res = verification_service.verify_email('user@example.com')
            self.assertEqual(res.status, 'UNKNOWN')
            self.assertEqual(res.classification, 'UNKNOWN')
            self.assertEqual(res.data_sent, False)

    def test_8_catch_all_domain(self):
        with patch('app.services.verification_service.smtp_service.verify_mailbox_smtp') as mock_smtp:
            mock_smtp.return_value = {
                'attempted': True,
                'connected': True,
                'smtp_status': 'ACCEPTED',
                'mailbox_status': 'CATCH_ALL',
                'is_catch_all': True,
                'server_code': 250,
                'server_message': 'Receiving server accepts arbitrary recipients, so individual mailbox existence cannot be confirmed.',
                'mx_host_used': 'mx.example.com',
                'data_sent': False,
                'smtp_trace': {
                    'attempted': True,
                    'connected': True,
                    'hostname': 'mx.example.com',
                    'port': 25,
                    'stage': 'RCPT_TO',
                    'greeting': {'code': 220, 'response': '220 mx.example.com ESMTP'},
                    'ehlo': {'code': 250, 'response': '250 OK'},
                    'mail_from': {'code': 250, 'response': '250 Sender OK'},
                    'rcpt_to': {'code': 250, 'response': '250 Recipient OK'},
                    'data_sent': False,
                    'catch_all_probe': {'tested': True, 'code': 250, 'is_catch_all': True},
                    'attempted_servers': []
                },
                'details': {'stage': 'RCPT_TO', 'code': 250, 'is_catch_all': True}
            }
            res = verification_service.verify_email('user@example.com')
            self.assertEqual(res.status, 'RISKY')
            self.assertEqual(res.classification, 'RISKY')
            self.assertEqual(res.data_sent, False)

    def test_9_disposable_domain(self):
        res = verification_service.verify_email('test@mailinator.com')
        self.assertEqual(res.disposable_detected, True)
        self.assertEqual(res.data_sent, False)

    def test_10_role_account(self):
        res = verification_service.verify_email('info@example.com')
        self.assertEqual(res.role_account_detected, True)
        self.assertEqual(res.data_sent, False)

    def test_11_multiple_mx_records(self):
        with patch('app.services.verification_service.dns_service.check_domain_dns') as mock_dns:
            mock_dns.return_value = {
                'domain': 'multimx.com',
                'is_resolvable': True,
                'has_mx': True,
                'mx_records': [
                    {'priority': 10, 'host': 'mx1.multimx.com'},
                    {'priority': 20, 'host': 'mx2.multimx.com'}
                ],
                'a_records': ['1.2.3.4'],
                'error': None,
                'is_timeout': False
            }
            with patch('app.services.verification_service.smtp_service.verify_mailbox_smtp') as mock_smtp:
                mock_smtp.return_value = {
                    'attempted': True,
                    'connected': True,
                    'smtp_status': 'ACCEPTED',
                    'mailbox_status': 'CONFIRMED',
                    'is_catch_all': False,
                    'server_code': 250,
                    'server_message': '250 OK',
                    'mx_host_used': 'mx1.multimx.com',
                    'data_sent': False,
                    'smtp_trace': {
                        'attempted': True,
                        'connected': True,
                        'hostname': 'mx1.multimx.com',
                        'port': 25,
                        'stage': 'RCPT_TO',
                        'greeting': {'code': 220, 'response': '220 OK'},
                        'ehlo': {'code': 250, 'response': '250 OK'},
                        'mail_from': {'code': 250, 'response': '250 OK'},
                        'rcpt_to': {'code': 250, 'response': '250 OK'},
                        'data_sent': False,
                        'catch_all_probe': None,
                        'attempted_servers': [{'host': 'mx1.multimx.com'}]
                    },
                    'details': {}
                }
                res = verification_service.verify_email('user@multimx.com')
                self.assertEqual(res.status, 'VALID')
                self.assertEqual(res.data_sent, False)

    def test_12_provider_hiding_recipient_existence(self):
        with patch('app.services.verification_service.smtp_service.verify_mailbox_smtp') as mock_smtp:
            mock_smtp.return_value = {
                'attempted': True,
                'connected': False,
                'smtp_status': 'BLOCKED',
                'mailbox_status': 'UNCONFIRMED',
                'is_catch_all': False,
                'server_code': None,
                'server_message': 'Port 25 outbound network restriction or connection error for mx.provider.com: Connection timed out.',
                'mx_host_used': 'mx.provider.com',
                'data_sent': False,
                'smtp_trace': {
                    'attempted': True,
                    'connected': False,
                    'hostname': 'mx.provider.com',
                    'port': 25,
                    'stage': 'CONNECT_ERROR',
                    'greeting': None,
                    'ehlo': None,
                    'mail_from': None,
                    'rcpt_to': None,
                    'data_sent': False,
                    'catch_all_probe': None,
                    'attempted_servers': []
                },
                'details': {'error': 'Connection timed out'}
            }
            res = verification_service.verify_email('user@example.com')
            self.assertEqual(res.status, 'UNKNOWN')
            self.assertEqual(res.classification, 'UNKNOWN')
            self.assertEqual(res.data_sent, False)

if __name__ == '__main__':
    unittest.main()
