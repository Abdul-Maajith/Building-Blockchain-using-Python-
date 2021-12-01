# Importing the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify

# Building a blockchain
class Blockchain:
    def __init__(self):
        self.chain = [] #Initializing chain of block 
        self.create_block(proof = 1, previous_hash = '0') # Genesis block 

    # Creating (or) adding a block, after mining..
    def create_block(self, proof, previous_hash):
        block = { 
            "index": len(self.chain) + 1, 
            "timestamp":str(datetime.datetime.now()),
            "proof": proof, 
            "previous_hash": previous_hash
        }
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
 
# Mining our blockchain =>
# 1) Creating a Web App => 
app = Flask(__name__)

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
    block = blockchain.create_block(proof, previous_hash)

    # To print data, which is added in the block in postman!
    # proof(Nounce) = soln to the cryptoPuzzle, that leads "0000" zeroes 
    response = {
        "message": "Congratulations, you have just mined a block! Reward: 3.15 BTC",
        "index": block["index"], 
        "timestamp": block["timestamp"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
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

# 6) Running the app
app.run(host = "0.0.0.0", port = 5000)
 