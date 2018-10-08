## CLI tool for export vm images to ovirt external provider (cinder)


### Help

You can read help

	./upload_external_provider.py -h
    usage: upload_external_provider_test.py [-h] --image IMAGE_PATH
                                        [--description DESCRIPTION]
                                        [--name DISKNAME]
                                        [--openstackvolumetype OPENSTACKVOLUMETYPE]
                                        [--storagedomain STORAGEDOMAIN]
                                        [--conf CEPHCONF] [--pool RBDPOOL]
                                        [--id CEPHUSER] [--ca CA_FILE] --host
                                        OVIRTHOST --password OVIRTPASS

    Convert and transfer images supported by qemu-img to ovirt -> ceph.
    
    optional arguments:
    -h, --help            show this help message and exit
    --image IMAGE_PATH, -i IMAGE_PATH
                            Short or full path to importing image
    --description DESCRIPTION, -d DESCRIPTION
                            Disk description
    --name DISKNAME, -n DISKNAME
                            Disk name
    --openstackvolumetype OPENSTACKVOLUMETYPE, -t OPENSTACKVOLUMETYPE
                            OpenStackVolumeType that provides cinder
    --storagedomain STORAGEDOMAIN, -s STORAGEDOMAIN
                            oVirt OpenStack Cinder provider
    --conf CEPHCONF, -c CEPHCONF
                            Path to ceph config
    --pool RBDPOOL        Rbd pool
    --id CEPHUSER         Ceph user id
    --ca CA_FILE          Ovirt ca.pem certificate
    --host OVIRTHOST      Ovirt Hoted Engine FQDN
    --password OVIRTPASS, -p OVIRTPASS
                            Ovirt Hosted Engine password

### Requirements

You need installed qemu-img, ceph(librbd), ovirt-engine-sdk-python (pip)

### Usage
    [root@importer VM]# ./upload_external_provider.py --image image.vhd --ca /opt/ca.pem --name vmdiskname --description="need to remove" --host ovirt.domain --password mypass
    Checking image...
    Connecting...
    Creating disk...
    Current progress:     (100.00/100%)
    Upload completed successfully


### Options
##### --image -i
source image, like vm.vhd
##### --description -d
disk description in ovirt
##### --name -n
disk alias in ovirt (default image name)
##### --openstackvolumetype -t
volume_backend_name in cinder.conf . You can find it in ovirt interface disks -> cinder (default cinder)
##### --storagedomain -s
ovirt storage external provider name (default ovirt-block-provider)
##### --conf -c
ceph config (default /etc/ceph/ceph.conf)
##### --pool
ceph pool for rbd configured in cinder (default rbd)
##### --id
ceph user (default admin)
##### --ca
CA from ovirt hosted engine. Stored in /etc/pki/ovirt-engine/ca.pem on ovirt host
##### --host
Ovirt hosted engine FQDN
##### --password
Ovirt hosted engine internal admin password

