# challenge.py
# For the "try to break my bot" LinkedIn post.
# Runs one commenter's question through both bots, prints a reply I can paste,
# and logs it so I can write the follow up post with real numbers.
#
# Run from the repo root:
#   python challenge.py "Priya" "my power bill doubled and nobody can tell me why"
#
# Then open results/challenge_log.csv and fill in the "broke_it" column myself
# (yes / no / partly) after reading the answer. I judge these by hand, not the AI grader.

import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "scripts"))
from query_legacy import ask_legacy  # old keyword matching bot
from router import respond           # new GenAI agent

LOG = Path(__file__).parent / "results" / "challenge_log.csv"
FIELDS = ["time", "commenter", "question", "old_answer", "new_route",
          "new_answer", "cited_pages", "broke_it", "notes"]


def main():
    if len(sys.argv) < 3:
        print('Usage: python challenge.py "Commenter Name" "their question"')
        return

    name, question = sys.argv[1], sys.argv[2]
    old = ask_legacy(question)
    new = respond(question)

    # Write the row. broke_it and notes stay empty until I review it.
    new_file = not LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "commenter": name,
            "question": question,
            "old_answer": old["answer"],
            "new_route": new["route"],
            "new_answer": new["answer"],
            "cited_pages": ";".join(new.get("cited_pages") or []),
            "broke_it": "",
            "notes": "",
        })

    # Print a reply draft. I still read it and edit before posting.
    print("\n----- reply draft -----\n")
    print(f'Ran it, {name.split()[0]}.\n')
    print(f'Old bot: "{old["answer"]}"\n')
    print(f'New bot: "{new["answer"]}"\n')
    print("Verdict: ")
    print("\n-----------------------\n")
    print(f"Route: {new['route']}  |  logged to {LOG.name}")


if __name__ == "__main__":
    main()
