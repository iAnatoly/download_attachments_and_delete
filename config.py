detach_dir = 'downloads' 		# save all attachments in cwd
user = 'user.name@gmail.com'	# username
pwd = ''                		# password. Use application password in case of 2FA 
server = 'imap.gmail.com'		# server. usually the same for everyone
batch_size = 1000			    # number of messages to scan before backing off
backoff_period = 300 			# number of seconds to back off for
label = "[Gmail]/All Mail"	    # The label to scan. For all mail, choose '"[Gmail]/All Mail"'
search_criteria = "has:attachment jpg larger:256K"  # gmail search string
