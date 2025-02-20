import json
import subprocess
import os
import re

def extract_module_name(verilog_code):
    """
    Extract the module name from the Verilog code.
    Assumes the module declaration is of the form:
        module <module_name> (
    Returns the module name as a string, or None if not found.
    """
    match = re.search(r'\bmodule\s+(\w+)', verilog_code)
    if match:
        return match.group(1)
    return None

def parse_optimized(lines):
    """
    Extract resource usage numbers from the main (optimized) report sections.
    Returns a dictionary with keys: LUT, FF, DSP, BRAM, IO.
    """
    optimized = {"LUT": None, "FF": None, "DSP": None, "BRAM": None, "IO": None}
    for line in lines:
        m = re.search(r'\|\s*Slice LUTs\*?\s*\|\s*(\d+)', line)
        if m:
            optimized["LUT"] = int(m.group(1))
        m = re.search(r'\|\s*Slice Registers\s*\|\s*(\d+)', line)
        if m:
            optimized["FF"] = int(m.group(1))
        m = re.search(r'\|\s*DSPs\s*\|\s*(\d+)', line)
        if m:
            optimized["DSP"] = int(m.group(1))
        m = re.search(r'\|\s*Block RAM Tile\s*\|\s*(\d+)', line)
        if m:
            optimized["BRAM"] = int(m.group(1))
        m = re.search(r'\|\s*Bonded IOB\s*\|\s*(\d+)', line)
        if m:
            optimized["IO"] = int(m.group(1))
    return optimized

def extract_primitives_section(lines):
    """
    Extracts all lines between the "7. Primitives" header and the "8. Black Boxes" header.
    """
    start_marker = "7. Primitives"
    end_marker   = "8. Black Boxes"
    start_idx = None
    end_idx = None

    for idx, line in enumerate(lines):
        if start_idx is None and start_marker in line and (idx + 1 < len(lines) and "------" in lines[idx + 1]):
            start_idx = idx
        elif start_idx is not None and end_marker in line and (idx + 1 < len(lines) and "------" in lines[idx + 1]):
            end_idx = idx
            break

    if start_idx is None or end_idx is None:
        return []
    return lines[start_idx:end_idx]

def parse_primitives_section(lines):
    """
    Parses the primitives section lines to accumulate resource usage.
    Returns a dictionary with keys: LUT, FF, DSP, BRAM, IO.
    In this example:
      - For LUT: sums up any primitive whose name starts with "LUT" (e.g., LUT2, LUT3, ...)
      - For IO: sums the usage of IBUF and OBUF.
    """
    resources = {"LUT": 0, "FF": 0, "DSP": 0, "BRAM": 0, "IO": 0}
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line.startswith("|"):
            continue
        parts = stripped_line.split("|")
        if len(parts) < 4:
            continue
        ref_name = parts[1].strip()
        used_str = parts[2].strip()
        try:
            used = int(used_str)
        except ValueError:
            continue
        if ref_name.startswith("LUT"):
            resources["LUT"] += used
        if ref_name in ("IBUF", "OBUF"):
            resources["IO"] += used
        # (Add additional processing for FF, DSP, BRAM if necessary.)
    return resources

def run_synthesis(solution_code):
    """
    Writes the given Verilog solution to a temporary file,
    creates a Tcl script for Vivado to run synthesis and generate a utilization report,
    runs Vivado in batch mode, and parses the resource usage report.
    Returns a dictionary with keys "optimized" and "primitives" containing resource usage.
    """
    # Write the Verilog code to a temporary file.
    verilog_file = "temp.v"
    with open(verilog_file, "w") as f:
        f.write(solution_code)

    # Extract the module name from the solution code.
    top_module = extract_module_name(solution_code)
    print(top_module)
    if top_module is None:
        print("Could not extract module name; using 'temp_top' as a default.")
        top_module = "temp_top"

    vivado_project = "temp_project"
    tcl_script = "synthesis_script.tcl"

    # Get the Vivado installation path from the environment variable.
    vivado_path_env = os.environ.get("vivado")
    if vivado_path_env is None:
        print("Error: 'vivado' environment variable is not set.")
        return None
    vivado_path = os.path.join(vivado_path_env, "vivado.bat")

    # Create the Vivado Tcl script.
    tcl_commands = f"""
    create_project {vivado_project} -force -part xc7z020clg400-1
    add_files {verilog_file}
    set_property top {top_module} [current_fileset]

    # Run synthesis only (no simulation)
    synth_design -top {top_module}

    # Generate resource utilization report
    report_utilization -file resource_usage.rpt

    quit
    """
    with open(tcl_script, "w") as file:
        file.write(tcl_commands)

    # Run Vivado in batch mode using the generated Tcl script.
    try:
        result = subprocess.run(
            [vivado_path, "-mode", "batch", "-source", tcl_script],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        print("Synthesis failed:", e)
        return None
    print(result.stdout)
    # Check for the success message in the output.
    if "Finished Writing Synthesis Report" in result.stdout:
        # Read the resource utilization report.
        with open("resource_usage.rpt", "r") as f:
            report_lines = f.readlines()
        optimized_resources = parse_optimized(report_lines)
        primitives_section = extract_primitives_section(report_lines)
        primitives_resources = (parse_primitives_section(primitives_section)
                                  if primitives_section else {})
        return {"optimized": optimized_resources, "primitives": primitives_resources}
    else:
        print("Synthesis did not complete successfully.")
        return None

def run_resource_usage():
    # Load the original JSON.
    input_json_file = "solutions.json"  # Update this file name if needed.
    with open(input_json_file, "r") as f:
        data = json.load(f)

    # Traverse all top-level keys (e.g., "4o") and all subcategories.
    for top_key, top_value in data.items():
        # print(top_value.keys())
        # exit()
        # top_value should be a dict with categories (e.g., "Combinational Logic", "Finite State Machines", etc.)
        for category, module_list in top_value.items():
            # if category == "Combinational Logic":
            #     continue
            for module in module_list:
                for sol in module["solutions"]:
                    if sol.get("pass", "").strip().lower() == "true":
                        solution_code = sol["solution"]
                        print(f"Running synthesis for module '{module['module']}' in category '{category}'")
                        resource_usage = run_synthesis(solution_code)
                        if resource_usage:
                            sol["resource usage"] = resource_usage
                        else:
                            sol["resource usage"] = {"optimized": {}, "primitives": {}}
                    else:
                        sol["resource usage"] = {"optimized": {}, "primitives": {}}

                    # Write the updated JSON (with resource usage added) to a new file.
                    output_json_file = "solutions.json"
                    with open(output_json_file, "w") as f:
                        json.dump(data, f, indent=4)
                    print(f"Updated JSON written to {output_json_file}")


