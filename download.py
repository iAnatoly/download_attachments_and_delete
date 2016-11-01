# A simple script for downloading all attachments from Gmail mailbox
# see @README.md

import email
import imaplib
import os
import time
import datetime
import socket
import email.Header

socket.setdefaulttimeout(10)

#from config import detach_dir, user, pwd, server
import config

class FileNameProvider:
    def __init__(self, basename='part'):
        self.counter = 1
        self.default_ext = 'jpg'
        self.template = '{}-{:03d}.jpg'
        self.basename = basename

    def get_surrogate_filename(self):
        filename = self.template.format(self.basename, self.counter)
        self.counter += 1
        return filename

    def get_unique_name(self, path, filename):
        i = 1
        result = os.path.join(path, filename)
        while True:
            if not os.path.isfile(result):
                return result
            result = os.path.join(path, self.template.format(self.basename, i))
	    i += 1


class AttachmentFetcher:
    def __init__(self):
        self.BACKOFF_NORMAL = config.backoff_period
        self.BACKOFF_ERROR = config.backoff_period * 2
        self.INBOX_LABEL = config.label #'"[Gmail]/All Mail"'
        self.CRITERIA = 'ALL'

    def fetch_and_save(self):
        m = imaplib.IMAP4_SSL(config.server)
        m.login(config.user, config.pwd)


        print('------- BEGINNING OF FETCH CYCLE: {} ({})-------'.format(datetime.datetime.now(), config.user))

        m.select(self.INBOX_LABEL)

        resp, items = m.search(None, self.CRITERIA)
        items = items[0].split()  # getting the msg id

        print('INFO: Found {} item(s)'.format(len(items)))

	processed_items = 0

        for msg_id in items:
	    if processed_items >= config.batch_size:
		print('Processed {} items; backing off'.format(processed_items))
		break

            resp, data = m.fetch(msg_id, '(RFC822)')  # fetching the whole message

            if not data or not data[0]:
                print('WARN: data part of the attachment is empty (we are probably being throttled)')
                break

            if self.process_email(data):
                print('INFO: Deleting message {}'.format(msg_id.decode('utf-8')))
                m.store(msg_id, '+X-GM-LABELS', '\\Trash')
                m.expunge()
		processed_items += 1
        print('------- END OF FETCH CYCLE: {} -------'.format(datetime.datetime.now()))
	if processed_items == 0:
	     print("No emails with attachments left; exiting.")
	     return 0
	
	return 1


    def process_email(self, data):
        email_body = data[0][1]  # getting the mail content
        mail = email.message_from_string(email_body.decode('utf-8'))  # parsing the mail content to get a mail object

        # Check if any attachments at all
        if mail.get_content_maintype() != 'multipart':
            return False

	mail_from, encoding = email.Header.decode_header(mail['From'])[0]
	mail_subject = email.Header.decode_header(mail['Subject'])[0]
        print('INFO: Processing email from: "{}"; Subject: "{}"'.format(mail_from, mail_subject))

        processed_at_least_one_attachment = False

        name_provider = FileNameProvider()

        for part in mail.walk():
            if self.process_part(part, name_provider):
                processed_at_least_one_attachment = True  # delete email if at least one attachment was aved
        return processed_at_least_one_attachment

    def process_part(self, part, name_provider):
        # multipart are just containers, so we skip them
        if part.get_content_maintype() == 'multipart':
            return False

        # Empty Content-Disposition means it is not an attachment
        if not part.get('Content-Disposition'):
            return False

        filename = part.get_filename()

	if filename:
	    filename, encoding = email.Header.decode_header(filename)[0]
        if not filename:
            filename = name_provider.get_surrogate_filename()
            print('WARN: empty filename; using a surrogate: {}'.format(filename))


        att_path = name_provider.get_unique_name(config.detach_dir, filename)
        return self.save_payload(att_path, part.get_payload(decode=True))

    @staticmethod
    def save_payload(path, payload):
        try:
            fp = open(path, 'wb')
            fp.write(payload)
            fp.close()
            return True
        except Exception as ex:
            print(ex)
            return False

    def fetch_forever(self):
        while True:
            try:
                if not self.fetch_and_save(): break
                print('INFO: sleeping for {} seconds'.format(self.BACKOFF_NORMAL))
                time.sleep(self.BACKOFF_NORMAL)
            except Exception as ex:
                print('ERR: {}'.format(ex))
                print('INFO: Retrying in {} seconds'.format(self.BACKOFF_ERROR))
                time.sleep(self.BACKOFF_ERROR)


def main():
    fetcher = AttachmentFetcher()
    fetcher.fetch_forever()

if __name__ == '__main__':
    main()
