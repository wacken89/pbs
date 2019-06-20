import random
import time
import sys

user = ("John Sonner", "Adam Walker", "Frank Sinatra", "Alex Baldwin", "Stefany Frizzell")
level = ("INFO", "WARNING", "FAIL", "CRITICAL", "DISASTER") 
message = ("User parameters updating fails", "Something goes wrong with server", "Payment disabled for user", "Connection lost", "API not availiable")

while True:
	num = random.randrange(0,5)
	print(level[num] + ' \"' + user[num] + '\" \"' + message[num] + '\"')
	time.sleep(10)