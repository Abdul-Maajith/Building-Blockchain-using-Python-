# Importing the libraries
import datetime
import hashlib
import json
import requests 
from flask import Flask, jsonify, request
from uuid import uuid4  
from urllib.parse import urlparse

# Part 1 - Building a blockchain
class Blockchain:
    def __init__(self):
        self.chain = [] #Initializing chain of block 
        self.transactions = [] # Contains all txns
        self.create_block(proof = 1, previous_hash = '0') # Genesis block 
        self.nodes = set() # Address(url) of different

    # Creating (or) adding a block, after mining..
    def create_block(self, proof, previous_hash):
        block = { 
            "index": len(self.chain) + 1, 
            "timestamp":str(datetime.datetime.now()),
            "proof": proof, 
            "previous_hash": previous_hash, 
            "transactions": self.transactions
        }

        # After creating a block with the old txn's, we must empty the txn
        self.transactions = []
        self.chain.append(block)
        return block
   
    # Getting the last block in the chain
    def get_previous_block(self):
        return self.chain[-1]

    # Proof of work - Cracking CryptoPuzzle using trial & error method
    # Here, new_Proof - hash() which is been founded by hit & trial method 
    # Proof = Nounce
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            # Complex Cryptopuzzle:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()

            # In order to crack, the first four digit must be zeroes!
            if hash_operation[:4] == "0000":
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    # Hash function to return a cryptographic hash of a previous block - Previous hash
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys= True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    # Validating the chain - Checking whether the previous hash of each block = hash of the actual previous block and the proof of each block is valid
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block["previous_hash"] != self.hash(previous_block):
                return False

            previous_proof = previous_block["proof"]
            proof = block["proof"]
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != "0000":
                return False
            previous_block = block 
            block_index += 1
        return True

    # Anatomy of transaction:
    def add_transactions(self, sender, receiver, amount):
        self.transactions.append({
            "sender": sender, 
            "receiver": receiver, 
            "amount": amount
        })
        
        # After adding this txn's in last index in the blockchain, we must move on to the next index for the new txn's to be added.
        previous_block = self.get_previous_block()
        return previous_block["index"] + 1

    # Adding nodes with diff address(url), that contain all the blocks to the main network
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    # Replace the longest chain, when there is conflict between nodes on mining a block
    def replace_chain(self):
        network = self.nodes 
        longest_chain = None 
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f"http://{node}/get_chain")
            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["chain"]
                if length > max_length and self.is_chain_valid(chain): 
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
# --------------------------------------------------

# Part 2 - Mining our blockchain =>
# 1) Creating a Web App => 
app = Flask(__name__)

# creating an address for the node on port 5000 - coz to provide rewards to miner from node.
node_address = str(uuid4()).replace("-", "")

# 2) Creating a blockchain
blockchain = Blockchain()

# 3) Mining a new block - to make a request, use route decorator
#   - In order to mine a block, we need to do proof of work and we also need the proof of the previous block to do hash operations

@app.route("/mine_block", methods=["GET"])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block["proof"]
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transactions(sender= node_address, receiver= "Maajee", amount= 1)
    block = blockchain.create_block(proof, previous_hash)

    # To print data, which is added in the block in postman!
    # proof(Nounce) = soln to the cryptoPuzzle, that leads "0000" zeroes 
    response = {
        "message": "Congratulations, you have just mined a block! Reward: 3.15 BTC",
        "index": block["index"], 
        "timestamp": block["timestamp"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
        "transactions": block["transactions"]
    }
    return jsonify(response), 200

# 4) Getting the full blockchain as response in postman!
@app.route("/get_chain", methods=["GET"])
def get_chain():
    response = {
        "chain": blockchain.chain,
        "length": len(blockchain.chain)
    }
    return jsonify(response), 200

# 5) Checking, if the blockchain in valid
@app.route("/is_valid", methods=["GET"])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid: 
        response = {
            "message" : "All Good, Blockchain is valid."
        }
    else: 
        response = {
            "message" : "Something went wrong! Blockchain is Invalid."
        }
    return jsonify(response), 200

# 6) Posting the transactions on postman to add it on blockchain
@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    json = request.get_json() #Same as req.body
    transaction_keys = ["sender", "receiver", "amount"]
    if not all (key in json for key in transaction_keys):
        return "Some elements of the transaction are missing", 400
    index = blockchain.add_transactions(json["sender"], json["receiver"], json["amount"])
    response = {
        "message" : f"This transaction will be added to block {index}"
    }
    return jsonify(response), 201
# --------------------------------------------------

# Part 3 - Decentralizing our blockchain across the network & storing the transaction data...
# Transaction data's were added as soon as only when the blocks were mined by the miners.

# connecting new node
@app.route("/connect_node", methods=["POST"])
def connect_node():
    json = request.get_json()
    
    # To get all the nodes, which have been posted - to join nodes network
    nodes = json.get["nodes"]
    if nodes is None:
        return "No Node Address Found!", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {
        "message": "All Nodes are now connected, The INDcoin blockchain now contains the following nodes: ", 
        "total_nodes": list(blockchain.nodes)
    }
    return jsonify(response), 201

# Replacing the chain by the longest chain found, if needed..
@app.route("/replace_chain", methods=["GET"])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced: 
        response = {
            "message" : "The nodes had different chains so the chains was replaced by the longest chain.", 
            "new_chain": blockchain.chain
        }
    else: 
        response = {
            "message" : "All good, the chain is the largest one.", 
            "Actual_chain": blockchain.chain
        }
    return jsonify(response), 200

# Running the app
app.run(host = "0.0.0.0", port = 5000)
 

# Instruction in postman =>
# get_chain
# connect_node
# mine_block & get_chain - one node to check consensus
# replace_chain - to replace the longest chain in other two node
# add_transaction - to add a transaction. but it is not yet added to the block
# mine_block - In order to add the transaction to the newly mined block.