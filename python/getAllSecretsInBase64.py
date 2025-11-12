import os
import subprocess
from subprocess import Popen, PIPE
import sys
import apt

package = 'jq' # insert your package name here
cache = apt.Cache()
package_installed = False

namespace= sys.argv[1]

subprocess = subprocess.Popen("kubectl config current-context", shell=True, stdout=subprocess.PIPE)
context = subprocess.stdout.read()
filename = 'SecretsInBase64_' + context.strip().decode("utf-8") + "_" + namespace

if package in cache:

    package_installed = cache[package].is_installed

if (package_installed):
    print("YES jq is installed")
    print("Results will be in file " + filename)
    print("...any secrets in base64.")
else:
    print("First install jq by doing >> sudo apt install jq <<")
    exit()

file = open(filename, 'w+')

command = "kubectl get secrets -n " + namespace + " | awk -F \" \" '{print $1}' | grep -v NAME"
pipe = Popen(command, shell=True, stdout=PIPE)

for line in pipe.stdout:
    command2 = "kubectl get secrets "  + str(line.strip().decode("utf-8")) + " -n " + namespace + " -o json | jq .data | sed 's/\"//g' | sed 's/,//g' | sed 's/{//g' | sed 's/}//g' | sed '/^[[:space:]]*$/d'"
    pipe2 = Popen(command2, shell=True, stdout=PIPE)
    for line2 in pipe2.stdout:
        #print(line2.strip().decode("utf-8"))
        file.write(line2.strip().decode("utf-8")+'\n')