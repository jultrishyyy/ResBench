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

def write_tcl():
        # Generate the TCL script for Vivado
    tcl_commands = f"""
    create_project temp_project ./temp_project -force -part xc7z020clg400-1
    set_property source_mgmt_mode All [current_project]
    add_files {TEMP_VERILOG_FILE}
    add_files -fileset sim_1 {TEMP_TESTBENCH_FILE}
    set_property top {top_module} [get_filesets sim_1]
    launch_simulation -simset sim_1 -mode behavioral
    run 3000ns
    close_sim
    exit
    """
    # Write the Tcl script
    with open(TCL_SCRIPT_FILE, "w", encoding="utf-8") as file:
        file.write(tcl_commands)

# Function to extract the top module name from the testbench
def extract_top_module_name(testbench_file):
    with open(testbench_file, 'r', encoding="utf-8") as file:
        for line in file:
            match = re.search(r'\s*module\s+(\w+)\s*;', line)
            if match:
                print(match.group(1))
                return match.group(1)  # Extract module name
    return None  # Return None if no module found



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
    vivado_path = os.path.join(vivado_path, "vivado.bat")

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

                # Iterate over all solutions
                for solution_entry in solutions:
                    verilog_code = solution_entry["solution"]

                    # Write the Verilog design to a file
                    with open(TEMP_VERILOG_FILE, "w", encoding="utf-8") as f:
                        f.write(verilog_code)

                    # Write the testbench to a file
                    with open(TEMP_TESTBENCH_FILE, "w", encoding="utf-8") as f:
                        f.write(testbench_code)

                    # Extract the top module name
                    top_module = extract_top_module_name(TEMP_TESTBENCH_FILE)
                    if not top_module:
                        print(f"Error: Could not extract top module from {module_name}. Skipping...")
                        solution_entry["pass"] = "Error: Could not extract top module."
                        continue

                    print(f"Testing module: {module_name} (Top Module: {top_module})")

                    write_tcl()

                    # Run Vivado in batch mode
                    print(f"Running Vivado simulation for {module_name}...")
                    process = subprocess.run([vivado_path, "-mode", "batch", "-source", TCL_SCRIPT_FILE], capture_output=True, text=True)

                    # Capture output logs
                    output_log = process.stdout + "\n" + process.stderr
                    print(output_log)
                    test_passed = "All tests passed" in output_log

                    # Determine pass/fail status
                    if test_passed:
                        solution_entry["pass"] = "true"
                    else:
                        # Extract relevant error messages
                        error_lines = "\n".join(line for line in output_log.split("\n") if "error" or "fail" in line.lower())
                        solution_entry["pass"] = error_lines if error_lines else "Test failed somehow"

                    print(f"Test result for {module_name}: {'PASS' if test_passed else 'FAIL'}")

                    # Save results after testing each module
                    with open(SOLUTIONS_FILE, "w", encoding="utf-8") as file:
                        json.dump(solutions_data, file, indent=4)

    print("All tests completed.")
