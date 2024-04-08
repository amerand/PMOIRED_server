import docker
import multiprocessing, socket, time, os

client = docker.from_env()

# -- organise running containers in a dictionnary
listPmoired = lambda : {c.attrs['Name']:c for c in client.containers.list(all=True)}

def info():
    C = listPmoired()
    C = {k:C[k] for k in C if k.startswith('/pmoired')}
    if len(C)==0:
        print('no containers running or stopped')
    for k in sorted(C):
        print(k, C[k].status, )

def runContainers(ncont=1, ncpus_per_cont=None, start_port=10000):
    """
    run `ncont` instances of PMOIRED each with `ncpus_per_cont` (by default all instances have access 
    to all CPUs!). 
    
    The first instance starts on port `start_port`=10000, and each instance increments the port by one
    """
    # -- total CPUs on the machine
    ncpus = multiprocessing.cpu_count()
    if ncpus_per_cont==None:
        ncpus_per_cont = ncpus
    shift = min(max(ncpus//(ncont), 1), ncpus_per_cont)

    C = listPmoired()
    for i in range(ncont):
        cpuset_cpus = ','.join([str((shift*i+j)%ncpus) for j in range(ncpus_per_cont)])
        name = 'pmoired'+str(start_port+i)
        if '/'+name in C:
            if C['/'+name].status!='running':
                C['/'+name].start()
                print('restarting', '/'+name)
            else:
                print('status of', '/'+name, ':', C['/'+name].status)
        else:
            print('running', '/'+name, cpuset_cpus, '->', 
                  'http://'+socket.getfqdn()+':'+str(start_port+i), 
                  'or', 
                  'http://'+socket.gethostbyname(socket.getfqdn())+':'+str(start_port+i))
            client.containers.run('pmoired', name=name, cpuset_cpus=cpuset_cpus,
                                  ports={'8888/tcp':start_port+i}, detach=True)

def stopContainers(R=None):
    """
    will stop all running instance of pmoired Docker containers if R==None. Alternatively, one
    can give a list if port integers for the port to be stopped. E.g. R=[8889, 8891] will stop 
    'pmoired8889' and 'pmoired8891', if they exist.
    """
    C = listPmoired()
    if R is None:
        # -- prune all
        K = filter(lambda x: x.startswith('/pmoired'), C.keys())
    else:
        K = filter(lambda x: x.startswith('/pmoired') and int(x.split('/pmoired')[1]) in R, C.keys())
    for k in sorted(K):
        if C[k].status!='runing':
            print('stopping', k)
            C[k].stop()
    return

def backupToTar(cont=None):
    C = listPmoired()
    if type(cont) is int:
        cont = '/pmoired'+str(cont)
    if not cont.startswith('/'):
        cont = '/'+cont
    if not cont in C:
        print('failed: unknown container "'+cont+'"')
        info()
        return False
    tarname = '_'.join([cont[1:], time.asctime().replace(' ', '_')])+'.tar'
    print('backing up in', tarname)
    with open(tarname, 'wb') as f:
        bits, stat = C[cont].get_archive('/PMOIRED_examples/')
        for chunk in bits:
            f.write(chunk)
    return True
    
def restoreFromTar(filename, cont=None, backup=False):
    """
    filename: a tar file copy of "PMOIRED_examples/"
    container should be a name of a running container, e.g. '
    """
    if not os.path.exists(filename):
        print('failed,', filename, 'does not exist')
        return False
    C = listPmoired()
    if cont is None:
        cont = '/'+os.path.basename(filename).split('_')[0]
    if not cont in C:
        print('failed: unknown container "'+cont+'"')
        info()
        return False
    if backup:
        backupToTar(cont)
    print('restoring', cont, end=' ')
    with open(filename, 'rb') as f:
        test = C[cont].put_archive('/', f)
    if test:
        print('OK')
    else:
        print('failed')
    return True
            
def removeContainers(R=None, backup=True):
    """
    will remove all stopped/exited instance of pmoired Docker containers if R==None. Alternatively, one
    can give a list if port integers for the port to be stopped. E.g. R=[8889, 8891] will remove 
    'pmoired8889' and 'pmoired8891', if they exist and have been stopped.

    backup=True will copy the content of 'PMOIRED_examples/' in a tar file.
    """
    C = listPmoired()
    if R is None:
        # -- prune all
        K = filter(lambda x: x.startswith('/pmoired'), C.keys())
    else:
        K = filter(lambda x: x.startswith('/pmoired') and int(x.split('/pmoired')[1]) in R, C.keys())
    for k in sorted(K):
        if C[k].status=='exited':
            if backup:
                backupToTar(k)
            print('removing', k)
            C[k].remove()
        else:
            print('can only remove a stopped container!', k, C[k].status)
    return