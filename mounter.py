#!/usr/bin/python
#
# David Bezemer <david.bezemer@kaltura.com>
#
import sys, syslog, ConfigParser, time, os
import commands

# Read in configuration file
cfg                = ConfigParser.RawConfigParser()
cfg.read('/etc/mounter.d/mounter.conf')
syslog.openlog('mounter', 1)

# Load variables from config
check_filename     = cfg.get('global', 'check_filename').strip()
tmp_dir            = cfg.get('global', 'tmp_dir').strip()

# Perform FS checks, write to file if rw, read from file if ro
def check_fs (device, mount_opts = '', uid = 0) :
    mount_cmd      = 'mount -v -o %s %s %s' %(mount_opts, device, tmp_dir)
    unmount_cmd    = 'umount -v %s' %(tmp_dir)
    syslog.syslog('Executing : %s' %unmount_cmd)
    unmount_out = commands.getstatusoutput(unmount_cmd)
    syslog.syslog(unmount_out[1])
    if not unmount_out[0] in (0, 256) :
        syslog.syslog('umount failed with %s' %unmount_out[0])
    syslog.syslog('Executing : %s' %mount_cmd)
    mount_out = commands.getstatusoutput(mount_cmd)
    syslog.syslog(mount_out[1])
    if mount_out[0] <> 0 :
        syslog.syslog('mount failed with %s' %mount_out[0])
        return 'mounterror'
    os.seteuid(uid)
    syslog.syslog('UID: %d, EUID: %d' %(os.getuid(), os.geteuid()))
    if "rw" in mount_opts :
        try : 
            check_file = file(tmp_dir + '/' + check_filename, 'w')
        except : 
            syslog.syslog('Write test failed with %s' %sys.exc_info()[1])
    if "ro" in mount_opts :
        try : 
            check_file = file(tmp_dir + '/' + check_filename, 'r')
        except : 
            syslog.syslog('Read test failed with %s' %sys.exc_info()[1])
        return 'accesserror'
    check_file.close()
    syslog.syslog('Returning successful for : %s' %device)
    syslog.syslog('Executing : %s' %unmount_cmd)
    unmount_out = commands.getstatusoutput(unmount_cmd)
    syslog.syslog(unmount_out[1])
    return 'successful'


for section in cfg.sections() :
    if cfg.has_option(section, 'path') :
        path          = cfg.get(section, 'path')
        uid           = int(cfg.get(section, 'uid')) 

        filesystems = cfg.get(section, 'filesystems').split(',')
        for fs in filesystems :
            device      = cfg.get(fs.strip(), 'device') 
            mount_opts  = cfg.get(fs.strip(), 'mount_opts')
            fstype      = cfg.get(fs.strip(), 'fstype') 

            syslog.syslog('Trying %s (%s) -> %s' %(device, mount_opts, path))
            fs_status = check_fs(device, mount_opts, uid) 
            # if checks succeeded mount according to FS type
            if fs_status == 'successful' :
                if fstype in ('ext3', 'ext4') :
                    print '-fstype=%s,%s \t :%s' %(fstype, mount_opts, device)
                elif fstype in ('nfs') :
                    print '-fstype=%s,%s \t %s' %(fstype, mount_opts, device)
                break;
            else :
                continue;

syslog.closelog()

