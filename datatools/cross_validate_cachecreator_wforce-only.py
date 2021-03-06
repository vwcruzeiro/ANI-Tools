import numpy as np
import pyanitools as pyt
from pyNeuroChem import cachegenerator as cg
import sys
import os

import hdnntools as hdn

import matplotlib.pyplot as plt
import matplotlib as mpl


def interval(v,S):
    ps = 0.0
    ds = 1.0 / float(S)
    for s in range(S):
        if v > ps and v <= ps+ds:
            return s
        ps = ps + ds

#wkdir = '/home/jsmith48/scratch/ccsd_extrapolation/learning_cases/dft_retrain/'
#saef   = wkdir + "sae_linfit.dat"
#data_root = '/home/jsmith48/scratch/ccsd_extrapolation/h5files_holdout_split/trainset/prepped/'

#wkdir = '/home/jsmith48/scratch/ANI-2x_retrain/model1/'
#saef   = wkdir + "sae_linfit.dat"
#data_root = '/home/jsmith48/scratch/auto_al/h5files/'

wkdir = '/home/jsmith48/scratch/ccsd_extrapolation/learning_cases/delta_DZ_retrain/delta_dft_1/'
saef   = wkdir + "sae_linfit.dat"
data_root = '/home/jsmith48/scratch/ccsd_extrapolation/h5files_holdout_split/trainset/delta/'

h5files = [data_root+f for f in os.listdir(data_root) if '.h5' in f]

store_dir = wkdir + "cache-data-"

N = 5

for i in range(N):
    if not os.path.exists(store_dir + str(i)):
        os.mkdir(store_dir + str(i))

    if os.path.exists(store_dir + str(i) + '/../testset/testset'+str(i)+'.h5'):
        os.remove(store_dir + str(i) + '/../testset/testset'+str(i)+'.h5')

    if not os.path.exists(store_dir + str(i) + '/../testset'):
        os.mkdir(store_dir + str(i) + '/../testset')

cachet = [cg('_train', saef, store_dir + str(r) + '/',False) for r in range(N)]
cachev = [cg('_valid', saef, store_dir + str(r) + '/',False) for r in range(N)]
testh5 = [pyt.datapacker(store_dir + str(r) + '/../testset/testset'+str(r)+'.h5') for r in range(N)]

Nd = np.zeros(N,dtype=np.int32)
Nbf = 0
for f,fn in enumerate(h5files):
    print('Processing file('+ str(f+1) +' of '+ str(len(h5files)) +'):', fn)
    adl = pyt.anidataloader(fn)

    To = adl.size()
    Ndc = 0
    Fmt = []
    Emt = []
    for c, data in enumerate(adl):
        #if c == 2 or c == 2 or c == 2:
        # Get test store name
        #Pn = fn.split('/')[-1].split('.')[0] + data['path']
        Pn = data['path']+'_'+str(f).zfill(6)+'_'+str(c).zfill(6)
        #print(Pn)

        # Progress indicator
        sys.stdout.write("\r%d%% %s" % (int(100*c/float(To)), Pn))
        sys.stdout.flush()

        #print(data.keys())

        # Extract the data
        X = data['coordinates']
        #E = data['extrapE']
        E = data['energies']
        #F = data['mp2_tz_grad']
        #F = data['forces']
        F = 0.0*X	

        S = data['species']

        #X = X.reshape(E.size,-1,3)
        #if len(X.shape) != 3:
        #    print('Error! X shape incorrect!',X.shape)
        #    print(S)
        #    exit(1)

        #print(X.shape)
        #Fmt.append(np.max(np.linalg.norm(F,axis=2),axis=1))
        Emt.append(E)
        #Mv = np.max(np.linalg.norm(F,axis=2),axis=1)
        #print(Mv.shape,X.shape)
        #index = np.where(Mv > 1.00)[0]
        #indexk = np.where(Mv <= 1.00)[0]
        #if index.size > 0:
            #print(Mv[index])
            #hdn.writexyzfile(bddir+'mols_'+str(c).zfill(3)+'_'+str(f).zfill(3)+'.xyz',X[index],S)
        #Nbf += index.size
        Nbf = 0
        #if data['path'] == '/dimer7/grp_0':
        #    print(data['path'])
        #    print(E)
        #    print(F)

        # CLear forces
        #X = X[indexk]
        #F = F[indexk]
        #E = E[indexk]

        #exit(0)
        #print(" MAX FORCE:", F.max(), S)
        '''
        print('meanforce:',F.flatten().mean())
        print("FORCE:",F)
        print(np.max(F.reshape(E.size,F.shape[1]*F.shape[2]),axis=1))
        print("MAX FORCE:", F.max(),S)

        if F.max() > 0.0:
            print(np.mean(F.reshape(E.size,F.shape[1]*F.shape[2]),axis=1).shape, E.size)
            plt.hist(np.max(np.abs(F).reshape(E.size,F.shape[1]*F.shape[2]),axis=1),bins=100)
            plt.show()
            plt.scatter(np.max(np.abs(F).reshape(E.size,F.shape[1]*F.shape[2]),axis=1), E)
            plt.show()
        '''
        Ru = np.random.uniform(0.0, 1.0, E.shape[0])
        nidx = np.where(Ru < 1.0)
        X = X[nidx]
        F = F[nidx]
        E = E[nidx]

        Esae = hdn.compute_sae(saef,S)
        Hidx = np.where(E-Esae < 4.5)

        X = X[Hidx]
        F = F[Hidx]
        E = E[Hidx]
 
        Hidx = np.where(E-Esae > -20.0)

        X = X[Hidx]
        F = F[Hidx]
        E = E[Hidx]

        Ndc += E.size
        #for i in range(E.size):
        #    X[i] = X[0]
        #    F[i] = F[0]
        #    E[i] = E[0]

        if (set(S).issubset(['C', 'N', 'O', 'H', 'S', 'F', 'Cl'])):

            # Random mask
            R = np.random.uniform(0.0, 1.0, E.shape[0])
            idx = np.array([interval(r,N) for r in R])

            # Build random split lists
            split = []
            for j in range(N):
                split.append([i for i, s in enumerate(idx) if s == j])
                nd = len([i for i, s in enumerate(idx) if s == j])
                Nd[j] = Nd[j] + nd

            # Store data
            for i,t,v,te in zip(range(N), cachet, cachev, testh5):
                ## Store training data
                X_t = np.array(np.concatenate([X[s] for j, s in enumerate(split) if j != i]), order='C', dtype=np.float32)
                F_t = np.array(np.concatenate([F[s] for j, s in enumerate(split) if j != i]), order='C', dtype=np.float32)
                E_t = np.array(np.concatenate([E[s] for j, s in enumerate(split) if j != i]), order='C', dtype=np.float64)

                if E_t.shape[0] != 0:
                    #print('\n',E_t.shape)
                    t.insertdata(X_t, F_t, E_t, list(S))

                ## Split test/valid data and store\
                R2 = np.random.uniform(0.0, 1.0, np.array(split[i]).shape[0])
                va_idx = np.array(split[i])[np.where(R2 >= 0.5)] 
                te_idx = np.array(split[i])[np.where(R2  < 0.5)] 

                #print(va_idx,te_idx)

                ## Store Validation
                if va_idx.size > 0:
                    X_v = np.array(X[va_idx], order='C', dtype=np.float32)
                    F_v = np.array(F[va_idx], order='C', dtype=np.float32)
                    E_v = np.array(E[va_idx], order='C', dtype=np.float64)
                    if E_v.shape[0] != 0:
                        #print(E_v.shape)
                        v.insertdata(X_v, F_v, E_v, list(S))

                ## Store testset
                if te_idx.size > 0:
                    X_te = np.array(X[te_idx], order='C', dtype=np.float32)
                    F_te = np.array(F[te_idx], order='C', dtype=np.float32)
                    E_te = np.array(E[te_idx], order='C', dtype=np.float64)
                    if E_te.shape[0] != 0:
                        te.store_data(Pn, coordinates=X_te, forces=F_te, energies=E_te, species=list(S))

    #plt.hist(np.concatenate(Fmt), bins=150)
    #plt.show()

    #plt.hist(Emt, bins=150)
    #plt.show()

    #sys.stdout.write("\r%d%%" % int(100))
    print(" Data Kept: ", Ndc, 'High Force: ', Nbf)
    sys.stdout.flush()
    print("")

# Print some stats
print('Data count:',Nd)
print('Data split:',100.0*Nd/np.sum(Nd),'%')

# Save train and valid meta file and cleanup testh5
for t,v,th in zip(cachet, cachev, testh5):
    t.makemetadata()
    v.makemetadata()
    th.cleanup()
