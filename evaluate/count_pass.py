import json
import pandas as pd
from collections import defaultdict

# Load the JSON file
file_path = "solutions.json"  # Adjust this path based on your local directory
with open(file_path, "r") as f:
    data = json.load(f)

# Initialize a dictionary to store the structured results
structured_results = defaultdict(lambda: defaultdict(lambda: {"total": 0, "pass": 0, "syntax_error": 0, "functional_error": 0}))

# Process the data to count various results per LLM and type
for llm, categories in data.items():
    for category, modules in categories.items():
        for module in modules:
            for solution in module.get("solutions", []):
                structured_results[category][llm]["total"] += 1

                pass_info = solution.get("pass", "")
                if pass_info == "true":
                    structured_results[category][llm]["pass"] += 1
                elif "Detected error while running simulation" in pass_info:
                    structured_results[category][llm]["syntax_error"] += 1

                # Functional error count
                structured_results[category][llm]["functional_error"] = (
                    structured_results[category][llm]["total"]
                    - structured_results[category][llm]["syntax_error"]
                    - structured_results[category][llm]["pass"]
                )

# Create a DataFrame from the structured results
df_restructured = pd.DataFrame.from_dict(
    {category: {llm: f"{counts['pass']} | {counts['functional_error']} | {counts['syntax_error']}" for llm, counts in llms.items()}
     for category, llms in structured_results.items()},
    orient="index"
)

# Save to a CSV file
csv_output_path = "solution_pass_analysis.csv"  # Adjust the path as needed
df_restructured.to_csv(csv_output_path)

print(f"CSV file saved at: {csv_output_path}")
# print(df_restructured)
