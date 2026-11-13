import json
import os
import re
import subprocess

# File paths
SOLUTIONS_FILE = "solutions.json"
PROBLEMS_FILE = "problems.json"
TEMP_VERILOG_FILE = "temp.v"
TEMP_TESTBENCH_FILE = "testbench.v"
TCL_SCRIPT_FILE = "run_testbench.tcl"

# List of possible success_messages
success_messages = [
    "All tests passed",
    "Your Design Passed"
]

# Function to extract the top module name from the testbench
def extract_top_module_name(testbench_file):
    with open(testbench_file, 'r', encoding="utf-8") as file:
        for line in file:
            match = re.search(r'\s*module\s+(\w+)\s*;', line)
            if match:
                print(match.group(1))
                return match.group(1)  # Extract module name
    return None  # Return None if no module found

# Function that executes the actual simulation via xsim
def run_xsim(module_name, xvlog, xelab, xsim):

    # Compile DUT + Testbench
    compile_proc = subprocess.run(
        [xvlog, TEMP_VERILOG_FILE, TEMP_TESTBENCH_FILE],
        capture_output=True,
        text=True
    )

    output_log = compile_proc.stdout + "\n" + compile_proc.stderr

    if compile_proc.returncode != 0:
        return output_log

    # Elaborate
    elab_proc = subprocess.run(
        [xelab, module_name, "-s", "sim_snapshot"],
        capture_output=True,
        text=True
    )

    output_log += elab_proc.stdout + "\n" + elab_proc.stderr

    if elab_proc.returncode != 0:
        return output_log

    # Run simulation
    sim_proc = subprocess.run(
        [xsim, "sim_snapshot", "-runall"],
        capture_output=True,
        text=True
    )

    output_log += sim_proc.stdout + "\n" + sim_proc.stderr

    return output_log

def run_functional_correctness():
    # Load JSON files
    with open(SOLUTIONS_FILE, "r", encoding="utf-8") as file:
        solutions_data = json.load(file)

    with open(PROBLEMS_FILE, "r", encoding="utf-8") as file:
        problems_data = json.load(file)

    # Map module names to their testbenches
    module_testbenches = {}
    for category, problems in problems_data.items():
        for problem in problems:
            module_name = problem.get("module")
            testbench_code = problem.get("Testbench")
            if module_name and testbench_code:
                module_testbenches[module_name] = testbench_code

    # print(module_testbenches.keys())

    # Get Vivado path from environment variable
    vivado_path = os.environ.get("vivado")
    if not vivado_path:
        raise EnvironmentError("Vivado environment variable not set.")
    os_name = os.name
    if (os_name == "posix"): 
        xvlog = os.path.join(vivado_path, "xvlog")
        xelab = os.path.join(vivado_path, "xelab")
        xsim = os.path.join(vivado_path, "xsim")
        vivado_path = os.path.join(vivado_path, "vivado")
    elif (os_name == "nt"): 
        xvlog = os.path.join(vivado_path, "xvlog.bat")
        xelab = os.path.join(vivado_path, "xelab.bat")
        xsim = os.path.join(vivado_path, "xsim.bat")
        vivado_path = os.path.join(vivado_path, "vivado.bat")
    else:
        raise EnvironmentError("Could not determine os")    

    # Iterate over solutions and test them
    for model, categories in solutions_data.items():
        for category, modules in categories.items():
            for module_entry in modules:
                module_name = module_entry["module"]
                # print(module_name)
                # print(module_name in module_testbenches.keys())

                if module_name not in module_testbenches:
                    print(f"Skipping {module_name}: No testbench found.")
                    continue

                testbench_code = module_testbenches[module_name]
                solutions = module_entry["solutions"]

                # Write the testbench to a file
                with open(TEMP_TESTBENCH_FILE, "w", encoding="utf-8") as f:
                    f.write(testbench_code)

                # Extract the top module name
                top_module = extract_top_module_name(TEMP_TESTBENCH_FILE)
                if not top_module:
                    print(f"Error: Could not extract top module from {module_name}. Skipping...")
                    solution_entry["pass"] = "Error: Could not extract top module."
                    continue

                # Iterate over all solutions
                for solution_entry in solutions:
                    verilog_code = solution_entry["solution"]
                    if "`timescale" not in verilog_code:
                        verilog_code = "`timescale 1ns/1ps\n" + verilog_code

                    # Write the Verilog design to a file
                    with open(TEMP_VERILOG_FILE, "w", encoding="utf-8") as f:
                        f.write(verilog_code)

                    print(f"Testing module: {module_name} (Top Module: {top_module})")
                    print(f"Running XSIM simulation for {module_name}...")

                    # Run simulation and extract output
                    output_log = run_xsim(top_module, xvlog, xelab, xsim)
                    print(output_log)
                    test_passed = any(msg in output_log for msg in success_messages)

                    # Determine pass/fail status
                    if test_passed:
                        solution_entry["pass"] = "true"
                    else:
                        # Extract relevant error messages
                        error_lines = "\n".join(line for line in output_log.split("\n") if "error" in line.lower() or "fail" in line.lower())
                        solution_entry["pass"] = error_lines if error_lines else "Test failed somehow"

                    print(f"Test result for {module_name}: {'PASS' if test_passed else 'FAIL'}")

                    # Save results after testing each module
                    with open(SOLUTIONS_FILE, "w", encoding="utf-8") as file:
                        json.dump(solutions_data, file, indent=4)

    print("All tests completed.")
