import jsonrpclib

class GethJSON:
    """ 
     Start a connnection to the geth json rpc 
     server, pointed by addr which is a tuple
     (host, port)
    """
    def __init__(self, addr):
        self.addr = addr
        self.server = jsonrpclib.Server(addr[0]+':'+str(addr[1]))

    def weiToEther(self, wei):
        ethInWei = 1000000000000000000
        return float(wei)/ethInWei

    def getAccounts(self):
        return self.server.eth_accounts()

    def getCoinbase(self):
        return self.server.eth_coinbase()

    def getMostRecentBlockNumber(self):
        return self.server.eth_blockNumber()

    def getGasPrice(self):
        return self.server.eth_gasPrice()

    def getIsMining(self):
        return self.server.eth_mining()

    def getHashrate(self):
        return self.server.eth_hashrate()

    def getBalance(self, account, tag='latest'):
        return int(self.server.eth_getBalance(account, tag), 16)

    def getDefaultBalance(self):
        coinbase = self.getCoinbase()
        return self.getBalance(coinbase)

    def getWork(self):
        ret = self.server.eth_getWork()
        dictRet = {
            'CurrentBlockHeader': ret[0],
            'DAGSeedHash': ret[1],
            'Target': ret[2]
        }
        return dictRet





if __name__ == '__main__':
    gethJSON = GethJSON(('http://localhost', 8545))


    

    