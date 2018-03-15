#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2016 VMware, Inc.  All rights reserved.
2016-04-06 - Jase McCarty

To provide an exmple of VC side VSAN API access, it shows how to get VSAN cluster capacity
status by invoking the QuerySpaceUsage API of the
VsanSpaceUsage MO.

Requires Humanize - https://pypi.python.org/pypi/humanize

"""

__author__ = 'VMware, Inc'

from pyVim.connect import SmartConnect, Disconnect
import sys
import ssl
import urllib
import atexit
import argparse
import getpass
#import Humanize for readable data
import humanize 
#import the VSAN API python bindings
import vsanmgmtObjects
import vsanapiutils



def GetArgs():
   """
   Supports the command-line arguments listed below.
   """
   parser = argparse.ArgumentParser(
       description='Process args for VSAN SDK sample application')
   parser.add_argument('-s', '--host', required=True, action='store',
                       help='Remote host to connect to')
   parser.add_argument('-o', '--port', type=int, default=443, action='store',
                       help='Port to connect on')
   parser.add_argument('-u', '--user', required=True, action='store',
                       help='User name to use when connecting to host')
   parser.add_argument('-p', '--password', required=False, action='store',
                       help='Password to use when connecting to host')
   parser.add_argument('--cluster', dest='clusterName', metavar="CLUSTER",
                      default='VSAN-Cluster')
   args = parser.parse_args()
   return args

def getClusterInstance(clusterName, serviceInstance):
   content = serviceInstance.RetrieveContent()
   searchIndex = content.searchIndex
   datacenters = content.rootFolder.childEntity
   for datacenter in datacenters:
      cluster = searchIndex.FindChild(datacenter.hostFolder, clusterName)
      if cluster is not None:
         return cluster
   return None

#Start program
def main():
   args = GetArgs()
   if args.password:
      password = args.password
   else:
      password = getpass.getpass(prompt='Enter password for host %s and '
                                        'user %s: ' % (args.host,args.user))

		
   #For python 2.7.9 and later, the default SSL conext has more strict
   #connection handshaking rule. We may need turn of the hostname checking
   #and client side cert verification
   context = None
   if sys.version_info[:3] > (2,7,8):
      context = ssl.create_default_context()
      context.check_hostname = False
      context.verify_mode = ssl.CERT_NONE

   si = SmartConnect(host=args.host,
                     user=args.user,
                     pwd=password,
                     port=int(args.port),
                     sslContext=context)

   atexit.register(Disconnect, si)

   #for detecting whether the host is VC or ESXi
   aboutInfo = si.content.about

   if aboutInfo.apiType == 'VirtualCenter':
      majorApiVersion = aboutInfo.apiVersion.split('.')[0]
      if int(majorApiVersion) < 6:
         print('The Virtual Center with version %s (lower than 6.0) is not supported.'
               % aboutInfo.apiVersion)
         return -1

      #Here is an example of how to access VC side VSAN API
      vcMos = vsanapiutils.GetVsanVcMos(si._stub, context=context)
      # Get vsan space report system
      vhs = vcMos['vsan-cluster-space-report-system']

      cluster = getClusterInstance(args.clusterName, si)

      if cluster is None:
         print("Cluster %s is not found for %s" % (args.clusterName, args.host))
         return -1
      
      CapacitySummary = vhs.QuerySpaceUsage(cluster=cluster)
      clusterTotalCapacity = CapacitySummary.totalCapacityB
      clusterFreeCapacity = CapacitySummary.freeCapacityB

      print("Cluster %s" % (args.clusterName))
      print("  Total Capacity: %s" % (humanize.naturalsize(clusterTotalCapacity, gnu=True)))
      print("  Free Capacity: %s" % (humanize.naturalsize(clusterFreeCapacity, gnu=True)))
      
# Start program
if __name__ == "__main__":
   main()
