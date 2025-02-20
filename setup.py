import argparse
import subprocess
from generate_solutions import generate_solutions
from functional_correctness import run_functional_correctness, run_resource_usage

def main():
    parser = argparse.ArgumentParser(description="Command-line interface for Verilog solution generation and evaluation.")
    
    parser.add_argument("-generate_solutions", nargs=3, metavar=("MODEL_NAME", "K", "API_KEY"), help="Generate Verilog solutions using the specified model, number of iterations, and API key.")
    parser.add_argument("-functional_correctness", action="store_true", help="Run functional correctness evaluation.")
    parser.add_argument("-resource_usage", action="store_true", help="Run resource usage evaluation.")
    
    args = parser.parse_args()
    
    if args.generate_solutions:
        model_name, k, api_key = args.generate_solutions
        generate_solutions(api_key, model_name, int(k))
        
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
    
if __name__ == "__main__":
    main()
