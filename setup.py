import os, glob, shutil
import argparse
import subprocess
from dotenv import load_dotenv
from generate_solutions import generate_solutions
from functional_correctness import run_functional_correctness
from resource_usage import run_resource_usage

def main():
    # load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Command-line interface for Verilog solution generation and evaluation.")
    
    parser.add_argument("-generate_solutions", nargs=4, metavar=("PROVIDER", "MODEL_NAME", "K", "API_KEY"), help="Generate Verilog solutions using the specified provider, model, number of iterations, and API key.")
    parser.add_argument("-functional_correctness", action="store_true", help="Run functional correctness evaluation.")
    parser.add_argument("-resource_usage", action="store_true", help="Run resource usage evaluation.")
    parser.add_argument("-remove_logs", action="store_true", help="Remove all logs when programs finishes.")
    
    args = parser.parse_args()
    
    if args.generate_solutions:
        provider, model_name, k, api_key = args.generate_solutions
        generate_solutions(provider, api_key, model_name, int(k))
        
        if args.functional_correctness:
            run_functional_correctness()
            subprocess.run(["python", "./evaluate/count_pass.py"])
            subprocess.run(["python", "./evaluate/plot_pass.py"])
        
            if args.resource_usage:
                run_resource_usage()
                subprocess.run(["python", "./evaluate/count_resource.py"])
    else:
        if args.functional_correctness:
            run_functional_correctness()
            subprocess.run(["python", "./evaluate/count_pass.py"])
            subprocess.run(["python", "./evaluate/plot_pass.py"])
            
            if args.resource_usage:
                run_resource_usage()
                subprocess.run(["python", "./evaluate/count_resource.py"])
        
        if args.resource_usage:
            run_resource_usage()
            subprocess.run(["python", "./evaluate/count_resource.py"])

    #Cleanup of temporary files
    if os.path.exists("resource_usage.rpt"):
        os.remove("resource_usage.rpt")
    if os.path.exists("temp.v"):
        os.remove("temp.v")
    if os.path.exists("testbench.v"):
        os.remove("testbench.v")

    if os.path.exists(".Xil"):
        shutil.rmtree(".Xil", ignore_errors=True)
    if os.path.exists("xsim.dir"):
        shutil.rmtree("xsim.dir", ignore_errors=True)

    if args.remove_logs:
        for log in glob.glob("*.log"):
            os.remove(log)
        for jou in glob.glob("*.jou"):
            os.remove(jou)
        for pb in glob.glob("*.pb"):
            os.remove(pb)

if __name__ == "__main__":
    main()
