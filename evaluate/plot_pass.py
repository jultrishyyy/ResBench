import json
import matplotlib.pyplot as plt
import re
import seaborn as sns
import pandas as pd

# --- Utility Functions ---

def compute_module_pass(solution_list, k):
    """
    Check the first k solutions for a module.
    Return 1 if at least one of them has a "pass" value (after stripping and lowercasing) equal to "true",
    otherwise return 0.
    """
    for sol in solution_list[:k]:
        if sol.get("pass", "").strip().lower() == "true":
            return 1
    return 0

def compute_pass_at_k_for_modules(modules, k):
    """
    Given a list of modules (each module is expected to have a "solutions" list),
    compute the fraction of modules that pass@k.
    """
    total = len(modules)
    if total == 0:
        return 0
    passed = sum(compute_module_pass(mod["solutions"], k) for mod in modules)
    return passed / total

def compute_overall_pass_at_k(llm_data, ks):
    """
    Given one LLM's data (a dict mapping category names to lists of modules),
    compute the overall pass@k (over all modules in all categories).
    Returns a dictionary mapping each k to the pass@k value.
    """
    all_modules = []
    for cat, modules in llm_data.items():
        all_modules.extend(modules)
    overall = {}
    for k in ks:
        overall[k] = compute_pass_at_k_for_modules(all_modules, k)
    return overall

def compute_category_pass_at_k(llm_data, ks):
    """
    For each category (type) in one LLM, compute pass@k.
    Returns a dictionary mapping category names to a dictionary of k -> pass@k.
    """
    cat_results = {}
    for cat, modules in llm_data.items():
        k_dict = {}
        for k in ks:
            k_dict[k] = compute_pass_at_k_for_modules(modules, k)
        cat_results[cat] = k_dict
    return cat_results

# --- Main processing and plotting ---

# Choose the k values you want to evaluate pass@k for:
ks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

# Load the JSON file.
input_json_file = "solutions.json"  # adjust filename if necessary
with open(input_json_file, "r") as f:
    data = json.load(f)

# We'll store our computed pass@k results per LLM in a dictionary.
llm_results = {}
for llm, llm_data in data.items():
    overall = compute_overall_pass_at_k(llm_data, ks)
    categories = compute_category_pass_at_k(llm_data, ks)
    llm_results[llm] = {
        "overall": overall,
        "categories": categories
    }

# --- Plot Overall Pass@k for each LLM ---
plt.figure(figsize=(10, 6))
for llm, res in llm_results.items():
    plt.plot(ks, [res["overall"][k] for k in ks], marker='o', label=llm)

# plt.xticks(ks)  # Ensure all values from 1 to 15 are shown
# plt.xlabel("k", fontsize=14)
# plt.ylabel("Overall Pass@k", fontsize=14)
# plt.title("Overall Pass@k across k for each LLM", fontsize=16)  # Larger title
# plt.legend(loc="upper left", bbox_to_anchor=(1, 1))  # Legend outside the plot
# plt.grid(True)
# plt.tight_layout()
# plt.savefig("./figures/overall_pass_at_k.png")
# plt.show()


# --- Plot Per-Category Pass@k for all LLMs, one figure per k ---
# First, determine the union of all categories across LLMs.
# Prepare data for heatmap
category_pass_k = {}
for llm, res in llm_results.items():
    for cat, kdict in res["categories"].items():
        if cat not in category_pass_k:
            category_pass_k[cat] = {}
        category_pass_k[cat][llm] = kdict[15]  # Using Pass@15

# Convert to DataFrame
df_heatmap = pd.DataFrame.from_dict(category_pass_k).T


for k in ks:
    # Convert to DataFrame
    df_heatmap = pd.DataFrame.from_dict(category_pass_k).T

    # Plot heatmap
    plt.figure(figsize=(10, 6))
    sns.heatmap(df_heatmap, annot=True, cmap="Blues", linewidths=0.5, fmt=".2f")

    plt.title("Pass@15 Heatmap for Each LLM Across Categories", fontsize=16, fontweight="bold")
    plt.xlabel("LLM", fontsize=14, fontweight="bold")
    plt.ylabel("Category", fontsize=14, fontweight="bold")

    plt.xticks(rotation=45, ha="right", fontsize=12)
    plt.yticks(fontsize=12)

    plt.tight_layout()
    heatmap_path = f"./figures/per_category_pass_k{k}_heatmap.png"
    plt.savefig(heatmap_path)

# --- (Optional) Print the computed results ---
print("Overall Pass@k per LLM:")
for llm, res in llm_results.items():
    print(f"{llm}: {res['overall']}")

print("\nPer-Category Pass@k per LLM:")
for llm, res in llm_results.items():
    print(f"{llm}:")
    for cat, kdict in res["categories"].items():
        print(f"  {cat}: {kdict}")
