import sys
import json
import socket
import threading



def startup():
	run = True
	for fwdr in config["forwarding"]:
		port = fwdr
		ipopts = config["forwarding"][fwdr]
		fwdr = class_forwarder(port, ipopts)
		forwarders.update({port: fwdr})
	while run:
		try:
			pass
		except KeyboardInterrupt:
			run = False
			print("Quitting Main")



class class_forwarder:
	def __init__(self, lis_port, dest_opts):
		self.quitting = False
		self.lis_port = int(lis_port)
		self.dest_ip = dest_opts["ipv4"]
		self.dest_port = int(dest_opts["port"])
		self.threads = []
		self.start()
	def start(self):
		print("Starting forwarder 0.0.0.0:%s --> %s:%s" % (str(self.lis_port), self.dest_ip, str(self.dest_port)))
		lis_thread = threading.Thread(target=self._listener)
		lis_thread.daemon = True
		lis_thread.start() # Start talker thread to listen to port
		self.threads.append(lis_thread)
	def _listener(self):
		while True:
			ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # v6 family
			ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			ssock.bind(("", self.lis_port))
			ssock.listen(1024)
			client, addr = ssock.accept()
			print("Forwarder %s: Recieved connection from %s:%s" % (self.lis_port, addr[0], str(addr[1])))
			target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			target.connect((self.dest_ip, self.dest_port))
			cli_thread = threading.Thread(target=self._talker, args=(client,target))
			cli_thread.daemon = True
			cli_thread.start() # Start talker thread to listen to port
			self.threads.append(cli_thread)
			tar_thread = threading.Thread(target=self._talker, args=(target,client))
			tar_thread.daemon = True
			tar_thread.start() # Start talker thread to listen to port
			self.threads.append(tar_thread)
	def _talker(self, client, target):
		while True:
			try:
				if self.quitting:
					target.close()
					return None
				recieve = client.recv(1024)
				target.send(recieve)
			except socket.error:
				return None



def make_config(options, args):
	global config
	if options["config_file"]:
		f = open(options["config_file"])
		data = f.read()
		f.close()
		config = json.loads(data)
	else:
		if options["destination_port"] and options["destination_ip"] and options["listening_port"]:
			int(options["destination_port"])  # Must be an integer
			int(options["listening_port"])  # Must be an integer
			config = {
				"forwarding": {
					options["listening_port"]: {
						"ipv4": options["destination_ip"],
						"port": options["destination_port"]
						}
					}
				}
		else:
			print("ERROR: You must provide either: (a config file path) or (a destination IP, a destination port, and a listening port)")
			sys.exit()



if __name__ == "__main__":
	from optparse import OptionParser,OptionGroup
	global forwarders
	forwarders = {}
	parser = OptionParser()
	parser.add_option("-c", "--config_file", dest="config_file",
		help="JSON file with forwarding configuration", metavar="CONFIG_FILE_PATH")
	parser.add_option("-l", "--listening_port", dest="listening_port",
		help="TCP port to listen on", metavar="LISTENTING_PORT")
	parser.add_option("-i", "--destination_ip", dest="destination_ip",
		help="IP address of the destination", metavar="DESTINATION_IP")
	parser.add_option("-p", "--destination_port", dest="destination_port",
		help="TCP port on the destination", metavar="DESTINATION_PORT")
	(options, args) = parser.parse_args()
	options = vars(options)
	make_config(options, args)
	startup()
