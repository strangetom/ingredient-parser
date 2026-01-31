#!/usr/bin/env python3

import argparse
import sqlite3
import time

from ingredient_parser import parse_ingredient

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingredient Parser benchmark")
    parser.add_argument(
        "-n", type=int, help="Number of sentences to use from each source.", default=100
    )
    parser.add_argument(
        "--iterations", "-i", type=int, help="Number of iterations to run.", default=500
    )
    parser.add_argument(
        "--foundationfoods", "-ff", action="store_true", help="Enable foundation foods."
    )
    args = parser.parse_args()

    with sqlite3.connect(
        "train/data/training.sqlite3", detect_types=sqlite3.PARSE_DECLTYPES
    ) as conn:
        c = conn.cursor()
        # Select `n` sentences from each source
        c.execute(
            """
            SELECT sentence FROM 
            (
                SELECT *, row_number() OVER (
                    PARTITION BY source ORDER BY rowid
                ) 
                AS rn FROM en
            )
            WHERE rn <= ?
            ORDER BY source, rn
            """,
            (args.n,),
        )
        sentences = [sent for (sent,) in c.fetchall()]
    conn.close()

    start = time.time()
    for i in range(args.iterations):
        for sent in sentences:
            parse_ingredient(
                sent, expect_name_in_output=True, foundation_foods=args.foundationfoods
            )

    duration = time.time() - start
    total_sentences = args.iterations * len(sentences)
    print(f"Elapsed time: {duration:.2f} s.")
    print(f"{total_sentences} total iterations.")
    print(f"{1e6 * duration / total_sentences:.2f} us/sentence.")
    print(f"{total_sentences / duration:.2f} sentences/second.")
