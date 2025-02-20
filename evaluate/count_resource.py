import json
import pandas as pd
from collections import defaultdict

# Load the JSON file
file_path = "solutions.json"
with open(file_path, "r") as f:
    data = json.load(f)

# Initialize a dictionary to store the minimal LUT usage for each module and LLM
lut_results = defaultdict(lambda: defaultdict(lambda: float("inf")))

# Process the data to extract the minimum LUT usage per module per LLM
for llm, categories in data.items():
    for category, modules in categories.items():
        for module_data in modules:
            module_name = module_data["module"].replace("_", " ")  # Replace underscores with spaces
            for solution in module_data.get("solutions", []):
                if "resource usage" in solution and "optimized" in solution["resource usage"]:
                    lut_count = solution["resource usage"]["optimized"].get("LUT", float("inf"))
                    # Store the minimum LUT usage
                    lut_results[module_name][llm] = min(lut_results[module_name][llm], lut_count)

# Convert the dictionary into a DataFrame
df_lut = pd.DataFrame.from_dict(lut_results, orient="index")

# Save to a CSV file
csv_output_path = "solution_resource_analysis.csv"
df_lut.to_csv(csv_output_path)

# Print the CSV file path
print(f"CSV file saved at: {csv_output_path}")
