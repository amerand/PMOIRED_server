# PMOIRED_server
Using [Docker](https://www.docker.com/) to run many instances of [PMOIRED](https://github.com/amerand/PMOIRED) with its Jupyter Notebooks [examples](https://github.com/amerand/PMOIRED_examples). 

## Building [Docker](https://www.docker.com/) images
The provided [docker file](Dockerfile) will generate a container to install [PMOIRED](https://github.com/amerand/PMOIRED) and run the [examples](https://github.com/amerand/PMOIRED_examples) in Jupyter Lab. To generate the container, simply run:
```
docker build -t pmoired:latest .
```
to run a container which will use only the first four CPUs and exposed on port 8890 (including to outside world):
```
docker run -p 8890:8888 --name="pmoired8890" --cpuset-cpus=0-3 -d pmoired
```
in a browser, simply access `http://machine:8890` where *machine* is the IP/name of the computer running docker. To stop the container:
```
docker stop pmoired8890
```

## Running many instances with provided Python script

The script [`pmoiredDockers.py`](pmoiredDockers.py) is a simple use Docker's SDK to start many instances of the container, on a range of ports and with the load spread on different CPUs. Install first the docker SDK:
```
pip3 install docker
```
Then use the provided functions to start and stop instances (you still have to first build the images: the python scripts assume there is a proper Docker image `pmoired`, as decribed in the first section):
```
>>> import pmoiredDockers
>>> pmoiredDockers.runContainers(4, 6, start_port=9000)
running /pmoired9000 0,1,2,3,4,5 -> http://labrique:9000 or http://127.0.1.1:9000
running /pmoired9001 3,4,5,6,7,8 -> http://labrique:9001 or http://127.0.1.1:9001
running /pmoired9002 6,7,8,9,10,11 -> http://labrique:9002 or http://127.0.1.1:9002
running /pmoired9003 9,10,11,0,1,2 -> http://labrique:9003 or http://127.0.1.1:9003
>>> pmoiredDockers.stopContainers([9001, 9002])
stopping /pmoired9002
stopping /pmoired9001
>>> pmoiredDockers.info()
/pmoired9000 running
/pmoired9001 exited
/pmoired9002 exited
/pmoired9003 running
>>> pmoiredDockers.stopContainers()
stopping /pmoired9003
stopping /pmoired9000
>>> pmoiredDockers.removeContainers()
backing up in pmoired9003_Mon_Apr__8_18:28:13_2024.tar, removing /pmoired9003
backing up in pmoired9002_Mon_Apr__8_18:28:13_2024.tar, removing /pmoired9002
backing up in pmoired9001_Mon_Apr__8_18:28:13_2024.tar, removing /pmoired9001
backing up in pmoired9000_Mon_Apr__8_18:28:13_2024.tar, removing /pmoired9000
```
After importing, the call to `runContainers` starts 4 instances with a maximum of 6 CPUs each on ports 9000..9003. The Jupyer-lab sessions are accessible at the listed (local) addresses. Note that the load is spread amongst all avalaible CPUs (here 12) with equal priorities. The calls to `stopContainers` first stops specific containers referenced by their ports. The call without arguments stops all remaining instances. After containers are stopped, calling `runContainers` will restart them (***without changing the ports or CPUs assignments***). The last call to  `removeContainers` removes the containers, making a backup of the whole directory *PMOIRED_examples/* in a tar file. As for stopping containers, you can pass a list of ports corresponding to the containers to be removed. You can remove containers without doing a backup by passing `backup=False`.

At any moment, you can backup/restore a running containers by doing:
```
>>> pmoiredDockers.backupToTar('pmoired10000')
backing up in pmoired10000_Mon_Apr__8_19:51:55_2024.tar
>>> pmoiredDockers.restoreFromTar('pmoired10000_Mon_Apr__8_19:51:50_2024.tar')
restoring /pmoired10000 OK
```

If you are lost, you can use `info()` to know which instances are running or were stopped. running `docker stats` in a terminal is a better way to monitor containers, as it show real-time CPU and memory usage.
## Limitations
