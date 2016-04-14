# A simple script for downloading all attachments from Gmail mailbox
# see @README.md

import email
import imaplib
import os
import time
import datetime
import socket

socket.setdefaulttimeout(10)

from config import detach_dir, user, pwd, server


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


class AttachmentFetcher:
    def __init__(self):
        self.BACKOFF_NORMAL = 60
        self.BACKOFF_ERROR = 60
        self.INBOX_LABEL = "[Gmail]/All Mail"
        self.CRITERIA = "ALL"

    def fetch_and_save(self):
        m = imaplib.IMAP4_SSL(server)
        m.login(user, pwd)


        print('------- BEGINNING OF FETCH CYCLE: {} ({})-------'.format(datetime.datetime.now(), user))

        m.select(self.INBOX_LABEL)

        resp, items = m.search(None, self.CRITERIA)
        items = items[0].split()  # getting the msg id

        print('INFO: Found {} item(s)'.format(len(items)))

        for msg_id in items:
            resp, data = m.fetch(msg_id, '(RFC822)')  # fetching the whole message

            if not data or not data[0]:
                print('WARN: data part of the attachment is empty (we are probably being throttled)')
                break

            if self.process_email(data):
                print('INFO: Deleting message {}'.format(msg_id))
                m.store(msg_id, '+X-GM-LABELS', '\\Trash')
                m.expunge()
        print('------- END OF FETCH CYCLE: {} -------'.format(datetime.datetime.now()))


    def process_email(self, data):
        email_body = data[0][1]  # getting the mail content
        mail = email.message_from_string(email_body)  # parsing the mail content to get a mail object

        # Check if any attachments at all
        if mail.get_content_maintype() != 'multipart':
            return False

        print('INFO: Processing email from: "{}"; Subject: "{}"'.format(mail['From'], mail['Subject']))

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

        if not filename:
            filename = name_provider.get_surrogate_filename()
            print('WARN: empty filename; using a surrogate: {}'.format(filename))


        att_path = name_provider.get_unique_name(detach_dir, filename)
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
                self.fetch_and_save()
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
