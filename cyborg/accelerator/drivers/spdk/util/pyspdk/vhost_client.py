import json


class VhostTgt(object):

    def __init__(self, py):
        super(VhostTgt, self).__init__()
        self.py = py

    def get_rpc_methods(self):
        rpc_methods = self._get_json_objs('get_rpc_methods', '127.0.0.1')
        return rpc_methods

    def get_scsi_devices(self):
        scsi_devices = self._get_json_objs(
            'get_scsi_devices', '127.0.0.1')
        return scsi_devices

    def get_luns(self):
        luns = self._get_json_objs('get_luns', '127.0.0.1')
        return luns

    def get_interfaces(self):
        interfaces = self._get_json_objs(
            'get_interfaces', '127.0.0.1')
        return interfaces

    def add_ip_address(self, ifc_index, ip_addr):
        sub_args = [ifc_index, ip_addr]
        res = self.py.exec_rpc(
            'add_ip_address',
            '127.0.0.1',
            sub_args=sub_args)
        return res

    def delete_ip_address(self, ifc_index, ip_addr):
        sub_args = [ifc_index, ip_addr]
        res = self.py.exec_rpc(
            'delete_ip_address',
            '127.0.0.1',
            sub_args=sub_args)
        return res

    def get_bdevs(self):
        block_devices = self._get_json_objs(
            'get_bdevs', '127.0.0.1')
        return block_devices

    def delete_bdev(self, name):
        sub_args = [name]
        res = self.py.exec_rpc('delete_bdev', '127.0.0.1', sub_args=sub_args)
        print res

    def kill_instance(self, sig_name):
        sub_args = [sig_name]
        res = self.py.exec_rpc('kill_instance', '127.0.0.1', sub_args=sub_args)
        print res

    def construct_aio_bdev(self, filename, name, block_size):
        sub_args = [filename, name, str(block_size)]
        res = self.py.exec_rpc(
            'construct_aio_bdev',
            '127.0.0.1',
            sub_args=sub_args)
        print res

    def construct_error_bdev(self, basename):
        sub_args = [basename]
        res = self.py.exec_rpc(
            'construct_error_bdev',
            '127.0.0.1',
            sub_args=sub_args)
        print res

    def construct_nvme_bdev(
            self,
            name,
            trtype,
            traddr,
            adrfam=None,
            trsvcid=None,
            subnqn=None):
        sub_args = ["-b", "-t", "-a"]
        sub_args.insert(1, name)
        sub_args.insert(2, trtype)
        sub_args.insert(3, traddr)
        if adrfam is not None:
            sub_args.append("-f")
            sub_args.append(adrfam)
        if trsvcid is not None:
            sub_args.append("-s")
            sub_args.append(trsvcid)
        if subnqn is not None:
            sub_args.append("-n")
            sub_args.append(subnqn)
        res = self.py.exec_rpc(
            'construct_nvme_bdev',
            '127.0.0.1',
            sub_args=sub_args)
        return res

    def construct_null_bdev(self, name, total_size, block_size):
        sub_args = [name, str(total_size), str(block_size)]
        res = self.py.exec_rpc(
            'construct_null_bdev',
            '127.0.0.1',
            sub_args=sub_args)
        return res

    def construct_malloc_bdev(self, total_size, block_size):
        sub_args = [str(total_size), str(block_size)]
        res = self.py.exec_rpc(
            'construct_malloc_bdev',
            '10.0.2.15',
            sub_args=sub_args)
        print res

    def _get_json_objs(self, method, server_ip):
        res = self.py.exec_rpc(method, server_ip)
        json_obj = json.loads(res)
        return json_obj
