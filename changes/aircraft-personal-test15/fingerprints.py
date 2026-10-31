"""IEEE negative zero has identical model meaning but a different textual spelling."""
import hashlib,re

def zero_normalized(data):
 return re.sub(rb'(?<!\S)-0(?:\.0+)?(?=\s|$)',lambda m:m.group()[1:],data)

def zero_hash(data):return hashlib.sha256(zero_normalized(data)).hexdigest()
