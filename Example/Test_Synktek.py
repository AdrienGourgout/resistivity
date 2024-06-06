from resistivity.Driver.MCLpy.MCL import MCL
import time


print("Creating MCL object")
mcl = MCL()
print("Finding systems")
systems = mcl.find_systems()
print(systems)
if len(systems) > 0:
    mcl_ip = str(next(iter(systems)))
else:
    mcl_ip = '172.22.11.2'
#    mcl_ip = '192.168.1.110'
mcl_ip = input("Enter MCL IP [%s]: " % mcl_ip) or mcl_ip
print("Connect to instrument")
mcl.connect(mcl_ip)

print(mcl.data.L1.dc)

# print('out_freq=', mcl.data.L1.val[1])
# print("")
# print('out_freq=', mcl.data.L1.val[1][0][1])
# print("")
# print('out_amp=', mcl.data.L1.val[1][0][2])
# print('Y=', mcl.data.L1.y)
# print('R=', mcl.data.L1.r)
# print('theta=', mcl.data.L1.theta)
# print('DC=', mcl.data.L1.dc)



print("Disconnecting...")
mcl.disconnect()