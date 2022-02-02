###############################
# Import Python modules
###############################
import sys,os
# NOTE: Uncomment these lines if you are putting the modules in the local directory
#sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'pyserial.serial'))
#sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'crcmod'))
import serial
import crcmod.predefined
import time


####################
# DNP Command Setup
# NOTE: Use strings in hex where you can to be consistent with 
#       bytes.fromhex(str) for functions.
####################
src_address = 1023
dst_address = 1
SRC_ADDR    = src_address.to_bytes(2,'little')
DST_ADDR    = dst_address.to_bytes(2,'little')
DNP_HEADER  = '0564'

####################
# Helper Functions DNP Commands
####################
# Generate DNP3 CRC
def gen_crc(data):
    # Import DNP3 CRC
    # NOTE: Normal use of CRCMOD and CRCCHECK did not generate the CRC correctly
    #       This is the ONLY method that generated the CRC correctly
    #       Online CRC Check: https://www.lammertbies.nl/comm/info/crc-calculation
    crcdnp = crcmod.predefined.mkCrcFun('crc-16-dnp')
    return crcdnp(data).to_bytes(2,'little')

# Build Header Packet
def build_dnp_header(head,src,dst,cntl):
    # Length will have to be updated if additional data is placed in packet
    plen    = 5
    packet = bytes.fromhex(head) + plen.to_bytes(1,'little') + bytes.fromhex(cntl) + dst.to_bytes(2,'little') + src.to_bytes(2,'little') 
    crc    = gen_crc(packet)
    return packet + crc

# Build Object Packet
def build_dnp_object(data):
    # Length will have to be updated if additional data is placed in packet
    plen    = 5
    packet = bytes.fromhex(data)
    crc    = gen_crc(packet)
    return packet + crc

####################
# Full DNP Commands
####################
# Data Link Layer Control Codes
## Producer
DLLCC_P_ACK                   = '80'
DLLCC_P_NACK                  = '81'
DLLCC_P_LINK_STATUS           = '8B'
DLLCC_P_NOT_SUPPORTED         = '8F'
DLLCC_P_RESET_LINK_STATES     = 'C0'
DLLCC_P_UNCONFIRMED_USER_DATA = 'C4'
DLLCC_P_REQUEST_LINK_STATUS   = 'C9'
DLLCC_P_TEST_LINK_STATES      = 'D2'
DLLCC_P_CONFIRMED_USER_DATA_D = 'D3'
DLLCC_P_CONFIRMED_USER_DATA_F = 'F3'
## Consumer
DLLCC_O_ACK                   = '00'
DLLCC_O_NACK                  = '01'
DLLCC_O_LINK_STATUS           = 'OF'
DLLCC_O_NOT_SUPPORTED         = '0F'
DLLCC_O_RESET_LINK_STATES     = '40'
DLLCC_O_UNCONFIRMED_USER_DATA = '44'
DLLCC_O_REQUEST_LINK_STATUS   = '49'
DLLCC_O_TEST_LINK_STATES      = '52'
DLLCC_O_CONFIRMED_USER_DATA_D = '53'
DLLCC_O_CONFIRMED_USER_DATA_F = '73'

# Function Codes
FC_CONFIRM                = '00'
FC_READ                   = '01'
FC_WRITE                  = '02'
FC_SELECT                 = '03'
FC_OPERATOR               = '04'
FC_DIR_OPERATE            = '05'
FC_DIR_OPERATE_NO_RESP    = '06'
FC_FREEZE                 = '07'
FC_FREEZE_NO_RESP         = '08'
FC_FREEZE_CLEAR           = '09'
FC_FREEZE_CLEAR_NO_RESP   = '0A'
FC_FREEZE_AT_TIME         = '0B'
FC_FREEZE_AT_TIME_NO_RESP = '0C'
FC_COLD_RESTART           = '0D'
FC_WARM_RESTART           = '0E'
FC_INIT_DATA              = '0F'
FC_INIT_APP               = '10'
FC_START_APP              = '11'
FC_STOP_APP               = '12'
FC_SAVE_CONFIG            = '13'
FC_ENABLE_UNSOL           = '14'
FC_DISABLE_UNSOL          = '15'
FC_ASSIGN_CLASS           = '16'
FC_DELAY_MEASURE          = '17'
FC_RECORD_TIME            = '18'
FC_OPEN_FILE              = '19'
FC_CLOSE_FILE             = '1A'
FC_DELETE_FILE            = '1B'
FC_FILE_INFO              = '1C'
FC_AUTH_FILE              = '1D'
FC_ABORT_FILE             = '1E'
FC_ACTIVATE_CONFIG        = '1F'
FC_AUTH_REQ               = '20'
FC_AUTH_REQ_NO_ACK        = '21'
FC_RESP                   = '81'
FC_UNSOL_RESP             = '82'
FC_AUTH_RESP              = '83'

TCAC_FIRST_FIN            = 'C0C0'


# Broadcast Commands
COLD_RESTART_BROADCAST = '056408C4FFFFFFFF4451C0C00D9C86'
LINK_STATUS_BROADCAST  = '056405C9FFFFFFFF46C9'

# Build commands
LINK_STATUS_DIRECT      = build_dnp_header(DNP_HEADER,src_address,dst_address,DLLCC_P_REQUEST_LINK_STATUS)
RESET_LINK_STATE_DIRECT = build_dnp_header(DNP_HEADER,src_address,dst_address,DLLCC_P_RESET_LINK_STATES)
TEST_LINK_STATE_DIRECT  = build_dnp_header(DNP_HEADER,src_address,dst_address,DLLCC_P_TEST_LINK_STATES)
UNCONFIRMED_USER_DATA   = build_dnp_header(DNP_HEADER,src_address,dst_address,DLLCC_P_UNCONFIRMED_USER_DATA)
COLD_RESTART_OBJ        = build_dnp_object(TCAC_FIRST_FIN + FC_COLD_RESTART)
WARM_RESTART_OBJ        = build_dnp_object(TCAC_FIRST_FIN + FC_WARM_RESTART)

# Wrapper for sending broadcast messages
# s = open serial port
# cmd = string of hex bytes
def send_broadcast(s, cmd):
    s.write(bytes.fromhex(cmd))
    time.sleep(1)
    r = s.read(size=200)
    if r: print(r)
    time.sleep(1)

# Wrapper for sending direct messages
# s = open serial port
# cmd = byte string built from build_dnp_header function
# cmd = byte string built from build_dnp_object
def send_direct(s, cmd, obj=b''):
    # If there are DNP3 objects, update the length byte
    # NOTE: DNP3 objects should be completely formed with CRC
    len_index = 2
    if obj:
        # using a bytearray might be more understandable
        # Compute new length byte and remove CRC from header
        cmd = cmd[:len_index] + (cmd[len_index] + (len(obj) - 2)).to_bytes(1,'little') + cmd[len_index + 1:-2]
        # Recompute CRC and update command
        crc    = gen_crc(cmd)
        cmd = cmd + crc
    s.write(cmd + obj)
    time.sleep(1)
    r = s.read(size=200)
    if r: print(r)
    time.sleep(1)

###############
# Setup Serial
###############
port     = '/dev/ttyUSB0'
baudrate = 19200
timeout  = 1
bytesize = 8
stopbits = serial.STOPBITS_ONE
serialPort = serial.Serial(port=port, baudrate=baudrate,
                                bytesize=bytesize, timeout=timeout, stopbits=stopbits)
response = b''

print('Starting DNP3 Stalker. Cntl-C to stop sending commands.\n')
while True:
    try:

        if len(sys.argv) < 2: 
            print('    Provide a command. Read the code.\n')
            break
        if sys.argv[1] == 'COLD_BROADCAST': send_broadcast(serialPort, COLD_RESTART_BROADCAST)
        if sys.argv[1] == 'LINK_BROADCAST': send_broadcast(serialPort, LINK_STATUS_BROADCAST)
        if sys.argv[1] == 'LINK_STAT': send_direct(serialPort, LINK_STATUS_DIRECT)
        if sys.argv[1] == 'COLD_RESTART': send_direct(serialPort, UNCONFIRMED_USER_DATA, obj=COLD_RESTART_OBJ)
        if sys.argv[1] == 'WARM_RESTART': send_direct(serialPort, UNCONFIRMED_USER_DATA, obj=WARM_RESTART_OBJ)
        time.sleep(1)


        # TODO: Remove old methods
        '''
        serialPort.write(bytes.fromhex(COLD_RESTART_BROADCAST))
        time.sleep(1)
        response = serialPort.read(size=200)
        if response: print(response)
        time.sleep(1)
        serialPort.write(build_dnp_data_header(DNP_HEADER,src_address,dst_address,'C9'))
        print("%s"%(build_dnp_data_header(DNP_HEADER,src_address,dst_address,'C9').hex()))
        time.sleep(1)
        response = serialPort.read(size=200)
        if response: print(response)
        time.sleep(1)
        '''
    except KeyboardInterrupt:
        break

serialPort.close()
