import email, imaplib, os, sys, time
from config import detach_dir, user, pwd, server


def fetch_and_save():
    m = imaplib.IMAP4_SSL(server)
    m.login(user, pwd)

    print('logged in as ' + user)

    m.select("[Gmail]/All Mail")

    resp, items = m.search(None, "ALL")
    items = items[0].split()  # getting the msg id

    print('Found {} items'.format(len(items)))

    for msg_id in items:
        resp, data = m.fetch(msg_id, "(RFC822)")  # fetching the whole message

        if not data or not data[0]:
            print('data part of the attchment is empty')
            continue

        email_body = data[0][1]  # getting the mail content
        mail = email.message_from_string(email_body)  # parsing the mail content to get a mail object

        # Check if any attachments at all
        if mail.get_content_maintype() != 'multipart':
            continue

        print('Processing email from: {}; Subject: {}'.format(mail["From"], mail["Subject"]))

        allow_delete = False

        # we use walk to create a generator so we can iterate on the parts and forget about the recursive headach
        for part in mail.walk():
            if process_part(part):
                allow_delete = True # delete email if at least one attachment was aved

        if allow_delete:
            print('Deleting message {}'.format(msg_id))
            m.store(msg_id, '+X-GM-LABELS', '\\Trash')
            m.expunge()


def process_part(part):
    # multipart are just containers, so we skip them
    if part.get_content_maintype() == 'multipart':
        print('Skipping multipart')
        return False

    # is this part an attachment ?
    if not part.get('Content-Disposition'):
        print('Empty content-disposition')
        return False

    filename = part.get_filename()
    counter = 1

    # if there is no filename, we create one with a counter to avoid duplicates
    if not filename:
        print('empty filename; using a surrogate')
        filename = 'part-%03d%s' % (counter, 'bin')
        counter += 1

    att_path = os.path.join(detach_dir, filename)

    # Check if its already there
    if not os.path.isfile(att_path):
        sys.stdout.write('.')
        # finally write the stuff
        fp = open(att_path, 'wb')
        fp.write(part.get_payload(decode=True))
        fp.close()
        return True
    else:
        print('File already exists: {}'.format(att_path))
        return False


def main():
    while True:
        try:
            fetch_and_save()
            print('sleeping for 60 seconds')
            time.sleep(60)
        except Exception as ex:
            print(ex)


if __name__ == '__main__':
    main()
