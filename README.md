# keylog
Simple Python keylogger for windows developed as an exercise for the Principles of Cybersecurity subject in the MSc. 

Main features:

a. Locally store keystrokes from the keyboard where the keylogger is installed.

b. Send by mail with a periodicity of 2 hours all the recorded keystrokes.

c. When the keylogger does not detect keystrokes for more than 5 minutes it must give a line break for the next time it registers keystrokes.

d. Add the possibility that the keylogger is running in the background, so that the user who installs it is not easily able to detect the keylogger.

In order to fulfill this part, the user must compile the script by using the command: "Pyinstaller -F -w "

e. Add a function to export the recorded keystrokes manually, so that when you demonstrate the keylogger it will be easier.
