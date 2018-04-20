import tempfile, os, shutil, shlex, subprocess, ntpath, timeout_decorator
from utils import constants, multicall
from progressbar import ProgressBar, Percentage, Bar, RotatingMarker, ETA, FileTransferSpeed
import logging

@timeout_decorator.timeout(20) # change this value if you want to wait more or less time to run this method
def fuzz_file(num_iterations, file_path, mcalls, validator=None, libs=None):
    '''
        Call an external fuzzer (hardcoded with radamsa, for now) to fuzz/mutate 
        the input file (file_path) for a number of times (num_iterations). Each 
        time it makes a multicall on different engines. 
    '''
    
    widgets = ['fuzzing ' + file_path + ' ', Percentage(), ' ', Bar(marker=RotatingMarker()), ' ', ETA(), ' ']
    bar = ProgressBar(widgets=widgets, maxval=num_iterations).start()
    logging.debug('fuzzing %s', file_path)

    #pylint: disable=W0612
    num_successful_iterations = 0
    num_unsuccessful_iterations = 0
    while num_successful_iterations < num_iterations:
        
        logging.debug('num_successful_iterations %s', str(num_successful_iterations))
        logging.debug('num_unsuccessful_iterations %s', str(num_unsuccessful_iterations))
        
        if num_unsuccessful_iterations > 100:
            print ('   hit max number of unsuccessful iterations')
            break # quit this file

        # fuzz the file with radamsa
        fuzzed_file_path = os.path.join(tempfile.gettempdir(), 'temp_filefuzzed')
        cmd = "radamsa --output {} {}".format(fuzzed_file_path, file_path)
        args = shlex.split(cmd)
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.communicate()
        except FileNotFoundError as error:
            if 'radamsa' in str(error):
                raise Exception('Please check if radamsa is installed on your environment (see README.md file).')
        except Exception as error:
            raise Exception('Error:', error)

        # TODO: consider optimizing. This is taking a LOT of time, both parsing and validating. - Marcelo
        '''
            Check if file is valid and should be considered
        '''
        if validator is not None:
            validation_error = validator(fuzzed_file_path)
            if validation_error:
                res = multicall.Results(fuzzed_file_path, validation_error)
                mcalls.notify(res)
                num_unsuccessful_iterations += 1
                continue # skip this file

        # check discrepancy
        try:
            res = multicall.callAll(fuzzed_file_path, libs=libs)
            path_list = file_path.split('/')
            index = path_list.index('seeds') + 1
            name = 'fuzzed_' + '_'.join(path_list[index:])
            res.path_name = os.path.join(constants.logs_dir, name)
            if mcalls.notify(res): # true if it is interesting and distinct. in this case, save the file
                ## get first name of file...
                shutil.copy(fuzzed_file_path, res.path_name)
        except UnicodeDecodeError as exc:
            # TODO: It is silly but we can't handle properly non-unicode outputs 
            # just because the .decode('utf-8') to convert bytes into strings 
            # raises this exception when the non-unicode char is mapped.
            num_unsuccessful_iterations += 1
            continue

        num_successful_iterations += 1
        bar.update(num_successful_iterations) 
        
    bar.finish()
    logging.debug('done fuzzing %s', file_path)

if __name__ == "__main__":
    dir_path = os.path.join(constants.seeds_dir, 'WebKit.JSTests.es6')
    # fuzz_dir(dir_path)