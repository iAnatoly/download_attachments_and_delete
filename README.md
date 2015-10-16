# Download and Delete

Simple script based on http://stackoverflow.com/questions/348630/how-can-i-download-all-emails-with-attachments-from-gmail
- more precisely, on http://stackoverflow.com/a/642988

I use it to download all the security alert form Samsung not-so-smart camera, which (due to complete lack of support) is
currently only able to send alerts/photos over SMTP.

Changes:
- Username/password are in config
- Infinite loop for downloading the messages as they arrive
- Removing the messages if attachment download is successful
- Minor refactoring and styling
