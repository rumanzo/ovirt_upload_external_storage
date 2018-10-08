#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author Alexey Kostin rumanzo@yandex.ru

"""

Requires the qemu-img package for checking file type and virtual size and ovirtsdk4 for create disk image on ovirt

Usage:

    upload_external_provider.py args
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import ovirtsdk4 as sdk
import ovirtsdk4.types as types

parser = argparse.ArgumentParser(description='Convert and transfer images supported by qemu-img to ovirt -> ceph.')
parser.add_argument('--image', '-i', dest='image_path', default=None, required=True,
                    help='Short or full path to importing image')
parser.add_argument('--description', '-d', dest='description', default=None,
                    help='Disk description')
parser.add_argument('--name', '-n', dest='diskname', default=None,
                    help='Disk name')
parser.add_argument('--openstackvolumetype', '-t', dest='openstackvolumetype', default="ceph",
                    help='OpenStackVolumeType that provides cinder')
parser.add_argument('--storagedomain', '-s', dest='storagedomain', default="ovirt-block-provider",
                    help='oVirt OpenStack Cinder provider')
parser.add_argument('--conf', '-c', dest='cephconf', default="/etc/ceph/ceph.conf",
                    help='Path to ceph config')
parser.add_argument('--pool', dest='rbdpool', default="rbd",
                    help='Rbd pool')
parser.add_argument('--id', dest='cephuser', default="admin",
                    help='Ceph user id')
parser.add_argument('--ca', dest='ca_file', default="ca.pem",
                    help='Ovirt ca.pem certificate')
parser.add_argument('--host', dest='ovirthost', default=None, required=True,
                    help='Ovirt Hoted Engine FQDN')
parser.add_argument('--password', '-p', dest='ovirtpass', default=None, required=True,
                    help='Ovirt Hosted Engine password')

args = parser.parse_args()
if not args.diskname:
    args.diskname = str(Path(os.path.basename(args.image_path)).with_suffix(''))

logging.basicConfig(level=logging.DEBUG, filename='upload_external_storage.log')

direct_upload = False

image_path = args.image_path
image_size = os.path.getsize(image_path)

# Get image info using qemu-img

print("Checking image...")

out = subprocess.check_output(
    ["qemu-img", "info", "--output", "json", image_path]).decode('utf-8')
image_info = json.loads(out)

# Minimcal size rbd image 1Gb. Bytes
if image_info["virtual-size"] < 2 ** 30:
    image_info["virtual-size"] = 2 ** 30

# This code will connect to the server and create a new
# disk on external provider, e.g. cinder, one that isn't attached to any virtual machine.
# Then using transfer service it will transfer disk data from local
# qcow2 disk to the newly created disk in server.

# Create the connection to the server:
print("Connecting...")

connection = sdk.Connection(
    url='https://{}/ovirt-engine/api'.format(args.ovirthost),
    username='admin@internal',
    password=args.ovirtpass,
    ca_file=args.ca_file,
    debug=True,
    log=logging.getLogger(),
)

# Get the reference to the root service:
system_service = connection.system_service()

# Add the disk. Note the following:
#
# 1. The size of the disk is specified in bytes, so to create a disk
#    of 10 GiB the value should be 10 * 2^30.
#
# 2. The disk size is indicated using the 'provisioned_size' attribute,
#    but due to current limitations in the engine, the 'initial_size'
#    attribute also needs to be explicitly provided for _copy on write_
#    disks created on block storage domains, so that all the required
#    space is allocated upfront, otherwise the upload will eventually
#    fail.
#
# 3. The disk initial size must be bigger or the same as the size of the data
#    you will upload.

print("Creating disk...")
disk_format = types.DiskFormat.RAW
disks_service = connection.system_service().disks_service()

disk = disks_service.add(
    types.Disk(
        name=args.diskname,
        openstack_volume_type=types.OpenStackVolumeType(name=args.openstackvolumetype),
        description=args.description,
        format=disk_format,
        provisioned_size=image_info["virtual-size"],
        storage_domains=[
            types.StorageDomain(
                name=args.storagedomain
            )
        ]
    )
)
# Wait till the disk is up, as the transfer can't start if the
# disk is locked:
disk_service = disks_service.disk_service(disk.id)
while True:
    time.sleep(5)
    disk = disk_service.get()
    if disk.status == types.DiskStatus.OK:
        break

try:
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    # Upload img to created rbd
    print("Uploading image...")
    process = subprocess.Popen(["qemu-img", "convert", "-p", "-m", "16", "-W", "-f", image_info["format"], "-O", "raw", "-n", image_path,
                                "rbd:{}/{}:id={}:conf={}".format(args.rbdpool, "volume-" + disk.id, args.cephuser,
                                                                 args.cephconf)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = b''
    while True:
        if process.poll() is None:
            char = process.stdout.read(1)
            if char != b'\r':
                output += char
            else:
                sys.stdout.write(CURSOR_UP_ONE)
                sys.stdout.write(ERASE_LINE)
                print('Current progress: {}'.format(output.decode('UTF-8')))
                output = b''
        else:
            break
    out, err = process.communicate()
    if err:
        connection.close()
        raise RuntimeError(err)
    print("Upload completed successfully")
except Exception as e:
    print(e)
finally:
    process.terminate()
    connection.close()
