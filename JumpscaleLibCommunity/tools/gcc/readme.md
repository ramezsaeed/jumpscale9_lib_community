# GCC = Global Control Center

## intro

is 3 physical nodes running 1 docker each all connected over Weave

in each docker

- caddy: port 443 proxy for etcd
- etcd (behind caddy which is https frontend)
- skydns
- aydostor
- agentcontroller/syncthing

the 3 dockers talk to each other using weave

## implementation remarks

- see this extension (which is using executors.prefab... methods)
- is docker with volume on btrfs (make sure is right btrfs volume)
- install agentcontroller &  syncthing
- weave to get agentcontroller/syncthing to work together in cluster of 3
- so 3 agents, 3 agentcontrollers all talking to each other

how to install (prefab based)
- use prefab to install docker (docker methods are not finished yet): ubuntu 15.10 tmux image
- the prefab has been updated yesterday to support tmux for startup as well (is under systemd, keep that name)
- implement weave compatibility (is new)
- on physical node ufw blocks all, only dns, 443 & weave ports are open
- install python3 & ... through prefab.apps for now
- install agentcontroller,golang, skydns, etcd, ... all through prefab.apps for now
- syncthing is used to sync the aydostor folders (for each namespace create a new replica set in synchting, create code for this in aydostor)
- no ays because this is the bootstrap before we will do anything further, we need to be able to rely on this no matter what happens with our code, ... so we need to stay close to the code
- all managed through ssh keys

ITS IMPORTANT WE CAN REPRODUCE ALL !!!
so nothing manual with customer docker images or custom manual installs !!!


