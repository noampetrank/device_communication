from pydcomm.public.bugarpc import IRemoteProcedureClient, RemoteProcedureServer

class RPyCRemoteProcedureClient(IRemoteProcedureClient):
    def __init__(self, ip_port):
        import rpyc

        ip, port = ip_port.split(":")
        port = int(port)

        self.server = rpyc.connect(ip, port)

    def call(self, procedure_name, params):
        return self.server.root.call(procedure_name, params)

    def get_version(self):
        return "rypc-v1.0.0"

    def stop(self):
        try:
            self.call('_rpc_stop', '')
        except EOFError:
            pass


class RPyCRemoteProcedureServer(RemoteProcedureServer):
    def __init__(self):
        self.server = None

    def listen(self, executor, rpc_id, wait):
        assert wait, "Currently only wait option is implemented."
        import rpyc
        self_ = self

        class RPyCService(rpyc.Service):
            def exposed_call(self, procedure_name, params):
                if procedure_name == "_rpc_get_version":
                    return executor.get_version()
                elif procedure_name == "_rpc_stop":
                    self_.server.close()
                    return
                elif procedure_name == "_rpc_device_time_usec":
                    import time
                    return str(time.time() * 1000)
                else:
                    return executor.execute_procedure(procedure_name, params)

        self.server = rpyc.OneShotServer(RPyCService, port=rpc_id)
        self.server.start()

    def wait(self):
        raise NotImplementedError("RPyCRemoteProcedureServer can't wait")

    def stop(self):
        if self.server is not None:
            self.server.close()


def test_RPyC():
    from pydcomm.rpc.buga_grpc_server import BugaEchoExecutor

    def start_server():
        server = RPyCRemoteProcedureServer()
        server.listen(BugaEchoExecutor(), 18861, True)

    from threading import Thread
    server_thread = Thread(target=start_server)
    server_thread.start()

    import time
    from socket import error
    client = None
    for _ in range(20):
        try:
            client = RPyCRemoteProcedureClient("localhost:18861")
            break
        except error:
            time.sleep(0.1)
    else:
        raise RuntimeError("RPyCRemoteProcedureClient failed to connect to RPyCRemoteProcedureServer")

    try:
        assert client.get_executor_version() == BugaEchoExecutor().get_version(), "RPyCRemoteProcedureServer returned incorrect executor version"

        ret = client.call("yes", "yes")
        assert ret == "yes", "RPyCRemoteProcedureServer returned incorrect echo: 'yes' != {!r}".format(ret)

        ret = client.call("yes", 1)
        assert ret == 1, "RPyCRemoteProcedureServer returned incorrect echo: 1 != {!r}".format(ret)
    finally:
        # Test stop doesn't throw or hang.
        client.stop()


if __name__ == "__main__":
    test_RPyC()
