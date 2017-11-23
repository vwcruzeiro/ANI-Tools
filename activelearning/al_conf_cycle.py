import anialservertools as ast
import anialtools as alt
from time import sleep
import os

hostname = "comet.sdsc.xsede.org"
#hostname = "moria.chem.ufl.edu"
username = "jsmith48"

root_dir = '/home/jsmith48/scratch/auto_al/'

swkdir = '/home/jsmith48/scratch/auto_al_cycles/'# server working directory
datdir = 'ANI-AL-0606.0201.04'

h5stor = root_dir + 'h5files/'# h5store location

optlfile = root_dir + 'optimized_input_files.dat'

mae = 'module load gnu/4.9.2\n' +\
      'module load gaussian\n' +\
      'export PATH="/home/$USER/Gits/RCDBuilder/build/bin:$PATH"\n' +\
      'export LD_LIBRARY_PATH="/home/$USER/Gits/RCDBuilder/build/lib:$LD_LIBRARY_PATH"\n'

fpatoms = ['C', 'N', 'O', 'S', 'F', 'Cl']

#---- Training Parameters ----
GPU = [3,4,5,6,7] # GPU IDs

M   = 0.34 # Max error per atom in kcal/mol
Nnets = 5 # networks in ensemble
aevsize = 1008

wkdir = '/home/jsmith48/scratch/auto_al/modelCNOSFCl/ANI-AL-0606/ANI-AL-0606.0201/'
iptfile = '/home/jsmith48/scratch/auto_al/modelCNOSFCl/inputtrain.ipt'
saefile = '/home/jsmith48/scratch/auto_al/modelCNOSFCl/sae_wb97x-631gd.dat'
cstfile = '/home/jsmith48/scratch/auto_al/modelCNOSFCl/rHCNOSFCl-4.6A_16-3.1A_a4-8.params'
#-----------0---------

# Training varibles

#### Sampling parameters ####
nmsparams = {'T': 800.0,
             'Ngen': 80,
             'Nkep': 10,
             }

mdsparams = {'N': 4,
             'T': 600,
             'dt': 1.0,
             'Nc': 1000,
             'Ns': 2,
             }


### BEGIN CONFORMATIONAL REFINEMENT LOOP HERE ###
N = [0,1,2,3,4,5,6,7,8,9,10]

for i in N:
    netdir = wkdir+'ANI-AL-0606.0201.04'+str(i).zfill(2)+'/'
    if not os.path.exists(netdir):
        os.mkdir(netdir)

    nnfprefix   = netdir + 'train'

    netdict = {'iptfile' : iptfile,
               'cnstfile' : cstfile,
               'saefile': saefile,
               'nnfprefix': netdir+'train',
               'aevsize': aevsize,
               'num_nets': Nnets,
               }

    ## Train the ensemble ##
    aet = alt.alaniensembletrainer(netdir, netdict, 'train', h5stor, Nnets)
    aet.build_training_cache()
    aet.train_ensemble(GPU)

    ldtdir = root_dir  # local data directories
    if not os.path.exists(root_dir + datdir + str(i+1).zfill(2)):
        os.mkdir(root_dir + datdir + str(i+1).zfill(2))

    ## Run active learning sampling ##
    acs = alt.alconformationalsampler(ldtdir, datdir + str(i+1).zfill(2), optlfile, fpatoms, netdict)
    acs.run_sampling_nms(nmsparams, GPU)
    acs.run_sampling_md(mdsparams, GPU)

    ## Submit jobs, return and pack data
    ast.generateQMdata(hostname, username, swkdir, ldtdir, datdir + str(i+1).zfill(2), h5stor, mae)


