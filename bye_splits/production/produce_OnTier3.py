import os
import glob
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--inputFolder", dest="inputFolder",   type=str, default=None, help="Input folder on the grid")
parser.add_option("--outputFolder",dest="outputFolder",  type=str, default=None, help="Ouutput folder where to store")
parser.add_option("--n_files",     dest="n_files",       type=int, default=100,  help="Number of ntuples to process")
parser.add_option("--particles",   dest="particles",     type=str, default='photons', help="Number of ntuples to process")
parser.add_option("--queue",       dest="queue",         type=str, default='short', help="long or short queue")
parser.add_option("--no_exec",     dest="no_exec",       action='store_true', default=False, help="stop execution")

(options, args) = parser.parse_args()

infile_base  = os.getcwd()+'/../'
user = infile_base.split('/')[5]
outfile_base = "/data_CMS/cms/"+user+"/ntupleProduction/"
infile_base  = "root://eos.grif.fr//eos/grif/cms/llr/store/user/"+user+"/"

###########

folder = outfile_base+options.outputFolder+'/skimmed_ntuples'
queue = options.queue
os.system('mkdir -p ' + folder)

print("Input has" , options.n_files, "files")
for idx in range(options.n_files):
    outRootName = folder + '/Ntuple_' + str(idx) + '.root'
    outJobName  = folder + '/job_' + str(idx) + '.sh'
    outLogName  = folder + "/log_" + str(idx) + ".txt"

    root_file = infile_base+options.inputFolder+"/NTuple_"+str(idx)+".root"
    cmsRun = "python produce.py --nevents=-1 --particles "+options.particles+" --inputFile="+root_file+" --outputFile="+outRootName+" >& "+outLogName

    skimjob = open (outJobName, 'w')
    skimjob.write ('#!/bin/bash\n')
    skimjob.write ('export X509_USER_PROXY=~/.t3/proxy.cert\n')
    skimjob.write ('source /cvmfs/cms.cern.ch/cmsset_default.sh\n')
    skimjob.write ('cd %s\n' % os.getcwd())
    skimjob.write ('export SCRAM_ARCH=slc6_amd64_gcc472\n')
    skimjob.write ('eval `scram r -sh`\n')
    skimjob.write ('cd %s\n'%os.getcwd())
    skimjob.write (cmsRun+'\n')
    skimjob.close ()

    os.system ('chmod u+rwx ' + outJobName)
    command = ('/home/llr/cms/'+user+'/t3submit -'+queue+' \'' + outJobName +"\'")
    print(command)
    if not options.no_exec: os.system (command)
