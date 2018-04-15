Cloud boot agent is the service run in cloud boot environment.
cloudboot init script:
 check environment. (if the cloudboot is boot from the disk)
1. try to load pickle information from default bootable disk: /dev/sda1, /dev/hda1
  1.1 [success]:
	if the configure section [rpcbox,msgbox,updatebox] is set
