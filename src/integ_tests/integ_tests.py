#!/usr/bin/python
import unittest, smtpd, asyncore
import os, sys, threading, json

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/..")
import server, database, email_utils, config

test_account='test@test.com'
test_event_id = '1'
test_event_location = 'Tokyo'
num_notification = 0
num_email = 0
wait_num_notification = threading.Semaphore(0)
wait_num_email = threading.Semaphore(0)
wait_smtp = threading.Semaphore(0)

(db_file, secret_token, smtp_context) = config_service = config.get_config('configs/test.ini')

# Mocked SMTP Server
# Count how many emails/notifications are sent
class MockSMTPServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, mail_options=None, rcpt_options=None):
        global num_notification, num_email
        if mailfrom == rcpttos[0]:
            num_notification += 1
            wait_num_notification.release()
        else:
            num_email += 1
            wait_num_email.release()

        print ('Receiving message from:', peer)
        print ('Message addressed from:', mailfrom)
        print ('Message addressed to  :', rcpttos)
        print ('Message length        :', len(data))
        print(data)
        return

def wait_for_num_notification():
    wait_num_notification.acquire()
    return num_notification

def wait_for_num_email():
    wait_num_email.acquire()
    return num_email

class TestAPIMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        def thread_func():
            global smtp_context
            MockSMTPServer((smtp_context.smtp_server, smtp_context.port), None)
            wait_smtp.release()
            asyncore.loop()
        threading.Thread(target=thread_func, args=(), daemon=True).start()
        wait_smtp.acquire()

    def setUp(self):
        global smtp_context, db_file, secret_token
        self.db_file = db_file
        s = server.Service(db_file, secret_token, smtp_context)
        self.client = s.get_test_client()

        global num_notification, num_email
        num_notification = 0
        num_email = 0

    def tearDown(self):
        conn = database.open_connection(self.db_file)
        conn.execute("DELETE FROM attendings")
        conn.execute("DELETE FROM users")
        conn.commit()

    def count_events(self, email):
        conn = database.open_connection(self.db_file)
        return database.count_events(conn, email)

    def test_list_events(self):
        resp = self.client.get("/events")

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(x["id"] == test_event_id for x in resp.json))

    def test_register_event(self):
        url = "/register/%s/%s" % (test_account, test_event_id)
        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.count_events(test_account) == 1)
        self.assertTrue(wait_for_num_notification() == 1)

    def test_register_non_exsiting_event(self):
        url = "/register/%s/01234" % test_account
        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 400)
        self.assertTrue(self.count_events(test_account) == 0)
        self.assertTrue(wait_for_num_notification() == 0)

    def test_list_user_events(self):

        self.client.post("/register/%s/%s" % (test_account, test_event_id))
        resp = self.client.get("/users/%s" % test_account)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(x["id"] == test_event_id for x in resp.json))
        self.assertFalse('London' in str(resp.data))

    def test_list_non_exisitng_user_events(self):

        resp = self.client.get("/users/%s" % test_account)

        self.assertEqual(resp.status_code, 200)

    def test_register_event_twice(self):
        url = "/register/%s/%s" % (test_account, test_event_id)
        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.count_events(test_account) == 1)
        url = "/register/%s/%s" % (test_account, test_event_id)
        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.count_events(test_account) == 1)
        self.assertTrue(wait_for_num_notification() == 1)
        self.assertTrue(wait_for_num_email() == 1)

    def test_unregister_event(self):
        url = "/register/%s/%s" % (test_account, test_event_id)
        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.count_events(test_account) == 1)
        url = "/register/%s/%s" % (test_account, test_event_id)
        resp = self.client.delete(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.count_events(test_account) == 0)
        self.assertTrue(wait_for_num_notification() == 1)

    def test_unregister_non_existing_event(self):
        url = "/register/%s/%s" % (test_account, test_event_id)
        resp = self.client.delete(url)

        self.assertEqual(resp.status_code, 400)

    def test_add_and_delete_event(self):
        params = {}
        params['name'] = 'New_event'
        params['location'] = 'Sky'
        params['start_timestamp'] = '2020'
        params['end_timestamp'] = '2021'

        # Add event
        resp = self.client.post("/events", json=params)
        self.assertEqual(resp.status_code, 200)
        event_id = resp.json['event_id']

        # Check event exists
        resp = self.client.get("/events")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(x["id"] == event_id for x in resp.json))

        resp = self.client.get("/event/%s" % event_id)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["id"] == event_id)

        # Delete event
        resp = self.client.delete("/event/%s" % event_id)
        self.assertEqual(resp.status_code, 200)

        # Check event has been removed
        resp = self.client.get("/events")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(any(x["id"] == event_id for x in resp.json))

        resp = self.client.get("/event/%s" % event_id)
        self.assertEqual(resp.status_code, 400)

    def test_add_event_missing_params(self):
        params = {}
        params['name'] = 'New_event'
        params['start_timestamp'] = '2020'
        params['end_timestamp'] = '2021'

        # Add event
        resp = self.client.post("/events", json=params)
        self.assertEqual(resp.status_code, 400)

    def test_delete_nonexisting_event(self):
        resp = self.client.delete("/event/%s" % 42)
        self.assertEqual(resp.status_code, 400)

    def test_admin_wrong_token(self):
        url = "/admin/%s/%s" % ('NOSECRET', test_event_id)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 401)

    def test_admin_valid_token(self):
        url = "/register/%s/%s" % (test_account, test_event_id)
        resp = self.client.post(url)

        url = "/admin/%s/%s" % (secret_token, test_event_id)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("test@test" in str(resp.data))

    def test_admin_valid_token_non_existing_event(self):
        url = "/admin/%s/%s" % (secret_token, 42)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 400)

if __name__ == '__main__':
    unittest.main()
