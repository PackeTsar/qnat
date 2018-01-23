import socket
import threading


config = {
	"forwarding":{
		221: {
			"ipv4": "192.168.1.10",
			"port": 22
			},
		222: {
			"ipv4": "192.168.1.1",
			"port": 22
			},
		}
	}


forwarders = {}


def startup():
	run = True
	for fwdr in config["forwarding"]:
		port = fwdr
		ipopts = config["forwarding"][fwdr]
		fwdr = forwarder(port, ipopts)
		forwarders.update({port: fwdr})
	while run:
		try:
			pass
		except KeyboardInterrupt:
			run = False
			print("Quitting Main")


class forwarder:
	def __init__(self, lis_port, dest_opts):
		self.quitting = False
		self.lis_port = lis_port
		self.dest_ip = dest_opts["ipv4"]
		self.dest_port = dest_opts["port"]
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


if __name__ == "__main__":
	startup()